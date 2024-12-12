import os
import logging
import requests
from flask import Flask, jsonify, request, make_response
from flask_cors import CORS
from dotenv import load_dotenv
import traceback
import sys
from datetime import datetime

# Explicitly print out environment variables and current working directory
print("Current Working Directory:", os.getcwd())
print("Python Path:", sys.path)
print("Environment Variables:")
for key, value in os.environ.items():
    print(f"{key}: {value}")

# Load environment variables with more verbose logging
load_dotenv(verbose=True)
env_path = os.path.join(os.path.dirname(__file__), '.env')
print(f"Attempting to load .env from: {env_path}")
load_dotenv(dotenv_path=env_path)

# Configure more detailed logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler('crypto_tracker.log')  # Output to file
    ]
)
logger = logging.getLogger(__name__)

# CoinMarketCap API Configuration
CMC_API_KEY = os.getenv('CMC_API_KEY', '')
print(f"CMC_API_KEY from os.getenv(): '{CMC_API_KEY}'")

if not CMC_API_KEY or CMC_API_KEY == 'YOUR_COINMARKETCAP_API_KEY':
    # Try reading .env file directly as a fallback
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if line.startswith('CMC_API_KEY='):
                    CMC_API_KEY = line.split('=', 1)[1].strip()
                    print(f"CMC_API_KEY read directly from file: '{CMC_API_KEY}'")
                    break
    except Exception as e:
        print(f"Error reading .env file directly: {e}")

if not CMC_API_KEY or CMC_API_KEY == 'YOUR_COINMARKETCAP_API_KEY':
    logger.error("CRITICAL: No valid CoinMarketCap API key found!")
    raise ValueError("CoinMarketCap API key is missing or invalid. Please check your .env file.")

logger.info(f"Raw CMC_API_KEY from os.getenv(): '{CMC_API_KEY}'")
logger.info(f"CMC_API_KEY length: {len(CMC_API_KEY)}")
logger.info(f"CMC_API_KEY first 5 chars: '{CMC_API_KEY[:5]}'")

CMC_API_BASE_URL = 'https://pro-api.coinmarketcap.com/v1'

logger.info(f"CoinMarketCap API Key loaded: {bool(CMC_API_KEY)}")

# Default cryptocurrencies to track
DEFAULT_CRYPTOS = ['BTC', 'BCH', 'BSV', 'LTC', 'XRP', 'ETH', 'DOGE']
MAX_ADDITIONAL_CRYPTOS = 3
user_added_cryptos = set(DEFAULT_CRYPTOS)  # Start with default cryptos

def get_crypto_data(symbols):
    """Fetch data for specific cryptocurrencies"""
    logger.info(f"Attempting to fetch data for symbols: {symbols}")
    
    # Log full API key details for debugging
    logger.info(f"Full API Key: {CMC_API_KEY}")
    logger.info(f"API Key Length: {len(CMC_API_KEY)}")
    
    headers = {
        'X-CMC_PRO_API_KEY': CMC_API_KEY,
        'Accept': 'application/json'
    }
    
    try:
        # Convert list to comma-separated string
        symbol_string = ','.join(symbols)
        
        # Enhanced logging for request details
        logger.info(f"Request Headers: {headers}")
        logger.info(f"Request URL: {CMC_API_BASE_URL}/cryptocurrency/quotes/latest")
        logger.info(f"Request Params: symbol={symbol_string}, convert=USD")
        
        # Fetch cryptocurrency data
        response = requests.get(
            f'{CMC_API_BASE_URL}/cryptocurrency/quotes/latest',
            headers=headers,
            params={
                'symbol': symbol_string,
                'convert': 'USD'
            },
            timeout=10
        )
        
        # Log full response details
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Headers: {response.headers}")
        logger.info(f"Response Text: {response.text}")
        
        # Validate responses
        if response.status_code != 200:
            logger.error(f"API Error: {response.text}")
            return None
        
        quote_data = response.json().get('data', {})
        
        # Fetch cryptocurrency metadata for images
        metadata_response = requests.get(
            f'{CMC_API_BASE_URL}/cryptocurrency/info',
            headers=headers,
            params={
                'symbol': symbol_string
            },
            timeout=10
        )
        
        # Validate responses
        if metadata_response.status_code != 200:
            logger.error(f"API Error: {metadata_response.text}")
            return None
        
        metadata = metadata_response.json().get('data', {})
        
        cryptocurrencies = []
        
        for symbol in symbols:
            if symbol not in quote_data or symbol not in metadata:
                logger.warning(f"Symbol {symbol} not found in API response")
                continue
            
            crypto = quote_data[symbol]
            meta = metadata[symbol]
            
            cryptocurrencies.append({
                'id': crypto['id'],
                'name': crypto['name'],
                'symbol': crypto['symbol'],
                'price': crypto['quote']['USD']['price'],
                'percent_change_24h': crypto['quote']['USD']['percent_change_24h'],
                'percent_change_7d': crypto['quote']['USD']['percent_change_7d'],
                'market_cap': crypto['quote']['USD']['market_cap'],
                'is_default': symbol in DEFAULT_CRYPTOS,
                'logo': meta.get('logo', '')  # Add logo URL
            })
        
        logger.info(f"Successfully retrieved data for {len(cryptocurrencies)} cryptocurrencies")
        return cryptocurrencies
            
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        logger.error(traceback.format_exc())
        return None

