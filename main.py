import requests
import os
from datetime import datetime, timedelta

def send(message):
    try:
        requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_TOKEN']}/sendMessage",
                      json={"chat_id": os.environ['TELEGRAM_CHAT_ID'], "text": message, "disable_web_page_preview": True}, timeout=10)
    except:
        pass

def main():
    send("SPACCATONIO ATTIVO – cerco deal Limited/Rare 3-30€ sotto 80% floor")
    
    url = "https://api.sorare.com/api/v1/cards"
    params = {
        "query": "rarity:limited OR rarity:rare price:3..30",
        "order_by": "created_at_desc",
        "page": 1
    }
    
    try:
        r = requests.get(url, params=params, timeout=15)
        cards = r.json().get("cards", [])
        
        for card in cards[:50]:  # primi 50 più recenti
            price = float(card["latest_offer"]["price_eur"])
            floor = float(card["player"]["floor_price_eur"] or 0)
            name = card["player"]["display_name"]
            rarity = card["rarity"].capitalize()
            uuid = card["uuid"]
            
            if floor > 0 and price < floor * 0.8 and 3 <= price <= 30:
                discount = int((floor - price) / floor * 100)
                msg = f"SPACCATONIO ALERT!\n{name} ({rarity})\n{price}€ (floor {floor}€ → -{discount}%)\nhttps://sorare.com/cards/{uuid}"
                send(msg)
                
        send("Scan completato – nessun altro deal trovato ora")
    except:
        send("Errore scan, riprovo fra 1 minuto")

if __name__ == "__main__":
    main()
