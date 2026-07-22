import json
import pandas as pd
from tqdm import tqdm

from Model.classifier import classify


# -----------------------------
# Confidence Threshold
# -----------------------------

MIN_CONFIDENCE = 0.45


# -----------------------------
# Labels
# -----------------------------

LABELS = [

    "Military Attack",

    "Shipping Attack",

    "Sanctions",

    "Political Instability",

    "Port Closure",

    "Oil Production Cut",

    "Oil Production Increase",

    "Trade Agreement",

    "Diplomatic Meeting",

    "Natural Disaster",

    "Cyber Attack",

    "Pipeline Damage",

    "Port Congestion",

    "Oil Export Restriction",

    "Other"

]


# -----------------------------
# Classify
# -----------------------------

def classify_article(text):

    result = classify(text)

    if result is None:
        return None

    try:

        if isinstance(result, str):
            result = json.loads(result)

        return result

    except Exception:

        print("Invalid JSON received from classifier")

        print(result)

        return None


from concurrent.futures import ThreadPoolExecutor, as_completed

MAX_WORKERS = 10


# -----------------------------
# Process News
# -----------------------------

def process_news(df):

    print()
    print("Classifying Articles...")
    print()

    results = [None] * len(df)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        future_map = {}

        for index, row in df.iterrows():

            future = executor.submit(

                classify_article,

                row["text"]

            )

            future_map[future] = index

        for future in tqdm(

                as_completed(future_map),

                total=len(future_map)

        ):

            idx = future_map[future]

            try:

                results[idx] = future.result()

            except Exception as e:

                print(f"Error classifying article {idx}: {e}")

                results[idx] = None

    final_rows = []

    for idx, row in df.iterrows():

        result = results[idx]

        if result is None:
            continue

        label = result.get("label", "Other")
        score = float(result.get("score", 0))

        if score < MIN_CONFIDENCE:
            continue

        row_dict = row.to_dict()

        row_dict["event_type"] = label
        row_dict["confidence"] = round(score, 3)

        final_rows.append(row_dict)

    if not final_rows:

        classified = pd.DataFrame(columns=list(df.columns) + ["event_type", "confidence"])

    else:

        classified = pd.DataFrame(final_rows)

    classified.to_csv(

        "classified_news.csv",

        index=False,

        encoding="utf-8"

    )

    print()

    print("--------------------------------")

    print("Articles after Classification :", len(classified))

    print("--------------------------------")

    print()

    print("Saved classified_news.csv")

    return classified


# -----------------------------
# Main
# -----------------------------

if __name__ == "__main__":

    df = pd.read_csv("unique_news.csv")

    classified = process_news(df)