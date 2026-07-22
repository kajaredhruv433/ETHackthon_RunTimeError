import os
import pandas as pd
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from Model.groq import ask_groq

CSV_FOLDER = "csv"


# ---------------------------------------------------
# Utility
# ---------------------------------------------------

def csv_path(file_name):
    return os.path.join(CSV_FOLDER, file_name)


def load_csv(file_name):
    return pd.read_csv(csv_path(file_name))


def save_csv(df, file_name):
    df.to_csv(csv_path(file_name), index=False)


def level_to_score(level):
    """
    Converts

    Very Low
    Low
    Medium
    High
    Very High

    into numbers
    """

    if pd.isna(level):
        return 0

    mapping = {
        "Very Low":1,
        "Low":2,
        "Medium":3,
        "High":4,
        "Very High":5
    }

    return mapping.get(str(level).strip(),0)


def score_to_level(score):

    if score<=1:
        return "Very Low"

    elif score==2:
        return "Low"

    elif score==3:
        return "Medium"

    elif score==4:
        return "High"

    return "Very High"

def load_all():

    data={}

    data["events"] = load_csv("geopolitical_events.csv")

    data["supplier"] = load_csv("supplier_preference.csv")

    data["sanctions"] = load_csv("sanctions.csv")

    data["ports"] = load_csv("port_security.csv")

    data["conflict"] = load_csv("conflict_status.csv")

    data["diplomatic"] = load_csv("diplomatic_risk.csv")

    data["dependency"] = load_csv("chokepoint_dependency.csv")

    data["relation"] = load_csv("geopolitical_relation.csv")

    data["exporters"] = load_csv("exporters.csv")

    data["supplier_dependency"] = load_csv("supplier_dependency.csv")

    # Keep only countries that exist in the exporters list
    exporters_list = data["exporters"]["Country"].unique().tolist()
    data["supplier"] = data["supplier"][data["supplier"]["Country"].isin(exporters_list)]

    return data

def save_all(data):

    save_csv(data["supplier"],"supplier_preference.csv")

    save_csv(data["sanctions"],"sanctions.csv")

    save_csv(data["ports"],"port_security.csv")

    save_csv(data["conflict"],"conflict_status.csv")

    save_csv(data["diplomatic"],"diplomatic_risk.csv")

    save_csv(data["dependency"],"chokepoint_dependency.csv")

def get_supplier(data,country):

    df=data["supplier"]

    if pd.isna(country) or not isinstance(country, str) or country.strip().lower() in ["none", "nan", ""]:

        return None

    exporters_list = data["exporters"]["Country"].unique().tolist()
    match = [c for c in exporters_list if c.lower() == country.lower()]
    if match:
        country = match[0]
    else:
        return None

    row=df[df["Country"]==country]

    if row.empty:

        new_row={

            "Country":country,

            "Preference Score":80,

            "Political Risk":10,

            "Sanction Risk":0,

            "Conflict Risk":0,

            "Export Stability":90,

            "Port Risk":20,

            "Chokepoint Risk":20,

            "Confidence":0.90

        }

        df.loc[len(df)] = new_row

        row=df[df["Country"]==country]

        data["supplier"]=df

    if row.empty:

        return None

    return row.index[0]
def increase(value,amount,max_value=100):

    return min(max_value,value+amount)


def decrease(value,amount,min_value=0):

    return max(min_value,value-amount)
def update_conflict(data, country, event, severity):

    df = data["conflict"]

    idx = df[df["Country"] == country].index

    if len(idx) == 0:
        return

    idx = idx[0]

    event = str(event).lower()

    if "war" in event:
        df.at[idx, "War"] = "Yes"

    if "civil" in event:
        df.at[idx, "Civil War"] = "Yes"

    if severity >= 8:
        df.at[idx, "Internal Stability"] = "Very Low"

    elif severity >= 6:
        df.at[idx, "Internal Stability"] = "Low"

    elif severity >= 4:
        df.at[idx, "Internal Stability"] = "Medium"

    else:
        df.at[idx, "Internal Stability"] = "High"

    if any(word in event for word in [
        "attack",
        "missile",
        "terror",
        "drone",
        "explosion",
        "military"
    ]):

        if severity >= 8:
            df.at[idx, "Terror Risk"] = "Very High"

        elif severity >= 6:
            df.at[idx, "Terror Risk"] = "High"

        elif severity >= 4:
            df.at[idx, "Terror Risk"] = "Medium"

        else:
            df.at[idx, "Terror Risk"] = "Low"

