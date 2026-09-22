#!/usr/bin/env python3
import os
import requests
from anthropic import Anthropic

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

STOCKS = {
    'GH': 'Guardant Health',
    'MPC': 'Marathon Petroleum',
    'CDNA': 'CareDx',
    'DK': 'Delek US',
    'ELF': 'E.l.f. Beauty',
    'PLTR': 'Palantir',
    'SCHD': 'Schwab Dividend',
    'SMR': 'Small Modular Reactor',
    '5141775': 'Harel Defense Index'
}

def get_stock_price(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            quote = data.get('quoteResponse', {}).get('result', [{}])[0]
            
            price = quote.get('regularMarketPrice', 'N/A')
            change_percent = quote.get('regularMarketChangePercent', 0)
            
            return {
                'price': price,
                'change_percent': change_percent,
                'success': True
            }
    except:
        pass
    
    return {'success': False}

def analyze_with_claude(stock_data):
    client = Anthropic()
    
    stocks_text = "\n".join([
        f"{symbol}: ${data['price']} ({data['change_percent']:+.1f}%)"
        for symbol, data in stock_data.items() if data['success']
    ])
    
    prompt = f"""Analyze these stocks in ONE line each. Format: [SYMBOL]: [ACTION: BUY/HOLD/WATCH] | [1 insight]

{stocks_text}

Be concise."""
    
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        requests.post(url, data=data, timeout=10)
        return True
    except:
        return False

def main():
    print("📊 Fetching stock prices...")
    
    stock_data = {}
    for symbol in STOCKS.keys():
        data = get_stock_price(symbol)
        if data['success']:
            stock_data[symbol] = data
    
    print(f"🤖 Analyzing {len(stock_data)} stocks...")
    analysis = analyze_with_claude(stock_data)
    
    message = f"<b>📊 Stock Update</b>\n\n{analysis}"
    
    print("📤 Sending to Telegram...")
    send_telegram_message(message)
    print("✓ Done!")

if __name__ == "__main__":
    main()
