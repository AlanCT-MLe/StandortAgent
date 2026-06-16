import json
import os
from google import genai
from google.genai import types # Added to support the new SDK config structure
from dotenv import load_dotenv

load_dotenv()

class BaseAgent:
    """
    Base Agent class
    Initialization
    """
    def __init__(self, profile: dict):
        self.profile = profile

    def evaluate(self, row) -> tuple[float, str]:
        raise NotImplementedError("Agents has to implement the evaluate method.")
    
class DemographicsAgent(BaseAgent):
    """
    Gemini 2.5 flash as a semantic router for the demographic weights
    """
    def __init__(self, profile: dict):
        super().__init__(profile)
        self.zielgruppe = self.profile.get("zielgruppe", "Alle Altersgruppen") 
        self.age_weights = self._get_llm_age_weights(self.zielgruppe)

    def _get_llm_age_weights(self, zielgruppe_text: str) -> dict:
        fix_weights = {"18_34": 0.33, "35_54": 0.33, "55_plus": 0.34} 
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            print("[Warning] GEMINI_API_KEY missing. Using fallback demographics.")
            return fix_weights
        
        try:
            # NEW SDK: Instantiate the client
            client = genai.Client(api_key=api_key)

            prompt = f"""
            Map the target audience "{zielgruppe_text}" to the following three age brackets: 
            '18_34', '35_54', '55_plus'.
            Assign a float weight between 0.0 and 1.0 to each based on relevance.
            The three weights MUST sum up to exactly 1.0.
            Return ONLY a valid JSON object. Example: {{"18_34": 0.2, "35_54": 0.5, "55_plus": 0.3}}
            """

            # NEW SDK: Call generate_content directly with config types
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    response_mime_type="application/json"
                )
            )

            weights = json.loads(response.text)

            if all(k in weights for k in ["18_34", "35_54", "55_plus"]):
                return weights
            raise ValueError("Malformed JSON keys.")
            
        except Exception as e:
            print(f"[Error] Gemini Demographic routing failed: {e}. Using fallback.")
            return fix_weights
        
    def evaluate(self, row) -> tuple[float, str]:
        p_18_34 = float(row.get("altersverteilung_18_34", 0))
        p_35_54 = float(row.get("altersverteilung_35_54", 0))
        p_55_plus = float(row.get("altersverteilung_55_plus", 0))
        
        score = (
            (self.age_weights["18_34"] * p_18_34) +
            (self.age_weights["35_54"] * p_35_54) +
            (self.age_weights["55_plus"] * p_55_plus)
            )
        percentage = round(score * 100, 1)
        rationale = f"Demographic Match: {percentage}% alignment for target '{self.zielgruppe}'."
        return score, rationale
    

class POIAgent(BaseAgent):
    """
    Logic evaluation for commercial foot traffic.
    """
    def evaluate(self, row) -> tuple[float, str]:
        rscore = float(row["poi_dichte"])

        if rscore >= 7.0:
            vibrancy = "highly active commercial ecosystem"
        elif rscore >= 4.0:
            vibrancy = "moderate mixed-use commercial presence"
        else:
            vibrancy = "low density, quiet local surroundings"

        rationale = f"Vibrancy Index: Ambient POI score is {rscore}/10 ({vibrancy})."
        return rscore, rationale
    
class RentAgent(BaseAgent):
    """
    Mathematical evaluation of rent and expected rent
    """
    def evaluate(self, row) -> tuple[float, str]:
        rent_index = float(row["mietindex_eur_m2"])
        required_area = float(self.profile.get("flaeche_m2", 0))
        max_budget = float(self.profile.get("budget_miete_eur", 0))
        
        expected_rent = rent_index * required_area
        rscore = max_budget - expected_rent
        
        if rscore >= 0:
            rationale = f"Rent under the budget: Expected lease €{expected_rent:,.2f}/mo (Savings: €{rscore:,.2f})."
        else:
            rationale = f"Rent over the budget: Expected lease €{expected_rent:,.2f}/mo (Exceeds budget by €{abs(rscore):,.2f})."
            
        return rscore, rationale
    
class TransportAgent(BaseAgent):
    """Infrastructural logistics, only logic the more the better"""
    def evaluate(self, row) -> tuple[float, str]:
        rscore = float(row["oev_score"])
        # FIXED: Changed 'raw_score' to 'rscore' to prevent NameError
        rationale = f"Accessibility: Transportations, logistics and roads available score: {rscore}/10."
        return rscore, rationale