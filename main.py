import pandas as pd
import sys

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from news_fetcher import fetch_news
from deduplicate import remove_duplicates
from classify_news import process_news as classify
from summarize_news import process_news as summarize
from extract_events import extract

from update_all_csv import (
    load_all,
    process_events,
    save_all,
    print_summary,
)
from route_decider import (
    load_data,
    oil_price_engine,
    shipping_route_engine,
    insurance_engine,
    decision_engine,
    save_results,
    best_supplier,
    print_best_supplier,
)


def banner():
    print("=" * 80)
    print("AI POWERED GEOPOLITICAL ENERGY INTELLIGENCE SYSTEM")
    print("=" * 80)


def main():

    banner()

    # ----------------------------------------
    # 1. Fetch News
    # ----------------------------------------
    print("\n[1/6] Fetching News...")

    raw_df = fetch_news()

    # ----------------------------------------
    # 2. Remove Duplicates
    # ----------------------------------------
    print("\n[2/6] Removing Duplicates...")

    unique_df = remove_duplicates(raw_df)

    # ----------------------------------------
    # 3. Classify News
    # ----------------------------------------
    print("\n[3/6] Classifying News...")

    classified_df = classify(unique_df)

    # ----------------------------------------
    # 4. Summarize News
    # ----------------------------------------
    print("\n[4/6] Summarizing Articles...")

    summarized_df = summarize(classified_df)

    # ----------------------------------------
    # 5. Extract Events
    # ----------------------------------------
    print("\n[5/6] Extracting Events...")

    extract(summarized_df)

    # ----------------------------------------
    # 6. Update CSV Intelligence Database
    # ----------------------------------------
    print("\n[6/7] Updating Intelligence Database...")

    data = load_all()

    process_events(data)

    save_all(data)

    print_summary(data)

    # ----------------------------------------
    # 7. Run Procurement Decision Engine
    # ----------------------------------------
    print("\n[7/7] Running Procurement Decision Engine...")

    dec_data = load_data()
    supplier = dec_data["supplier"]

    # Oil Price Engine
    supplier, brent = oil_price_engine(supplier)
    print("\nAfter Oil Price Engine\n")
    print(supplier[["Country", "Base Oil Price", "Price Score"]].head())

    # Shipping Engine
    supplier = shipping_route_engine(
        supplier,
        dec_data["ports"],
        dec_data["chokepoint"]
    )
    print("\nAfter Shipping Engine\n")
    print(
        supplier[
            [
                "Country",
                "Export Port",
                "Route",
                "Shipping Cost",
                "Shipping Score",
                "Route Safety"
            ]
        ].head()
    )

    # Insurance Engine
    supplier = insurance_engine(
        supplier,
        dec_data["conflict"],
        dec_data["sanctions"],
        dec_data["ports"],
        dec_data["chokepoint"]
    )
    print("\nAfter Insurance Engine\n")
    print(
        supplier[
            [
                "Country",
                "Insurance",
                "Delivered Price",
                "Insurance Score",
                "Delivered Price Score"
            ]
        ].head()
    )

    # Decision Engine
    events = pd.read_csv("csv/geopolitical_events.csv")
    supplier = decision_engine(
        supplier,
        dec_data["diplomatic"],
        events
    )

    # Save
    save_results(supplier)

    # Print Final Ranking
    print("\n")
    print("=" * 120)
    print("FINAL SUPPLIER RANKING")
    print("=" * 120)
    print(
        supplier[
            [
                "Rank",
                "Country",
                "Final Score",
                "Delivered Price",
                "Route",
                "Export Port"
            ]
        ]
    )

    # Best Supplier
    best = best_supplier(supplier)
    print_best_supplier(best)

    print("\nPipeline and Decision Engine Completed Successfully.")


if __name__ == "__main__":
    main()