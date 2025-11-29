import requests
import os
from datetime import datetime, timedelta

def send_telegram(message):
    url = f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage"
    payload = {"chat_id": os.environ['TELEGRAM_CHAT_ID'], "text": message, "disable_web_page_preview": True}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def login_sorare():
    query = """mutation ($email: String!, $password: String!) { signIn(email: $email, password: $password) { jwt } }"""
    variables = {"email": os.environ['SORARE_EMAIL'], "password": os.environ['SORARE_PASSWORD']}
    r = requests.post("https://api.sorare.com/graphql", json={"query": query, "variables": variables}, timeout=10)
    return r.json()["data"]["signIn"]["jwt"]

def get_floor(jwt, player_slug, rarity):
    query = """query ($slug: String!, $rarity: String!) {
      player(slug: $slug) {
        activeEnglishAuctionCards(rarities: [$rarity]) {
          nodes { currentPrice(currency: EUR) }
        }
        singleSaleOfferCards(rarities: [$rarity]) {
          nodes { price(currency: EUR) }
        }
      }
    }"""
    headers = {"Authorization": f"Bearer {jwt}"}
    variables = {"slug": player_slug, "rarity": rarity}
    r = requests.post("https://api.sorare.com/graphql", json={"query": query, "variables": variables}, headers=headers, timeout=10)
    data = r.json().get("data", {}).get("player", {})
    prices = []
    for node in data.get("activeEnglishAuctionCards", {}).get("nodes", []):
        if node.get("currentPrice"): prices.append(node["currentPrice"])
    for node in data.get("singleSaleOfferCards", {}).get("nodes", []):
        if node.get("price"): prices.append(node["price"])
    return min(prices) if prices else None

def main():
    try:
        jwt = login_sorare()
        start_time = (datetime.utcnow() - timedelta(minutes=12)).strftime("%Y-%m-%dT%H:%M:%SZ")

        query = """query ($after: String, $time: DateTime!) {
          anyCards(first: 100, after: $after, where: {
            latestEnglishAuctionPrice_gte: 3,
            latestEnglishAuctionPrice_lte: 30,
            rarity_in: [limited, rare],
            latestEnglishAuctionCreatedAt_gte: $time
          }) {
            nodes {
              uuid rarity latestEnglishAuctionPrice(currency: EUR)
              player { displayName slug }
            }
            pageInfo { endCursor hasNextPage }
          }
        }"""
        headers = {"Authorization": f"Bearer {jwt}"}
        all_offers = []
        after = None
        while True:
            variables = {"time": start_time, "after": after}
            data = requests.post("https://api.sorare.com/graphql", json={"query": query, "variables": variables}, headers=headers, timeout=10).json()
            nodes = data["data"]["anyCards"]["nodes"]
            all_offers.extend(nodes)
            if not data["data"]["anyCards"]["pageInfo"]["hasNextPage"]:
                break
            after = data["data"]["anyCards"]["pageInfo"]["endCursor"]

        for card in all_offers:
            price = card["latestEnglishAuctionPrice"]
            player_slug = card["player"]["slug"]
            rarity = card["rarity"].capitalize()
            floor = get_floor(jwt, player_slug, rarity)
            if floor and price < 0.8 * floor:
                discount = int((1 - price / floor) * 100)
                msg = f"SPACCATONIO ALERT!\n{card['player']['displayName']} ({rarity})\nPrezzo: {price}€ (floor {floor}€ → -{discount}%)\nhttps://sorare.com/cards/{card['uuid']}"
                send_telegram(msg)

        # Messaggio di vita se non ci sono alert
        if not all_offers:
            send_telegram("Spaccatonio vivo e vegeto – nessun deal negli ultimi 12 min")

    except Exception as e:
        send_telegram(f"Errore Spaccatonio: {str(e)[:200]}")

if __name__ == "__main__":
    main()
