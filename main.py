import requests
import os
from datetime import datetime, timedelta

def send_telegram(message):
    url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage"
    payload = {"chat_id": os.environ['TELEGRAM_CHAT_ID'], "text": message, "disable_web_page_preview": True}
    requests.post(url, json=payload)

def login_sorare():
    query = """
    mutation ($email: String!, $password: String!) {
      signIn(email: $email, password: $password) { jwt }
    }
    """
    variables = {"email": os.environ['SORARE_EMAIL'], "password": os.environ['SORARE_PASSWORD']}
    r = requests.post("https://api.sorare.com/graphql", json={"query": query, "variables": variables})
    return r.json()["data"]["signIn"]["jwt"]

def get_floor(jwt, player_slug, rarity):
    query = """
    query ($slug: String!, $rarity: Rarity!) {
      player(slug: $slug) {
        cards(rarities: [$rarity]) {
          nodes {
            singleSaleOffer { price(currency: EUR) }
          }
        }
      }
    }
    """
    headers = {"Authorization": f"Bearer {jwt}"}
    variables = {"slug": player_slug, "rarity": rarity}
    r = requests.post("https://api.sorare.com/graphql", json={"query": query, "variables": variables}, headers=headers)
    prices = [node["singleSaleOffer"]["price"] for node in r.json()["data"]["player"]["cards"]["nodes"] if node["singleSaleOffer"]]
    return min(prices) if prices else None

def main():
    try:
        jwt = login_sorare()
        start_time = (datetime.utcnow() - timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        query = """
        query ($time: DateTime!) {
          offers(first: 100, where: {rarity_in: [LIMITED, RARE], price_gte: 3, price_lte: 30, createdAt_gte: $time}) {
            nodes {
              id price(currency: EUR) createdAt
              card { rarity player { displayName slug } }
            }
          }
        }
        """
        headers = {"Authorization": f"Bearer {jwt}"}
        variables = {"time": start_time}
        data = requests.post("https://api.sorare.com/graphql", json={"query": query, "variables": variables}, headers=headers).json()
        offers = data["data"]["offers"]["nodes"]

        for o in offers:
            price = o["price"]
            player_slug = o["card"]["player"]["slug"]
            rarity = o["card"]["rarity"]
            floor = get_floor(jwt, player_slug, rarity)
            if floor and price < 0.8 * floor:
                player_name = o["card"]["player"]["displayName"]
                discount = int((1 - price / floor) * 100)
                msg = f"SPACCATONIO ALERT!\n{player_name} ({rarity})\nPrezzo: {price}€ (floor {floor}€ → -{discount}%)\nhttps://sorare.com/cards/{o['id']}"
                send_telegram(msg)
    except Exception as e:
        send_telegram(f"Errore bot: {str(e)}")

if __name__ == "__main__":
    main()
