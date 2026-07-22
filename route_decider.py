import pandas as pd
import numpy as np
import requests
import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
# ==========================================================
# CONSTANTS
# ==========================================================

CSV_FOLDER = "csv"

# -------------------------------
# Threat Mapping
# -------------------------------

LEVEL_MAP = {
    "Very Low": 1,
    "Low": 2,
    "Medium": 3,
    "High": 4,
    "Very High": 5,

    "No": 0,
    "Partial": 0.5,
    "Yes": 1
}

SANCTION_MAP = {
    "No": 0,
    "Low": 2,
    "Medium": 5,
    "High": 10
}

# ==========================================================
# Shipping Cost ($ / Barrel)
# ==========================================================

SHIPPING_COST = {

    "Saudi Arabia":2.1,
    "UAE":1.9,
    "Iraq":2.4,
    "Kuwait":2.0,
    "Qatar":2.2,
    "Oman":2.0,

    "Nigeria":4.8,
    "Angola":5.1,
    "Brazil":6.0,
    "United States":7.2,
    "Canada":6.8,
    "Norway":6.4,
    "Russia":4.5,
    "Mexico":6.5,
    "Malaysia":3.5,
    "Australia":4.9,

}

PRICE_DIFFERENTIAL = {

    "Saudi Arabia":-0.4,
    "Iraq":-0.9,
    "UAE":0.2,
    "Kuwait":-0.5,
    "Qatar":0.3,
    "Oman":0.1,

    "Nigeria":2.0,
    "Brazil":1.8,
    "Norway":2.5,
    "United States":1.5,
    "Canada":-2.0,
    "Russia":-3.0,

}


WEIGHTS = {

    "Preference":0.40,

    "Price":0.20,

    "Route":0.15,

    "Insurance":0.10,

    "Shipping":0.05,

    "Political":0.04,

    "Export":0.03,

    "Government":0.03

}

def load_data():

    supplier = pd.read_csv(f"{CSV_FOLDER}/supplier_preference.csv")

    diplomatic = pd.read_csv(f"{CSV_FOLDER}/diplomatic_risk.csv")

    conflict = pd.read_csv(f"{CSV_FOLDER}/conflict_status.csv")

    sanctions = pd.read_csv(f"{CSV_FOLDER}/sanctions.csv")

    ports = pd.read_csv(f"{CSV_FOLDER}/port_security.csv")

    chokepoint = pd.read_csv(f"{CSV_FOLDER}/chokepoint_dependency.csv")

    exporters = pd.read_csv(f"{CSV_FOLDER}/exporters.csv")

    return {

        "supplier":supplier,
        "diplomatic":diplomatic,
        "conflict":conflict,
        "sanctions":sanctions,
        "ports":ports,
        "chokepoint":chokepoint,
        "exporters":exporters

    }

def map_levels(df):

    df = df.copy()

    for col in df.columns:

        if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:

            df[col] = df[col].replace(LEVEL_MAP)

            try:

                df[col] = pd.to_numeric(df[col], errors='raise')

            except Exception:

                pass

    return df

def normalize(series, inverse=False):

    mn = series.min()
    mx = series.max()

    if mx == mn:
        return pd.Series([100]*len(series))

    score = (series-mn)/(mx-mn)*100

    if inverse:
        score = 100-score

    return score

def shipping_cost(country):

    return SHIPPING_COST.get(country,5.5)

def differential(country):

    return PRICE_DIFFERENTIAL.get(country,0)

def clamp(x, low=0, high=100):

    return max(low,min(high,x))

import requests

API_KEY = "EFJWX5MAJVTS30I9"

def get_live_brent_price():

    url = (
        f"https://www.alphavantage.co/query?"
        f"function=BRENT"
        f"&interval=daily"
        f"&apikey={API_KEY}"
    )

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()

        data = r.json()

        # Latest price
        latest = data["data"][0]

        return float(latest["value"])

    except Exception as e:

        print(e)
        print("Using default Brent price...")

        return 78.40


def crude_price(country, brent_price):

    diff = differential(country)

    return round(brent_price + diff, 2)
