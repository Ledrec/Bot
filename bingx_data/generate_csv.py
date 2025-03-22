import requests
import time
import hmac
import hashlib
from operator import itemgetter
import csv
from datetime import datetime

# BingX API base URL
API_URL = "https://open-api.bingx.com"

# Your API credentials (you’ll need to get these from BingX)
API_KEY = "U2HriBdK39ia5WHNdywJ5qG0bqeBsH267nMdPRNwdqGcbLE4d7uvvZF8XfYaew2gJAd0u3EdNBaIXnWDCMPw"  # Replace with your actual API key
SECRET_KEY = "YOUdH9COPvtvAo1EhYlLbD61tp9glWgfuVVRcX10CZw9D0dbJUYHDgh6e7Lq4kibIX6PupPlMOcnMMgVgMew"  # Replace with your actual secret key

# Function to generate the signature required by BingX API
def generate_signature(secret_key, params):
    query_string = "&".join([f"{key}={value}" for key, value in sorted(params.items())])
    return hmac.new(
        secret_key.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

# Function to get futures trading pairs with 24h change and save to CSV
def get_futures_trading_pairs_to_csv():
    endpoint = "/openApi/swap/v2/quote/ticker"
    url = f"{API_URL}{endpoint}"
    
    params = {
        "timestamp": int(time.time() * 1000)
    }
    
    signature = generate_signature(SECRET_KEY, params)
    params["signature"] = signature
    
    headers = {
        "X-BX-APIKEY": API_KEY
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('code') == 0:
            symbols_data = data['data']
            trading_pairs = []
            
            for symbol in symbols_data:
                last_price = float(symbol['lastPrice'])
                open_price = float(symbol['openPrice'])
                change_value = ((last_price - open_price) / open_price) * 100 if open_price != 0 else 0
                
                pair_info = {
                    'symbol': symbol['symbol'],
                    'change': change_value
                }
                trading_pairs.append(pair_info)
            
            # Sort by 24h change (descending) and take top 10
            trading_pairs.sort(key=itemgetter('change'), reverse=True)
            top_10_pairs = trading_pairs[:10]
            
            # Get current date for CSV
            current_date = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Write to CSV file
            csv_filename = 'bingx_top_10_futures_changes.csv'
            with open(csv_filename, 'w', newline='') as csvfile:
                fieldnames = ['date', 'symbol', 'value']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for pair in top_10_pairs:
                    writer.writerow({
                        'date': current_date,
                        'symbol': pair['symbol'],
                        'value': round(pair['change'], 2)
                    })
            
            print(f"Successfully saved top 10 futures pairs to '{csv_filename}'")
            return top_10_pairs
        else:
            print(f"API error: {data.get('msg', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

# Run the script
if __name__ == "__main__":
    top_pairs = get_futures_trading_pairs_to_csv()
    if top_pairs:
        print("Top 10 futures trading pairs by 24h change:")
        for pair in top_pairs:
            print(f"{pair['symbol']}: {pair['change']:.2f}%")
