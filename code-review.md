

### Bug Found

The signals "demographic_score", "poi_score", and "rent_score" are consider
to be the higher the better. The "rent_score" gives you the value in Euros per $m^{2}$, and the **lower** the better. The given function add this to the score, this will make the expensive the rent the higher the recommendation score, which
is wrong. Additionally, the municipalities scores are not normalized.

```python
from typing import Any

def score_municipalities(
    municipalities: list[dict[str, Any]],
    weights: dict[str, float] | None = None,
) -> list[tuple[str, float]]:
    
    if weights is None:
        weights = {
            "demographics_score": 0.30,
            "poi_score": 0.25,
            "rent_score": 0.30,
            "transit_score": 0.15,
        }

    # 
    flux = {
        "demographics_score": True,
        "poi_score": True,
        "rent_score": False,  
        "transit_score": True
    }

    # 3. Calculate Global Bounds for Normalization
    bounds = {}
    for signal in weights:
        # Fails fast with a KeyError if a dictionary is missing a required signal
        values = [m[signal] for m in municipalities]
        bounds[signal] = {"min": min(values), "max": max(values)}

    results = []
    for m in municipalities:
        total = 0.0
        for signal, weight in weights.items():
            min_value, max_value = bounds[signal]["min"], bounds[signal]["max"]
            range_val = max_value - min_value
            
            # FIX: Scaling / Normalization
            if delta_val == 0:
                normalization_score = 1.0 # Prevent ZeroDivisionError if all locations have same score
            else:
                if flux.get(signal, True):
                    normalization_score = (m[signal] - min_value) / delta_val
                else:
                    normalization_score = (max_value - m[signal]) / delta_val # 
            
            total += normaslization_score * weight
            
        results.append((m["gemeinde"], total))

    results.sort(key=lambda x: x[1], reverse=True)
    return results
```

#### Issues

1. The user can enter a weights dictionary with weights that sum > 1.
2. The **keys** of the weights dictionary can be different to the **keys** of the municipalities dictionary, if enter by the user. Creating an error.
3. There is no normalization of the weighted signals. Having different scales would give a false score.
4. The argument municipalities definition use the function Any, which allow the
user to enter any object to keys of the dictionary. There is no safety check to
review that only the "community" value is a string and the rest of the items of the keys are floats. 
5. The demographic score just refers to the proportion of 18-34 years old, it ignores the rest of the demographic. Making the score bias.
