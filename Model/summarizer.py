import requests

# -----------------------------
# CHANGE THIS
# -----------------------------
API_URL = "https://healthcare-bailey-mailto-mechanism.trycloudflare.com/chat"

TIMEOUT = 180


def summarize(text):

    try:

        response = requests.post(

            API_URL,

            json={
                "message": text
            },

            timeout=TIMEOUT

        )

        response.raise_for_status()

        data = response.json()

        return data.get("response", "")

    except requests.exceptions.RequestException as e:

        return f"Request Error: {e}"

    except Exception as e:

        return f"Error: {e}"