## Decision Log

##### Architectural Decisions

1. Define that the agent definition can be as simple as a function. Each agent/function was implemented as a decoupled multi-agent architecture. Running all the math with Python, most of it.

2. I implemented a global Min-Max normalization step inside the Orchestrator. The objective was to standaedize all the agents outputs to a uniform [0,1].

3. I decide to only use an LLM or an Gen AI approach only in two specific cases. **One** to interpret the context of the **zielgroup** and match it to the **altersverteilung** age bracket. This is because the user can be to ambiguous. **Second** to generate a summay with the given rationale and score computed. So it can report back in a natural way.

##### Key AI Prompts

1. Prompt 1 (The Logic Bridge): “Map the target audience '{zielgruppe}' to the following three age brackets [18_34, 35_54, 55_plus], returning only JSON percentage weights.” * Impact: This successfully bridged the gap between a user's qualitative business profile and the rigid, quantitative municipal dataset without hardcoding assumptions.

2. Prompt 2 (The Strategic Narrative): “Your client is in the '{branche}' sector targeting '{zielgruppe}'. The algorithm identified {gemeinde} as the optimal location with a suitability score of {final_score}%. Write a concise 2-paragraph executive summary explaining why this presents a strong strategic opportunity based on their profile. Return raw text.” Impact: Instead of forcing the LLM to format messy HTML, this prompt extracts pure consultative reasoning, allowing the Python Jinja2 engine to cleanly compile the final presentation.