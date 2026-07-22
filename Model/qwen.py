import requests

# -----------------------------
# CHANGE THIS
# -----------------------------
API_URL = "https://thing-rats-rouge-deeply.trycloudflare.com/chat"

TIMEOUT = 300


def ask_qwen(prompt):

    try:

        response = requests.post(

            API_URL,

            json={
                "message": prompt
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