def calculate_base_prices(df, brent_price):

    df = df.copy()

    prices = []

    for country in df["Country"]:

        prices.append(
            crude_price(country, brent_price)
        )

    df["Base Oil Price"] = prices

    return df
def calculate_price_score(df):

    df = df.copy()

    df["Price Score"] = normalize(
        df["Base Oil Price"],
        inverse=True
    )

    return df
def oil_price_engine(df):

    print("-"*60)
    print("Running Oil Price Engine...")
    print("-"*60)

    brent = get_live_brent_price()

    print(f"Brent Price : ${brent:.2f}/barrel")

    df = calculate_base_prices(
        df,
        brent
    )

    df = calculate_price_score(df)

    return df, brent
ROUTES = {

    "Saudi Arabia":
        "Ras Tanura → Strait of Hormuz → Arabian Sea → Mumbai",

    "UAE":
        "Fujairah → Arabian Sea → Mumbai",

    "Iraq":
        "Al Basrah → Strait of Hormuz → Arabian Sea → Mumbai",

    "Kuwait":
        "Mina Al Ahmadi → Strait of Hormuz → Arabian Sea → Mumbai",

    "Qatar":
        "Ras Laffan → Strait of Hormuz → Arabian Sea → Mumbai",

    "Oman":
        "Mina Al Fahal → Arabian Sea → Mumbai",

    "Nigeria":
        "Bonny Terminal → Cape of Good Hope → Mumbai",

    "Angola":
        "Luanda → Cape of Good Hope → Mumbai",

    "Brazil":
        "Santos → Cape of Good Hope → Mumbai",

    "United States":
        "Houston → Atlantic → Cape of Good Hope → Mumbai",

    "Canada":
        "Vancouver → Pacific Ocean → Mumbai",

    "Norway":
        "North Sea → Gibraltar → Suez → Mumbai",

    "Russia":
        "Novorossiysk → Bosphorus → Suez → Mumbai",

    "Malaysia":
        "Kertih → Strait of Malacca → Mumbai",

    "New Zealand":
        "Taranaki → Tasman Sea → Indian Ocean → Mumbai",

    "Vietnam":
        "Vung Tau → South China Sea → Strait of Malacca → Mumbai",

    "United Kingdom":
        "Hound Point → North Sea → English Channel → Gibraltar → Suez Canal → Red Sea → Arabian Sea → Mumbai",

    "Brunei":
        "Seria → South China Sea → Strait of Malacca → Mumbai",

    "Ghana":
        "Takoradi → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Trinidad & Tobago":
        "Galeota Terminal → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Guyana":
        "Georgetown → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Senegal":
        "Dakar → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Colombia":
        "Coveñas → Caribbean Sea → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Australia":
        "Dampier → Indian Ocean → Mumbai",

    "Papua New Guinea":
        "Kumul Terminal → Torres Strait → Indian Ocean → Mumbai",

    "Argentina":
        "Puerto Rosales → South Atlantic → Cape of Good Hope → Mumbai",

    "Congo":
        "Djeno Terminal → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Eq. Guinea":
        "Zafiro Terminal → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Mexico":
        "Cayo Arcas → Gulf of Mexico → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Ivory Coast":
        "Abidjan → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Suriname":
        "Paramaribo → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Ecuador":
        "Balao Terminal → Pacific Ocean → Indian Ocean → Mumbai",

    "Turkmenistan":
        "Turkmenbashi → Caspian Sea → Baku → Ceyhan Pipeline → Mediterranean → Suez Canal → Mumbai",

    "Algeria":
        "Arzew → Mediterranean → Suez Canal → Red Sea → Arabian Sea → Mumbai",

    "Gabon":
        "Cap Lopez → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Chad":
        "Kribi Terminal → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Cameroon":
        "Kole Terminal → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Kazakhstan":
        "CPC Terminal → Black Sea → Bosphorus → Suez Canal → Red Sea → Arabian Sea → Mumbai",

    "Venezuela":
        "Jose Terminal → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Azerbaijan":
        "Ceyhan Terminal → Mediterranean → Suez Canal → Red Sea → Arabian Sea → Mumbai",

    "Niger":
        "Seme Terminal → Atlantic Ocean → Cape of Good Hope → Mumbai",

    "Egypt":
        "Sidi Kerir → Suez Canal → Red Sea → Arabian Sea → Mumbai",

    "Libya":
        "Es Sider → Mediterranean → Suez Canal → Red Sea → Arabian Sea → Mumbai",

    "South Sudan":
        "Marsa Bashayer Terminal → Red Sea → Arabian Sea → Mumbai",

    "Iran":
        "Kharg Island Terminal → Strait of Hormuz → Arabian Sea → Mumbai"

}