def update_diplomatic(data, country, event, severity):

    df = data["diplomatic"]

    idx = df[df["Country"] == country].index

    if len(idx) == 0:
        return

    idx = idx[0]

    political = level_to_score(df.at[idx, "Political Stability"])

    export = level_to_score(df.at[idx, "Export Stability"])

    government = level_to_score(df.at[idx, "Government Stability"])

    event = str(event).lower()

    if any(word in event for word in [
        "sanction",
        "attack",
        "war",
        "missile",
        "protest",
        "military",
        "pipeline"
    ]):

        political += 1
        government += 1

    if any(word in event for word in [
        "export",
        "terminal",
        "oil",
        "pipeline",
        "refinery",
        "production"
    ]):

        export += 1

    political = min(5, political)
    export = min(5, export)
    government = min(5, government)

    df.at[idx, "Political Stability"] = score_to_level(political)

    df.at[idx, "Export Stability"] = score_to_level(export)

    df.at[idx, "Government Stability"] = score_to_level(government)

def update_sanctions(data, country, event, severity):

    df = data["sanctions"]

    idx = df[df["Country"] == country].index

    if len(idx) == 0:
        return

    idx = idx[0]

    event = str(event).lower()

    if "sanction" in event:

        df.at[idx, "Sanctioned"] = "Yes"

        df.at[idx, "Active"] = "Yes"

        if severity >= 8:
            df.at[idx, "Severity"] = "Very High"

        elif severity >= 6:
            df.at[idx, "Severity"] = "High"

        elif severity >= 4:
            df.at[idx, "Severity"] = "Medium"

        else:
            df.at[idx, "Severity"] = "Low"
def update_ports(data, country, event, severity):

    df = data["ports"]

    ports = df[df["Country"] == country]

    if ports.empty:
        return

    event = str(event).lower()

    for idx in ports.index:

        if any(word in event for word in [
            "port",
            "terminal",
            "harbour",
            "harbor",
            "missile",
            "drone",
            "attack",
            "naval"
        ]):

            if severity >= 8:

                df.at[idx, "Risk"] = "Very High"

                df.at[idx, "Military Threat"] = "Very High"

            elif severity >= 6:

                df.at[idx, "Risk"] = "High"

                df.at[idx, "Military Threat"] = "High"

            elif severity >= 4:

                df.at[idx, "Risk"] = "Medium"

                df.at[idx, "Military Threat"] = "Medium"

            else:

                df.at[idx, "Risk"] = "Low"

        if "blocked" in event or "closure" in event:

            df.at[idx, "Blocked"] = "Yes"

        if "sanction" in event:

            df.at[idx, "Sanctions"] = "Yes"

def update_chokepoints(data, country, event, severity):

    df = data["dependency"]

    idx = df[df["Country"] == country].index

    if len(idx) == 0:
        return

    idx = idx[0]

    event = str(event).lower()

    if "hormuz" in event:
        df.at[idx, "Hormuz"] = "Yes"

    if "red sea" in event:
        df.at[idx, "Red Sea"] = "Yes"

    if "suez" in event:
        df.at[idx, "Suez"] = "Yes"

    if "bab" in event:
        df.at[idx, "Bab-el-Mandeb"] = "Yes"

    if "cape" in event:
        df.at[idx, "Cape Route"] = "Yes"

