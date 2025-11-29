import requests
import os
from datetime import datetime, timedelta

def send(message):
    try:
        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
                      json={"chat_id": os.environ['TELEGRAM_CHAT_ID'], "text": message, "disable_web_page_preview": True}, timeout=10)
    except:
        pass

def get_floor(player_slug, rarity):
    url = "https://api.sorare.com/graphql"
    query = """
    query ($slug: String!, $rarity: Rarity!) {
      player(slug: $slug) {
        cards(rarities: [$rarity], first: 5) {
          nodes {
            tokenAuction { currentAsk(currency: EUR) }
            singleSaleOffer { price(currency: EUR) }
          }
        }
      }
    }
    """
    variables = {"slug": player_slug, "rarity": rarity.upper()}
    r = requests.post(url, json={"query": query, "variables": variables})
    data = r.json().get("data", {}).get("player", {}).get("cards", {}).get("nodes", [])
    prices = [node["tokenAuction"]["currentAsk"] if node["tokenAuction"] else node["singleSaleOffer"]["price"] if node["singleSaleOffer"] else None for node in data]
    prices = [p for p in prices if p]
    return min(prices) if prices else None

def main():
    send("Spaccatonio test 1-100€ ≤100% floor – scan attivo")
    
    url = "https://api.sorare.com/graphql"
    now = datetime.utcnow()
    start = (now - timedelta(minutes=15)).isoformat()
    
    query = """
    query ($start: DateTime!) {
      transferMarket {
        auctions(first: 20, where: {rarity_in: [LIMITED, RARE], createdAt_gte: $start}) {
          nodes {
            id currentPrice(currency: EUR) endAt
            card { rarity player { displayName slug } }
          }
        }
        singleSaleOffers(first: 20, where: {rarity_in: [LIMITED, RARE], price_gte: 1, price_lte: 100, createdAt_gte: $start}) {
          nodes {
            id price(currency: EUR)
            card { rarity player { displayName slug } }
          }
        }
      }
    }
    """
    variables = {"start": start}
    r = requests.post(url, json={"query": query, "variables": variables})
    data = r.json().get("data", {}).get("transferMarket", {})
    
    auctions = data.get("auctions", {}).get("nodes", [])
    offers = data.get("singleSaleOffers", {}).get("nodes", [])
    
    # Aste in scadenza
    for a in auctions:
        end_time = datetime.fromisoformat(a["endAt"].replace('Z', '+00:00'))
        remaining = (end_time - now).total_seconds()
        price = a["currentPrice"]
        player_slug = a["card"]["player"]["slug"]
        rarity = a["card"]["rarity"].upper()
        floor = get_floor(player_slug, rarity)
        if remaining < 300 and 1 <= price <= 100 and floor and price <= floor:
            discount = int((floor - price) / floor * 100) if floor > 0 else 0
            msg = f"ASTA SCADENZA! {a['card']['player']['displayName']} ({rarity}) {price}€ (floor {floor}€ -{discount}%, {remaining:.0f}s)\nhttps://sorare.com/cards/{a['id']}"
            send(msg)
    
    # Buy Now
    for o in offers:
        price = o["price"]
        player_slug = o["card"]["player"]["slug"]
        rarity = o["card"]["rarity"].upper()
        floor = get_floor(player_slug, rarity)
        if floor and price <= floor:
            discount = int((floor - price) / floor * 100) if floor > 0 else 0
            msg = f"BUY NOW! {o['card']['player']['displayName']} ({rarity}) {price}€ (floor {floor}€ -{discount}%)\nhttps://sorare.com/cards/{o['id']}"
            send(msg)
    
    send("Scan aste + Buy Now completato – prossimo tra 5 min")

if __name__ == "__main__":
    main()