MANUAL_PORTS = {
    "Qatar": "Ras Laffan",
    "Angola": "Luanda",
    "Canada": "Vancouver",
    "Norway": "Mongstad",
    "Malaysia": "Kertih",
    "New Zealand": "Taranaki",
    "Vietnam": "Vung Tau",
    "United Kingdom": "Hound Point",
    "Brunei": "Seria",
    "Ghana": "Takoradi",
    "Trinidad & Tobago": "Galeota Terminal",
    "Guyana": "Georgetown",
    "Senegal": "Dakar",
    "Colombia": "Coveñas",
    "Australia": "Dampier",
    "Papua New Guinea": "Kumul Terminal",
    "Argentina": "Puerto Rosales",
    "Congo": "Djeno Terminal",
    "Eq. Guinea": "Zafiro Terminal",
    "Mexico": "Cayo Arcas",
    "Ivory Coast": "Abidjan",
    "Suriname": "Paramaribo",
    "Ecuador": "Balao Terminal",
    "Turkmenistan": "Turkmenbashi",
    "Algeria": "Arzew",
    "Gabon": "Cap Lopez",
    "Chad": "Kribi Terminal",
    "Cameroon": "Kole Terminal",
    "Kazakhstan": "CPC Terminal (Novorossiysk)",
    "Azerbaijan": "Ceyhan Terminal",
    "Niger": "Seme Terminal",
    "Egypt": "Sidi Kerir Terminal",
    "South Sudan": "Marsa Bashayer Terminal"
}

def get_route(country):

    return ROUTES.get(
        country,
        "Direct Ocean Route"
    )

def get_export_port(country, ports):

    temp = ports[
        ports["Country"] == country
    ]

    if len(temp) == 0:
        return MANUAL_PORTS.get(country, "Unknown")

    return temp.iloc[0]["Port"]
def calculate_shipping(df):

    df = df.copy()

    df["Shipping Cost"] = df["Country"].apply(
        shipping_cost
    )

    return df
def calculate_shipping_score(df):

    df = df.copy()

    df["Shipping Score"] = normalize(

        df["Shipping Cost"],

        inverse=True

    )

    return df
def build_routes(df, ports):

    df = df.copy()

    routes = []

    export_ports = []

    for country in df["Country"]:

        routes.append(

            get_route(country)

        )

        export_ports.append(

            get_export_port(
                country,
                ports
            )

        )

    df["Export Port"] = export_ports

    df["Route"] = routes

    return df
def calculate_route_safety(df, chokepoint):

    safety = []

    for country in df["Country"]:

        row = chokepoint[
            chokepoint["Country"] == country
        ]

        if len(row) == 0:

            safety.append(70)

            continue

        row = row.iloc[0]

        score = 100

        score -= LEVEL_MAP[row["Hormuz"]] * 12

        score -= LEVEL_MAP[row["Red Sea"]] * 10

        score -= LEVEL_MAP[row["Bab-el-Mandeb"]] * 8

        score -= LEVEL_MAP[row["Suez"]] * 6

        score += LEVEL_MAP[row["Cape Route"]] * 3

        score = clamp(score)

        safety.append(score)

    df = df.copy()

    df["Route Safety"] = safety

    return df
def shipping_route_engine(df, ports, chokepoint):

    print("-"*60)

    print("Running Shipping Engine...")

    print("-"*60)

    df = build_routes(

        df,

        ports

    )

    df = calculate_shipping(df)

    df = calculate_shipping_score(df)

    df = calculate_route_safety(

        df,

        chokepoint

    )

    return df