def update_supplier_preference(data, country, event, severity):

    idx = get_supplier(data, country)

    if idx is None:

        return

    df = data["supplier"]

    political = df.at[idx, "Political Risk"]

    sanction = df.at[idx, "Sanction Risk"]

    conflict = df.at[idx, "Conflict Risk"]

    export = df.at[idx, "Export Stability"]

    port = df.at[idx, "Port Risk"]

    chokepoint = df.at[idx, "Chokepoint Risk"]

    confidence = df.at[idx, "Confidence"]

    event = str(event).lower()

    # -------------------------------
    # Political Events
    # -------------------------------

    if any(word in event for word in [

        "government",

        "protest",

        "election",

        "political",

        "diplomatic"

    ]):

        political = increase(political, severity)

    # -------------------------------
    # War
    # -------------------------------

    if any(word in event for word in [

        "war",

        "attack",

        "missile",

        "drone",

        "terror",

        "military"

    ]):

        conflict = increase(conflict, severity)

        port = increase(port, severity)

    # -------------------------------
    # Sanctions
    # -------------------------------

    if "sanction" in event:

        sanction = increase(sanction, severity)

    # -------------------------------
    # Oil Export
    # -------------------------------

    if any(word in event for word in [

        "pipeline",

        "export",

        "terminal",

        "production",

        "refinery",

        "oil"

    ]):

        export = decrease(export, severity)

    # -------------------------------
    # Chokepoints
    # -------------------------------

    if any(word in event for word in [

        "hormuz",

        "red sea",

        "suez",

        "bab",

        "shipping",

        "naval"

    ]):

        chokepoint = increase(chokepoint, severity)

    confidence = round(

        min(

            1.0,

            confidence + 0.01

        ),

        2

    )

    df.at[idx, "Political Risk"] = political

    df.at[idx, "Sanction Risk"] = sanction

    df.at[idx, "Conflict Risk"] = conflict

    df.at[idx, "Export Stability"] = export

    df.at[idx, "Port Risk"] = port

    df.at[idx, "Chokepoint Risk"] = chokepoint

    df.at[idx, "Confidence"] = confidence

def calculate_preference_score(data):

    df = data["supplier"]
    dep_df = data["dependency"]
    exp_df = data["exporters"]
    events_df = data["events"]
    rel_df = data["relation"]
    dep_sup_df = data["supplier_dependency"]

    print("\nCalculating Geopolitical Supplier Preference Scores using multi-factor formula...")

    for idx in df.index:
        country = df.at[idx, "Country"]

        # 1. Base Score
        base = float(df.at[idx, "Export Stability"])

        # 2. Risk parameters from supplier_preference.csv
        political = float(df.at[idx, "Political Risk"])
        sanction = float(df.at[idx, "Sanction Risk"])
        conflict = float(df.at[idx, "Conflict Risk"])
        port = float(df.at[idx, "Port Risk"])
        chokepoint = float(df.at[idx, "Chokepoint Risk"])

        # 3. Geopolitical Relation with India
        relation_with_india = 80  # Default
        rel_row = rel_df[rel_df["Country"] == country]
        if not rel_row.empty:
            relation_with_india = float(rel_row.iloc[0].get("Relation with India", 80))

        # 4. Spare capacity and import share from supplier_dependency.csv
        spare_capacity_val = 0.0
        import_share = 0.0
        dep_row = dep_sup_df[dep_sup_df["Country"] == country]
        if not dep_row.empty:
            dep_row = dep_row.iloc[0]
            import_share = float(dep_row.get("India Import %", 0.0))
            spare_cap_str = str(dep_row.get("Spare Capacity", "0.0")).lower()
            try:
                spare_capacity_val = float(spare_cap_str.split()[0])
            except Exception:
                spare_capacity_val = 0.0

        # Capacity and relation bonuses
        relation_bonus = (relation_with_india - 75) * 0.5
        spare_capacity_bonus = spare_capacity_val * 6
        import_share_bonus = import_share * 0.2  # Tie-breaker to favor larger established suppliers

        # Core supplier bonus from exporters.csv
        core_bonus = 0
        exp_row = exp_df[exp_df["Country"] == country]
        if not exp_row.empty:
            exp_row = exp_row.iloc[0]
            curr_export = str(exp_row.get("Current Export to India", "")).strip().lower()
            if "high" in curr_export:
                core_bonus = 15
            elif "medium" in curr_export:
                core_bonus = 10
            elif "low" in curr_export or "spot" in curr_export:
                core_bonus = 3

        # 5. Chokepoint dependency penalties and bonuses
        choke_penalty = 0
        diversification_bonus = 0
        resilience_bonus = 0

        choke_row = dep_df[dep_df["Country"] == country]
        if not choke_row.empty:
            choke_row = choke_row.iloc[0]
            hormuz = str(choke_row.get("Hormuz", "No")).strip()
            red_sea = str(choke_row.get("Red Sea", "No")).strip()
            bab = str(choke_row.get("Bab-el-Mandeb", "No")).strip()

            # Hormuz dependency penalty (very high shipping risk)
            if hormuz == "Yes":
                choke_penalty += 35
            elif hormuz == "Partial":
                choke_penalty += 5
                resilience_bonus += 10  # Resilient: can partially bypass Hormuz (e.g. UAE)

            # Red Sea dependency penalty (Houthi blockade risk)
            if red_sea == "Yes" or bab == "Yes":
                choke_penalty += 20
            elif red_sea == "Partial" or bab == "Partial":
                choke_penalty += 10

            # Diversification bonus (entirely outside Middle East / no chokepoints)
            if hormuz == "No" and red_sea == "No" and bab == "No":
                diversification_bonus += 10  # Nigeria, Brazil, etc.

        # 6. Geopolitical event warning signals
        country_events = events_df[events_df["Country"].str.lower() == country.lower()]
        events_penalty = 0
        for _, ev in country_events.iterrows():
            event_text = str(ev['Event']).lower()
            severity = int(ev['Severity'])
            # Refiners cancel cargo / security concerns
            if any(w in event_text for w in ["cancel", "cargo", "lifting"]):
                events_penalty += severity * 4
            elif any(w in event_text for w in ["concerns", "reduction", "security"]):
                events_penalty += severity * 2.5
            if any(w in event_text for w in ["strike", "attack", "refinery damage"]):
                events_penalty += severity * 1.5

        # 7. Specific geopolitical rules based on user criteria (July 2026 context)
        special_adjustment = 0
        country_lower = country.lower()
        if "uae" in country_lower or "united arab emirates" in country_lower:
            special_adjustment += 8   # Highlight UAE as a very strong resilient choice
        elif "nigeria" in country_lower:
            special_adjustment += 6   # Highlight Nigeria as good diversification
        elif "iraq" in country_lower:
            special_adjustment -= 15  # Penalty for Iraq due to cancelations and shipping risk

        # Weighted multi-factor equation (Quadrilateral-style representation of priorities)
        score = (
            base * 0.7
            + relation_bonus
            + spare_capacity_bonus
            + import_share_bonus
            + core_bonus
            + diversification_bonus
            + resilience_bonus
            + special_adjustment
            - political * 0.5
            - sanction * 1.5
            - conflict * 0.8
            - port * 0.1
            - chokepoint * 0.1
            - choke_penalty
            - events_penalty
        )

        # Round and bound
        score = int(round(score))
        score = max(0, min(100, score))
        df.at[idx, "Preference Score"] = score
