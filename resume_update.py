import os
import pandas as pd
from update_all_csv import load_all, process_events, save_all, print_summary

def main():
    print("=" * 80)
    print("RESUMING PIPELINE: UPDATING INTELLIGENCE DATABASE FROM EXTRACTED EVENTS")
    print("=" * 80)

    # 1. Load the database (which includes the recently generated csv/geopolitical_events.csv)
    print("\n[1/2] Loading all database files...")
    data = load_all()

    # 2. Process and save
    print("\n[2/2] Processing extracted events and updating database...")
    process_events(data)
    save_all(data)

    print("\nPipeline Completed successfully from resume script!")
    print_summary(data)

if __name__ == "__main__":
    main()
