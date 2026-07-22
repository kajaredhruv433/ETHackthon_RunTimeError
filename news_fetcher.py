import feedparser
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import re

# -----------------------------
# RSS Sources
# -----------------------------

RSS_FEEDS = {

    "Hormuz":"https://news.google.com/rss/search?q=Strait+of+Hormuz",

    "Iran":"https://news.google.com/rss/search?q=Iran+Oil",

    "RedSea":"https://news.google.com/rss/search?q=Red+Sea+Shipping",

    "OPEC":"https://news.google.com/rss/search?q=OPEC",

    "Saudi":"https://news.google.com/rss/search?q=Saudi+Oil",

    "Russia":"https://news.google.com/rss/search?q=Russia+Oil",

    "Energy":"https://news.google.com/rss/search?q=Global+Energy+Security",

    "Sanctions":"https://news.google.com/rss/search?q=Iran+Sanctions"

}

# -----------------------------
# Keywords
# -----------------------------

KEYWORDS = [

    "oil",

    "crude",

    "tanker",

    "shipping",

    "sanction",

    "hormuz",

    "red sea",

    "iran",

    "iraq",

    "saudi",

    "uae",

    "kuwait",

    "oman",

    "qatar",

    "opec",

    "refinery",

    "pipeline",

    "energy",

    "port",

    "export",

    "import",

    "cargo",

    "maritime",

    "strait",

    "bab el mandeb",

    "suez"

]

# -----------------------------
# Clean HTML
# -----------------------------

def clean_html(text):

    if text is None:

        return ""

    text = BeautifulSoup(text,"html.parser").get_text()

    text = re.sub(r"\s+"," ",text)

    return text.strip()

# -----------------------------
# Relevant?
# -----------------------------

def is_relevant(text):

    text = text.lower()

    for word in KEYWORDS:

        if word in text:

            return True

    return False

# -----------------------------
# Fetch News
# -----------------------------

def fetch_news():

    print()

    print("Fetching latest news...\n")

    articles=[]

    seen_titles=set()

    for topic,url in RSS_FEEDS.items():

        feed=feedparser.parse(url)

        print(f"{topic} -> {len(feed.entries)} Articles")

        for entry in feed.entries:

            title=clean_html(entry.get("title",""))

            summary=clean_html(entry.get("summary",""))

            published=entry.get("published","")

            link=entry.get("link","")

            full_text=title+" "+summary

            if len(full_text)<40:

                continue

            if not is_relevant(full_text):

                continue

            if title.lower() in seen_titles:

                continue

            seen_titles.add(title.lower())

            articles.append({

                "topic":topic,

                "title":title,

                "summary":summary,

                "text":full_text,

                "published":published,

                "link":link

            })

    df=pd.DataFrame(articles)

    if len(df)>0:

        try:

            df["published"]=pd.to_datetime(

                df["published"],

                errors="coerce",

                utc=True

            )

            df=df.sort_values(

                by="published",

                ascending=False

            )

        except:

            pass

    df.to_csv(

        "raw_news.csv",

        index=False,

        encoding="utf-8"

    )

    print()

    print("--------------------------------")

    print(f"Unique Relevant Articles : {len(df)}")

    print("--------------------------------")

    print()

    print("Saved raw_news.csv")

    return df

# -----------------------------
# Auto Load
# -----------------------------

if __name__ == "__main__":
    articles=fetch_news()