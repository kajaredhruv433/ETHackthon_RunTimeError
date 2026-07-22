import requests

# -----------------------------
# CHANGE THIS
# -----------------------------
API_URL = "https://essential-shoe-laughing-recorded.trycloudflare.com/chat"

TIMEOUT = 180


def classify(text):

    labels = [
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

    payload = {
        "text": text,
        "candidate_labels": labels
    }

    try:

        response = requests.post(
            API_URL,
            json=payload,
            timeout=TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        return data

    except requests.exceptions.RequestException as e:

        return f"Request Error: {e}"

    except Exception as e:

        return f"Error: {e}"
