import json
import argparse
import pandas as pd

def main():
    user_input = input(
        "Welcome! I am the Standort Agent, and I am here to help you find the " \
        "municipalities that best fits your business needs.\n"
        "If you need an example of the required filed press 1,\n" \
        "otherwise paste or input your profile information "
    ).strip

    if user_input == 1:
        print('{\n' \
        'branche: Fitness / Wellnessstudio,\n' \
        'flaeche_m2: 400,\n' \
        'zielgruppe: Erwachsene ab 30, gesundheitsbewusst,\n' \
        'budget_miete_eur: 6000,\n' \
        'region_praeferenz: Graz oder Linz\n' \
        '\n}'
        )
    elif user_input.startswith("{"):
        user_profile = json.loads(user_input)