BASE_INSURANCE = 0.80      # $ / barrel
WAR_COST = 0.60

CIVIL_WAR_COST = 0.50

HIGH_TERROR = 0.30

MEDIUM_TERROR = 0.15

LOW_TERROR = 0.05

SANCTION_COST = 0.40

BLOCKED_PORT = 0.40

PARTIAL_PORT = 0.20

HORMUZ_COST = 0.30

RED_SEA_COST = 0.25

BAB_COST = 0.25

SUEZ_COST = 0.20
def terror_cost(level):

    if level == "Very High":
        return 0.40

    if level == "High":
        return HIGH_TERROR

    if level == "Medium":
        return MEDIUM_TERROR

    if level == "Low":
        return LOW_TERROR

    return 0
def port_risk(country, ports):

    temp = ports[
        ports["Country"] == country
    ]

    if len(temp) == 0:

        return 0

    blocked = str(temp.iloc[0]["Blocked"])

    if blocked == "Yes":
        return BLOCKED_PORT

    if blocked == "Partial":
        return PARTIAL_PORT

    return 0
def sanction_cost(country, sanctions):

    temp = sanctions[
        sanctions["Country"] == country
    ]

    if len(temp) == 0:
        return 0

    active = temp.iloc[0]["Active"]

    if active == "Yes":
        return SANCTION_COST

    return 0
def conflict_cost(country, conflict):

    row = conflict[
        conflict["Country"] == country
    ]

    if len(row) == 0:

        return 0

    row = row.iloc[0]

    cost = 0

    if row["War"] == "Yes":

        cost += WAR_COST

    if row["Civil War"] == "Yes":

        cost += CIVIL_WAR_COST

    cost += terror_cost(
        row["Terror Risk"]
    )

    return cost
def chokepoint_cost(country, chokepoint):

    row = chokepoint[
        chokepoint["Country"] == country
    ]

    if len(row) == 0:

        return 0

    row = row.iloc[0]

    cost = 0

    if row["Hormuz"] == "Yes":

        cost += HORMUZ_COST

    if row["Red Sea"] == "Yes":

        cost += RED_SEA_COST

    if row["Bab-el-Mandeb"] == "Yes":

        cost += BAB_COST

    if row["Suez"] == "Yes":

        cost += SUEZ_COST

    return cost
def calculate_insurance(df,
                        conflict,
                        sanctions,
                        ports,
                        chokepoint):

    insurance = []

    for country in df["Country"]:

        cost = BASE_INSURANCE

        cost += conflict_cost(
            country,
            conflict
        )

        cost += sanction_cost(
            country,
            sanctions
        )

        cost += port_risk(
            country,
            ports
        )

        cost += chokepoint_cost(
            country,
            chokepoint
        )

        insurance.append(
            round(cost,2)
        )

    df = df.copy()

    df["Insurance"] = insurance

    return df
def insurance_score(df):

    df = df.copy()

    df["Insurance Score"] = normalize(

        df["Insurance"],

        inverse=True

    )

    return df
def delivered_price(df):

    df = df.copy()

    df["Delivered Price"] = (

        df["Base Oil Price"]

        +

        df["Shipping Cost"]

        +

        df["Insurance"]

    ).round(2)

    return df
def delivered_price_score(df):

    df = df.copy()

    df["Delivered Price Score"] = normalize(

        df["Delivered Price"],

        inverse=True

    )

    return df
def insurance_engine(df,
                     conflict,
                     sanctions,
                     ports,
                     chokepoint):

    print("-"*60)

    print("Running Insurance Engine...")

    print("-"*60)

    df = calculate_insurance(

        df,

        conflict,

        sanctions,

        ports,

        chokepoint

    )

    df = insurance_score(df)

    df = delivered_price(df)

    df = delivered_price_score(df)

    return df
