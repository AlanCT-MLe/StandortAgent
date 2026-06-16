import argparse
import json
from standort_agent.orchestrator import Orchestrator
import pandas as pd
from pathlib import Path

def load_profile(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def interactive_mode():
    print("Paste JSON (END to finish):")

    lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        lines.append(line)

    return json.loads("\n".join(lines))

def save_profile(profile, path="data/user_profile.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=4, ensure_ascii=False)

def location_matches(user_city, location):
    base_name = location.split("(")[0].strip().lower()
    return user_city.lower().strip() == base_name

def form(preference):
    """
    To give format to the users input
    """
    if type(preference) == str:
        preference = str(preference).strip().lower().replace("oder",",").replace("and", ",").split(",")
    else:
        preference = [string.lower() for string in preference]
        preference = [s.split("(")[0].strip() for s in preference]
    return set([p for p in preference if p])

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=str)
    parser.add_argument("--interactive", action="store_true")

    args = parser.parse_args()

    if not args.profile and not args.interactive:
        print("No arguments provided → switching to interactive mode by default")
        args.interactive = True

    if args.profile:
        with open(args.profile, "r", encoding="utf-8") as f:
            business_profile = json.load(f)
        print("read user profile")

    elif args.interactive:
        business_profile = interactive_mode()

        save_profile(business_profile)

        print("Profile saved to data/user_profile.json")


    # Filter Data
    csv_path = Path("data") / "municipalities.csv"
    df = pd.read_csv(csv_path)

    regions = df['bundesland'].unique()
    mp = df['gemeinde'].unique()

    up = business_profile["region_praeferenz"]
    user_profile = form(up)
    relevant_region = [loc for loc in regions if any(city.strip() in loc.lower() for city in user_profile)]
    relevant_mp = [loc for loc in mp if any(location_matches(city, loc) for city in user_profile)]
    austria = ["österreich", "osterreich", "austria", ""]

    if any(part.strip() in austria for part in user_profile):
        df_result = df.copy()
    elif (len(relevant_region)) > 0 or (len(relevant_mp) > 0) :
        mask = df["bundesland"].isin(relevant_region) | df["gemeinde"].isin(relevant_mp)
        df_result = df[mask].copy()
    else:
        raise ValueError("No known preferred locations found. Watch out for typos")

    orchestrator = Orchestrator(df_result,business_profile)
    report_path = orchestrator.run_and_report() 

if __name__ == "__main__":
    main()