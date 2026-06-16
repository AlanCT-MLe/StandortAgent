### Standort agent :space_invader:

Welcome to my Standort Agent project. The objective of this agent is to give an 
educated recommendation about the best municipality options to stablish a business
based on the **industry** :factory:, **area $m^{2}$**:triangular_ruler:, **target group**:family:, **rent-budget (euros)** :dollar:, and the **prefered region** :earth_africa: stablished by the client business needs.

#### Report HTML
You can find an example of the HTML of profil 3 here [report](https://github.com/AlanCT-MLe/StandortAgent/blob/main/location_suitability_report_profil3.html). Just download it and open with your favorite browser.

To run the Standort Agent you will need to install the required packages with **conda**:
```powershell
conda env create -f environment.yml
conda activate standort_agent
```

#### API Key and Run
1. Before running the agent you need to create a .env file in the root directory.
2. Inside .env write you Google AI key. An example is set in the file .env.example

#### Run the agent
After creating the environment and adding your Google API key, there are two options to run
the agent. Each has his own way of enter the **user profile**

1. ##### Enter a JSON profile 
    Enter the path of the JSON profile with the user profile information. In this Git
    repository you have three examples in the **example** folder.
```powershell
python main.py --profile example/profil_1.json
```

2. ##### Enter the information on the CLI
    You can enter the information by copying and pasting the dictionary with the
    user's profile information, writing **"END"** and then click enter.
```powershell
python main.py --interactive {
  "branche": "Gastronomie / Café",
  "flaeche_m2": 120,
  "zielgruppe": "Studierende und Familien",
  "budget_miete_eur": 2500,
  "region_praeferenz": "Österreich"
}
END
```

