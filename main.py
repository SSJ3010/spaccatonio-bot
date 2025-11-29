import requests
import os
from datetime import datetime, timedelta

def send(message):
    try:
        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
                      json={"chat_id": os.environ['TELEGRAM_CHAT_ID'], "text": message}, timeout=10)
    except:
        pass

def login():
    query = """mutation ($email: String!, $password: String!) {
      signIn(email: $email, password: $password) {
        jwt errors { message }
        currentUser { twoFactorAuthenticationEnabled }
      }
    }"""
    variables = {"email": os.environ['SORARE_EMAIL'], "password": os.environ['SORARE_PASSWORD']}
    r = requests.post("https://api.sorare.com/graphql", json={"query": query, "variables": variables}, timeout=15)
    data = r.json().get("data", {}).get("signIn", {})
    if data.get("errors"):
        send(f"Login fallito: {data['errors'][0]['message']}")
        return None
    if data.get("currentUser", {}).get("twoFactorAuthenticationEnabled"):
        send("Attiva la 2FA disattivata su Sorare o usa password app")
        return None
    return data.get("jwt")

def main():
    send("Spaccatonio avviato – test connessione")
    jwt = login()
    if not jwt:
        send("Impossibile fare login – controlla email/password Sorare")
        return
    send("Login Sorare OK! Bot attivo e gira ogni minuto.\nAspetta i primi deal sotto 80% floor…")

if __name__ == "__main__":
    main()
