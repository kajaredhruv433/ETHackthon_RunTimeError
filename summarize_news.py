import pandas as pd
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

from Model.summarizer import summarize

# ---------------------------------------
# Number of parallel API requests
# ---------------------------------------

MAX_WORKERS = 6


def summarize_article(text):

    try:

        summary = summarize(text)

        if summary is None:
            return ""

        return summary.strip()

    except Exception as e:

        print(e)

        return ""


def process_news(df):

    print()
    print("Summarizing Articles...")
    print()

    summaries = [""] * len(df)

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        future_map = {}

        for index, row in df.iterrows():

            future = executor.submit(

                summarize_article,

                row["text"]

            )

            future_map[future] = index

        for future in tqdm(

                as_completed(future_map),

                total=len(future_map)

        ):

            idx = future_map[future]

            try:

                summaries[idx] = future.result()

            except:

                summaries[idx] = ""

    df["summary_ai"] = summaries

    df.to_csv(

        "summarized_news.csv",

        index=False,

        encoding="utf-8"

    )

    print()

    print("--------------------------------")

    print("Articles Summarized :", len(df))

    print("--------------------------------")

    print()

    print("Saved summarized_news.csv")

    return df


if __name__ == "__main__":

    df = pd.read_csv("classified_news.csv")

    process_news(df)