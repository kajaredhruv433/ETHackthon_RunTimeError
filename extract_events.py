import json
import re
import pandas as pd
from tqdm import tqdm

from Model.qwen import ask_qwen


# ----------------------------------------------------
# Prompt Builder
# ----------------------------------------------------

def build_prompt(article):

    prompt = f"""

You are an Energy Security Intelligence Analyst.

Your task is to analyse the following geopolitical news.

Return ONLY VALID JSON.

Do NOT explain.

Do NOT use markdown.

Do NOT write ```json.

----------------------------

Article:

{article}

----------------------------

Determine:

1. Country where event occurred.

2. Main Actor.

3. Event Type.

Possible Event Types:

Military Attack
Shipping Attack
Sanctions
Political Instability
Port Closure
Oil Production Cut
Oil Production Increase
Trade Agreement
Diplomatic Meeting
Pipeline Damage
Natural Disaster
Cyber Attack
Port Congestion
Other

4. Severity (0-5)

0 = No impact

5 = Extremely High Impact

5. Political Risk (0-5)

6. Export Risk (0-5)

7. Is India affected?

true/false

8. Which exporters are affected?

Return list.

9. Which ports are affected?

Return list.

10. Which chokepoints are affected?

Possible values:

Strait of Hormuz

Bab el-Mandeb

Suez Canal

Red Sea

Malacca Strait

Panama Canal

11. Is there any sanction?

true/false

12. Short reason (maximum 30 words)

Return ONLY this JSON:

{{
"country":"",
"actor":"",
"event_type":"",
"severity":0,
"political_risk":0,
"export_risk":0,
"india_affected":false,
"affected_exporters":[],
"affected_ports":[],
"affected_chokepoints":[],
"sanction":false,
"reason":""
}}

"""

    return prompt


# ----------------------------------------------------
# Parse JSON
# ----------------------------------------------------

def parse_json(response):

    if response is None:
        return None

    response = response.strip()

    response = response.replace("```json","")

    response = response.replace("```","")

    match = re.search(r"\{.*\}",response,re.DOTALL)

    if match:

        try:

            return json.loads(match.group())

        except:

            return None

    return None


# ----------------------------------------------------
# Extract Events
# ----------------------------------------------------

def extract(df):

    print()
    print("Extracting Geopolitical Intelligence...")
    print()

    events=[]

    for _,row in tqdm(df.iterrows(),total=len(df)):

        prompt=build_prompt(row["summary_ai"])

        reply=ask_qwen(prompt)

        data=parse_json(reply)

        if data is None:

            continue

        data["title"]=row["title"]

        data["published"]=row["published"]

        data["link"]=row["link"]

        data["summary"]=row["summary_ai"]

        # Map to capitalized keys for update_all_csv.py
        data["Country"] = data.get("country", "")
        event_type = data.get("event_type", "")
        reason = data.get("reason", "")
        data["Event"] = f"{event_type}: {reason}" if event_type and reason else (event_type or reason)
        data["Severity"] = data.get("severity", 0)
        data["Time"] = row.get("published", "")

        events.append(data)

    if not events:

        events_df = pd.DataFrame(columns=["Time", "Country", "Event", "Severity"])

    else:

        events_df=pd.DataFrame(events)

    events_df.to_csv(

        "csv/geopolitical_events.csv",

        index=False,

        encoding="utf-8"

    )

    print()

    print("--------------------------------")

    print("Events Extracted :",len(events_df))

    print("--------------------------------")

    print()

    print("Saved csv/geopolitical_events.csv")

    return events_df


# ----------------------------------------------------
# Main
# ----------------------------------------------------

if __name__=="__main__":

    df=pd.read_csv("summarized_news.csv")

    extract(df)