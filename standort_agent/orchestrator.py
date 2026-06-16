import os
import pandas as pd
from google import genai
from google.genai import types # Added to support the new SDK config structure
from dotenv import load_dotenv
from jinja2 import Template
from standort_agent.agents import DemographicsAgent, POIAgent, RentAgent, TransportAgent

load_dotenv()

class Orchestrator:
    def __init__(self, df: pd.DataFrame, profile: dict):
        self.df = df
        self.profile = profile

        # Agents
        self.agents = {
            "Demographics": DemographicsAgent(profile),
            "POI": POIAgent(profile),
            "Rent": RentAgent(profile),
            "Transport": TransportAgent(profile)
        }

        # Priority Weights
        self.weights = {
            "Demographics": 0.25,
            "POI": 0.25,
            "Rent": 0.25,  
            "Transport": 0.25
        }

    def run_and_report(self) -> str:
        if self.df.empty:
            raise ValueError("DataFrame is empty.")
        
        # Get the scrores and reason of each Agent
        records = []
        for _, row in self.df.iterrows():
            mp_record = {
                "gemeinde": row["gemeinde"],
                "bundesland": row["bundesland"],
                "rscores": {},
                "reasons":{}
            }

            for name, agent in self.agents.items():
                score, reason = agent.evaluate(row)
                mp_record["rscores"][name] = score
                mp_record["reasons"][name] = reason
            records.append(mp_record)
        
        # Normalization of scores with Global Min-Max
        for name in self.agents.keys():
            scores = [record["rscores"][name] for record in records]
            min_value, max_value = min(scores), max(scores)
            delta_value = max_value - min_value

            for record in records:
                value = record["rscores"][name]
                # Avoid 0 division
                normalize_score = 1.0 if delta_value == 0 else (value - min_value)/delta_value
                record.setdefault("normalized_scores", {})[name] = normalize_score
        
        # Final Score: SUM 
        for record in records:
            w_sum = sum(
                record["normalized_scores"][name] * self.weights[name]
                for name in self.agents.keys()
            )
            record["final_score"] = round(w_sum * 100,2)

        # Rank the scores and locations
        top_records = sorted(records, key= lambda x: x["final_score"], reverse=True)
        top_places = top_records[:5]

        return self._render_jinja_report(top_places)
    
    def _generate_executive_summary(self, top_location: dict) -> str:
        """Gemini outputs pure text"""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Summary unavailable: GEMINI_API_KEY environment variable missing."

        industry = self.profile.get('branche', 'Commercial Retail')
        target = self.profile.get('zielgruppe', 'General Public')
        
        prompt = f"""
        You are a seasoned commercial real estate consultant. 
        Your client is opening a business in the '{industry}' sector, targeting '{target}'.
        Our algorithm has identified their absolute best location as {top_location['gemeinde']} in {top_location['bundesland']} with a structural suitability score of {top_location['final_score']}%.
        
        Write a concise, professional 2-paragraph executive summary explaining why this location presents a strong strategic opportunity based on their profile. Do not output any markdown headers, bullet points, or HTML tags. Return raw plain text paragraphs only.
        """

        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.4)
            )
            return response.text.strip()
        except Exception as e:
            print(f"[Error] Gemini Summary failure: {e}")
            return "Automated consulting narrative generation encountered a runtime exception."

    def _render_jinja_report(self, top_locations: list) -> str:
        """
        Renders  HTML layout template.
        """
        llm_summary = self._generate_executive_summary(top_locations[0])

       
        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Location Suitability Analysis Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; color: #2d3748; line-height: 1.6; max-width: 900px; }
        h1 { color: #1a365d; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; font-size: 2.2em; }
        h2 { color: #2c5282; margin-top: 40px; border-bottom: 1px solid #edf2f7; padding-bottom: 8px; }
        h3 { margin: 0 0 10px 0; color: #2b6cb0; }
        .summary-box { background-color: #f0fff4; padding: 20px; border-left: 4px solid #38a169; margin: 25px 0; border-radius: 0 6px 6px 0; white-space: pre-line; }
        .summary-box strong { color: #22543d; display: block; margin-bottom: 8px; font-size: 1.1em; }
        .location-card { border: 1px solid #e2e8f0; padding: 20px; margin-bottom: 20px; border-radius: 8px; background-color: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        .score-badge { font-size: 1.1em; font-weight: bold; color: #2b6cb0; background-color: #ebf8ff; padding: 4px 12px; border-radius: 20px; float: right; border: 1px solid #bee3f8; }
        .agent-note { margin-left: 15px; margin-bottom: 6px; font-size: 0.95em; color: #4a5568; }
        .bullet { font-weight: bold; color: #718096; margin-right: 5px; }
    </style>
</head>
<body>
    <h1>Location Suitability Analysis</h1>
    <p>Target Industry Profile: <strong>{{ profile.branche }}</strong></p>
    
    <div class="summary-box">
        <strong>Strategic Executive Summary</strong>
        {{ summary_text }}
    </div>
    
    <h2>Top Recommended Municipalities</h2>
    {% for loc in locations %}
    <div class="location-card">
        <span class="score-badge">Suitability Index: {{ loc.final_score }}%</span>
        <h3>Rank #{{ loop.index }}: {{ loc.gemeinde }} ({{ loc.bundesland }})</h3>
        <div class="agent-note"><span class="bullet">&bull;</span> {{ loc.reasons.Demographics }}</div>
        <div class="agent-note"><span class="bullet">&bull;</span> {{ loc.reasons.POI }}</div>
        <div class="agent-note"><span class="bullet">&bull;</span> {{ loc.reasons.Rent }}</div>
        <div class="agent-note"><span class="bullet">&bull;</span> {{ loc.reasons.Transport }}</div>
    </div>
    {% endfor %}
</body>
</html>"""

        # Compile and evaluate the parameters via Jinja
        template = Template(html_template)
        rendered_html = template.render(
            profile=self.profile,
            summary_text=llm_summary,
            locations=top_locations
        )

        output_file = "location_suitability_report.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rendered_html)
            
        return output_file
    

        