def process_events(data):

    events = data["events"]

    # Reset supplier risks and scores to baseline before updating
    df = data["supplier"]
    df["Political Risk"] = 10
    df["Sanction Risk"] = 0
    df["Conflict Risk"] = 0
    df["Export Stability"] = 90
    df["Port Risk"] = 20
    df["Chokepoint Risk"] = 20
    df["Confidence"] = 0.90
    df["Preference Score"] = 0
    data["supplier"] = df

    print()

    print("----------------------------------")

    print("Processing Events")

    print("----------------------------------")

    for _, row in events.iterrows():

        country = row["Country"]

        if pd.isna(country) or not isinstance(country, str) or country.strip().lower() in ["none", "nan", ""]:

            continue

        event = row["Event"]

        severity = int(row["Severity"])

        print(country, "->", event)

        update_conflict(

            data,

            country,

            event,

            severity

        )

        update_diplomatic(

            data,

            country,

            event,

            severity

        )

        update_sanctions(

            data,

            country,

            event,

            severity

        )

        update_ports(

            data,

            country,

            event,

            severity

        )

        update_chokepoints(

            data,

            country,

            event,

            severity

        )

        update_supplier_preference(

            data,

            country,

            event,

            severity

        )

    calculate_preference_score(data)

def print_summary(data):

    print("\n" + "=" * 60)
    print("UPDATE SUMMARY")
    print("=" * 60)

    supplier = data["supplier"]

    supplier = supplier.sort_values(
        "Preference Score",
        ascending=False
    )

    print("\nTop Preferred Suppliers\n")

    print(
        supplier[
            [
                "Country",
                "Preference Score",
                "Confidence"
            ]
        ].head(10).to_string(index=False)
    )

    print("\nCSV files updated successfully.")
def clear_events():

    columns = [
        "Time",
        "Country",
        "Event",
        "Severity"
    ]

    pd.DataFrame(columns=columns).to_csv(
        csv_path("geopolitical_events.csv"),
        index=False
    )