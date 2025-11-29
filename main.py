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
    
    # Prendi salt
    r = requests.get(f"https://api.sorare.com/api/v1/users/{email}", timeout=10)
    if r.status_code != 200:
        send(f"Salt fallito: {r.status_code}")
        return None
    salt = r.json()['salt'].encode('utf-8')
    
    hashed = bcrypt.hashpw(password, salt).decode('utf-8')
    
    # Mutation aggiornata 2025
    query = """
    mutation SignIn($email: String!, $password: String!) {
      signIn(email: $email, password: $password) {
        jwt
        errors { message }
      }
    }
    """
    variables = {"email": email, "password": hashed}
    resp = requests.post("https://api.sorare.com/graphql",
                         json={"query": query, "variables": variables}, timeout=15)
    data = resp.json().get("data", {}).get("signIn", {})
    if data.get("errors"):
        send(f"Login fallito: {data['errors'][0]['message']}")
        return None
    return data.get("jwt")

def main():
    send("Spaccatonio 2025 – test finale")
    jwt = login()
    if jwt:
        send("LOGIN OK DEFINITIVO!\nBot gira ogni minuto.\nDomani mattina ti mando la versione con alert reali sotto 80%.")
    else:
        send("Ancora no – ma ci siamo quasi")

if __name__ == "__main__":
    main()
