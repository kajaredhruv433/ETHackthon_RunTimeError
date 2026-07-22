import pandas as pd
import numpy as np
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity

from Model.embedding import embed

SIMILARITY_THRESHOLD = 0.90


def get_embedding(text):
    """
    Calls your embedding API.

    Expected API response:

    {
        "embedding":[0.12,-0.45,...]
    }
    """

    vector = embed(text)

    if vector is None:
        return None

    if isinstance(vector, str):
        return None

    if isinstance(vector, dict):
        return np.array(vector["embedding"])

    return np.array(vector)


def remove_duplicates(df):

    print()
    print("Generating embeddings...")
    print()

    embeddings = []

    for text in tqdm(df["text"]):

        emb = get_embedding(text)

        embeddings.append(emb)

    keep = []
    removed = set()

    print()
    print("Finding duplicate news...")
    print()

    for i in tqdm(range(len(df))):

        if i in removed:
            continue

        keep.append(i)

        if embeddings[i] is None:
            continue

        for j in range(i + 1, len(df)):

            if j in removed:
                continue

            if embeddings[j] is None:
                continue

            score = cosine_similarity(

                [embeddings[i]],

                [embeddings[j]]

            )[0][0]

            if score >= SIMILARITY_THRESHOLD:

                len_i = len(df.iloc[i]["text"])

                len_j = len(df.iloc[j]["text"])

                if len_i >= len_j:

                    removed.add(j)

                else:

                    removed.add(i)

                    keep.pop()

                    break

    unique_df = df.iloc[keep].reset_index(drop=True)

    unique_df.to_csv(

        "unique_news.csv",

        index=False,

        encoding="utf-8"

    )

    print()
    print("-----------------------------------")
    print("Original :", len(df))
    print("Unique   :", len(unique_df))
    print("Removed  :", len(df)-len(unique_df))
    print("-----------------------------------")

    return unique_df


if __name__ == "__main__":

    df = pd.read_csv("raw_news.csv")

    unique = remove_duplicates(df)