app = Flask(__name__)

# Comprehensive CORS configuration
CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "OPTIONS", "HEAD"],
        "allow_headers": ["Content-Type", "Authorization", "Access-Control-Allow-Origin"]
    }
})

@app.route('/api/cryptocurrencies', methods=['GET', 'OPTIONS'])
def get_tracked_cryptocurrencies():
    """Get all tracked cryptocurrencies (default + user-added)"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response

    logger.info("Received request for tracked cryptocurrencies")
    
    # Ensure we always have some cryptocurrencies to track
    all_cryptos = list(user_added_cryptos) if user_added_cryptos else DEFAULT_CRYPTOS
    logger.info(f"Attempting to fetch data for cryptocurrencies: {all_cryptos}")
    
    try:
        crypto_data = get_crypto_data(all_cryptos)
        
        # Create response with CORS headers
        if crypto_data:
            response = make_response(jsonify(crypto_data))
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Content-Type", "application/json")
            return response
        
        # If get_crypto_data fails, return default cryptocurrencies with minimal data
        fallback_data = [
            {
                'symbol': symbol,
                'name': symbol,  # Placeholder name
                'price': 0,  # Placeholder price
                'percent_change_24h': 0,  # Placeholder change
                'market_cap': 0,  # Placeholder market cap
                'is_default': True
            }
            for symbol in DEFAULT_CRYPTOS
        ]
        
        logger.warning("Falling back to default cryptocurrencies with minimal data")
        response = make_response(jsonify(fallback_data))
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Content-Type", "application/json")
        return response
    
    except Exception as e:
        logger.error(f"Unexpected error in get_tracked_cryptocurrencies: {e}")
        logger.error(traceback.format_exc())
        
        # Fallback to default cryptocurrencies with minimal data
        fallback_data = [
            {
                'symbol': symbol,
                'name': symbol,  # Placeholder name
                'price': 0,  # Placeholder price
                'percent_change_24h': 0,  # Placeholder change
                'market_cap': 0,  # Placeholder market cap
                'is_default': True
            }
            for symbol in DEFAULT_CRYPTOS
        ]
        
        response = make_response(jsonify(fallback_data))
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Content-Type", "application/json")
        return response

@app.route('/api/cryptocurrency/search/<query>', methods=['GET'])
def search_cryptocurrencies(query):
    """Search for cryptocurrencies based on a query"""
    try:
        headers = {
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
            'Accept': 'application/json'
        }
        
        # Try searching by symbol first
        symbol_response = requests.get(
            f'{CMC_API_BASE_URL}/cryptocurrency/map',
            headers=headers,
            params={
                'symbol': query.upper(),
                'limit': 5
            },
            timeout=10
        )
        
        # If symbol search fails, try name search
        if symbol_response.status_code != 200:
            name_response = requests.get(
                f'{CMC_API_BASE_URL}/cryptocurrency/map',
                headers=headers,
                params={
                    'aux': 'platform',
                    'listing_status': 'active',
                    'name': query,
                    'limit': 5
                },
                timeout=10
            )
            response = name_response
        else:
            response = symbol_response
        
        if response.status_code != 200:
            logger.error(f"Search API Error: {response.text}")
            return jsonify({'error': 'Failed to search cryptocurrencies'}), 500
        
        data = response.json().get('data', [])
        
        # Extract unique search results
        search_results = []
        seen_symbols = set()
        for crypto in data:
            if crypto['symbol'] not in seen_symbols:
                search_results.append({
                    'symbol': crypto['symbol'],
                    'name': crypto['name']
                })
                seen_symbols.add(crypto['symbol'])
                
                # Limit to 5 results
                if len(search_results) >= 5:
                    break
        
        return jsonify(search_results)
    
    except Exception as e:
        logger.error(f"Search Cryptocurrency Error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/cryptocurrency/add/<symbol>', methods=['GET'])
def add_cryptocurrency(symbol):
    """Add a new cryptocurrency to the tracked list"""
    try:
        # Validate symbol
        symbol = symbol.upper().strip()
        
        # Check if already tracking this cryptocurrency
        if symbol in user_added_cryptos:
            return jsonify({'error': f'{symbol} is already being tracked'}), 400
        
        # Validate the cryptocurrency exists
        headers = {
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
            'Accept': 'application/json'
        }
        
        # First, check if the symbol exists
        map_response = requests.get(
            f'{CMC_API_BASE_URL}/cryptocurrency/map',
            headers=headers,
            params={
                'symbol': symbol,
                'limit': 1
            },
            timeout=10
        )
        
        if map_response.status_code != 200:
            logger.error(f"Cryptocurrency Map API Error: {map_response.text}")
            return jsonify({'error': 'Failed to validate cryptocurrency'}), 500
        
        map_data = map_response.json().get('data', [])
        if not map_data:
            return jsonify({'error': f'Cryptocurrency with symbol {symbol} not found'}), 404
        
        # Add to user-tracked cryptocurrencies
        user_added_cryptos.add(symbol)
        
        logger.info(f"Added cryptocurrency: {symbol}")
        logger.info(f"Current tracked cryptocurrencies: {user_added_cryptos}")
        
        return jsonify({
            'message': f'{symbol} added successfully',
            'tracked_cryptos': list(user_added_cryptos)
        })
    
    except Exception as e:
        logger.error(f"Add Cryptocurrency Error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/cryptocurrency/remove/<symbol>')
def remove_cryptocurrency(symbol):
    """Remove a cryptocurrency from tracking"""
    logger.info(f"Received request to remove cryptocurrency: {symbol}")
    symbol = symbol.upper()
    
    if symbol in DEFAULT_CRYPTOS:
        logger.error(f"Cannot remove default cryptocurrency: {symbol}")
        return jsonify({'error': 'Cannot remove default cryptocurrencies'}), 400
    
    if symbol in user_added_cryptos:
        user_added_cryptos.remove(symbol)
        logger.info(f"Removed {symbol} from tracked cryptocurrencies")
        return jsonify({'message': f'Removed {symbol} from tracked cryptocurrencies'})
    
    logger.error(f"Cryptocurrency not found in tracked list: {symbol}")
    return jsonify({'error': 'Cryptocurrency not found in tracked list'}), 404

@app.route('/api/ping', methods=['GET', 'OPTIONS'])
def ping():
    """Simple ping endpoint to verify server is running"""
    # Handle CORS preflight request
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response

    try:
        # Actual ping response
        response_data = {
            "status": "ok", 
            "message": "Server is running and accessible",
            "timestamp": datetime.now().isoformat(),
            "environment": {
                "python_version": sys.version,
                "debug_mode": app.debug
            }
        }
        
        response = make_response(jsonify(response_data))
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    
    except Exception as e:
        # Log the full error for server-side debugging
        logger.error(f"Ping endpoint error: {str(e)}")
        logger.error(traceback.format_exc())
        logger.error(f"Request data: {request.data}")  # Log request data for more context
        
        # Return a 500 error with a meaningful message
        return jsonify({
            "status": "error",
            "message": "Internal server error during ping",
            "error": str(e)
        }), 500

@app.route('/api/debug', methods=['GET'])
def debug_endpoint():
    """Provide comprehensive debugging information"""
    try:
        # Detailed API key logging
        env_api_key = os.getenv('CMC_API_KEY')
        logger.info(f"Environment API Key: {env_api_key}")
        logger.info(f"Global CMC_API_KEY: {CMC_API_KEY}")
        
        # Test API key and request
        headers = {
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
            'Accept': 'application/json'
        }
        
        response = requests.get(
            f'{CMC_API_BASE_URL}/cryptocurrency/quotes/latest',
            headers=headers,
            params={
                'symbol': 'BTC',
                'convert': 'USD'
            },
            timeout=10
        )
        
        return jsonify({
            'env_api_key': env_api_key,
            'global_api_key': CMC_API_KEY,
            'api_key_present': bool(CMC_API_KEY),
            'api_key_first_chars': CMC_API_KEY[:5],
            'default_cryptos': DEFAULT_CRYPTOS,
            'user_added_cryptos': list(user_added_cryptos),
            'api_response_status': response.status_code,
            'api_response_json': response.json() if response.status_code == 200 else 'Failed to parse response'
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
