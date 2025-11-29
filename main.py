import requests
import os
import bcrypt

def send(message):
    try:
        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
                      json={"chat_id": os.environ['TELEGRAM_CHAT_ID'], "text": message}, timeout=10)
    except:
        pass

def login():
    email = os.environ['SORARE_EMAIL']
    password = os.environ['SORARE_PASSWORD'].encode('utf-8')
    
    # Prendi il salt pubblico
    salt_url = f"https://api.sorare.com/api/v1/users/{email}"
    salt_resp = requests.get(salt_url, timeout=10)
    if salt_resp.status_code != 200:
        send(f"Errore salt: {salt_resp.status_code}")
        return None
    salt = salt_resp.json()['salt'].encode('utf-8')
    
    # Hash password
    hashed = bcrypt.hashpw(password, salt).decode('utf-8')
    
    # Login con hash
    query = f'''mutation {{ signIn(input: {{email: "{email}", password: "{hashed}"}}) {{ jwt }} }}'''
    r = requests.post("https://api.sorare.com/graphql", json={"query": query}, timeout=15)
    try:
        jwt = r.json()["data"]["signIn"]["jwt"]
        return jwt
    except:
        send(f"Login fallito – risposta: {r.text[:200]}")
        return None

def main():
    send("Spaccatonio avviato – test login con hash bcrypt")
    jwt = login()
    if jwt:
        send("LOGIN OK CON HASH! Bot 100% funzionante.\nAdesso aggiungo gli alert veri domani.")
    else:
        send("Login fallito anche con hash – vediamo risposta sopra")

if __name__ == "__main__":
    main()