def add_stability_scores(df, diplomatic):

    diplomatic = diplomatic.copy()

    diplomatic = map_levels(diplomatic)

    diplomatic = diplomatic.rename(columns={

        "Political Stability":"Political Score",

        "Export Stability":"Export Score",

        "Government Stability":"Government Score"

    })

    df = df.merge(

        diplomatic[[
            "Country",
            "Political Score",
            "Export Score",
            "Government Score"
        ]],

        on="Country",

        how="left"

    )

    # Convert from 1-5 to 20-100

    df["Political Score"] *= 20
    df["Export Score"] *= 20
    df["Government Score"] *= 20

    return df
def recent_event_penalty(country, events):

    col_name = None
    for c in ["Country", "country"]:
        if c in events.columns:
            col_name = c
            break

    if col_name is None:
        return 0

    temp = events[
        events[col_name] == country
    ]

    if len(temp) == 0:

        return 0

    sev_col = None
    for s in ["Severity", "severity"]:
        if s in temp.columns:
            sev_col = s
            break

    if sev_col is None:
        return 0

    severity = temp[sev_col].max()

    if severity >= 5:

        return 20

    elif severity == 4:

        return 15

    elif severity == 3:

        return 8

    elif severity == 2:

        return 4

    return 0
def add_event_penalty(df, events):

    penalties = []

    for country in df["Country"]:

        penalties.append(

            recent_event_penalty(

                country,

                events

            )

        )

    df["Event Penalty"] = penalties

    return df
def calculate_final_score(df):

    df = df.copy()

    df["Final Score"] = (

        df["Preference Score"]*WEIGHTS["Preference"]

        +

        df["Delivered Price Score"]*WEIGHTS["Price"]

        +

        df["Route Safety"]*WEIGHTS["Route"]

        +

        df["Insurance Score"]*WEIGHTS["Insurance"]

        +

        df["Shipping Score"]*WEIGHTS["Shipping"]

        +

        df["Political Score"]*WEIGHTS["Political"]

        +

        df["Export Score"]*WEIGHTS["Export"]

        +

        df["Government Score"]*WEIGHTS["Government"]

        -

        df["Event Penalty"]

    )

    df["Final Score"] = df["Final Score"].round(2)

    return df
def rank_suppliers(df):

    df = df.copy()

    df = df.sort_values(

        "Final Score",

        ascending=False

    )

    df.reset_index(

        drop=True,

        inplace=True

    )

    df["Rank"] = df.index + 1

    return df
def best_supplier(df):

    row = df.iloc[0]

    return {

        "Country":row["Country"],

        "Port":row["Export Port"],

        "Route":row["Route"],

        "Final Score":row["Final Score"],

        "Delivered Price":row["Delivered Price"]

    }
def decision_engine(df,
                    diplomatic,
                    events):

    print("-"*60)

    print("Running Decision Engine...")

    print("-"*60)

    df = add_stability_scores(

        df,

        diplomatic

    )

    df = add_event_penalty(

        df,

        events

    )

    df = calculate_final_score(

        df

    )

    df = rank_suppliers(df)

    return df
def print_best_supplier(best):

    def format_cost(value):
        if value >= 1e9:
            return f"${value / 1e9:.2f}B"
        elif value >= 1e6:
            return f"${value / 1e6:.2f}M"
        elif value >= 1e3:
            return f"${value / 1e3:.2f}K"
        return f"${value:.2f}"

    print("\n")

    print("="*80)

    print("FINAL PROCUREMENT DECISION")

    print("="*80)

    print(f"Supplier         : {best['Country']}")

    print(f"Export Port      : {best['Port']}")

    route_str = str(best.get('Route', '')).replace("→", "->")

    print(f"Shipping Route   : {route_str}")

    price = best['Delivered Price']

    print(f"Delivered Price  : ${price:.2f} per barrel")

    print(f"Total Cost (100K bbl) : {format_cost(price * 100_000)}")

    print(f"Total Cost (1M bbl)   : {format_cost(price * 1_000_000)}")

    print(f"Total Cost (100M bbl) : {format_cost(price * 100_000_000)}")

    print(f"Final Score      : {best['Final Score']:.2f}")

    print("="*80)

def save_results(df):

    import os

    os.makedirs("output", exist_ok=True)

    df.to_csv(

        "output/final_supplier_ranking.csv",

        index=False

    )