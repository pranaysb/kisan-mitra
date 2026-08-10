import requests
import json
from typing import Dict, Any
from itertools import cycle

class RoundRobinKeyManager:
    def __init__(self, keys):
        valid_keys = [k.strip() for k in keys if k.strip()]
        self.keys = valid_keys
        self.key_cycle = cycle(self.keys) if self.keys else None

    def get_next_key(self):
        return next(self.key_cycle) if self.key_cycle else None

TAVILY_KEYS = [
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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",
    "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"
]
tavily_key_manager = RoundRobinKeyManager(TAVILY_KEYS)

def search_tavily(query: str) -> str:
    """Searches the live web using Tavily API for fact-checked agricultural context."""
    api_key = tavily_key_manager.get_next_key()
    if not api_key:
        return "Tavily Search not configured."
        
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "search_depth": "basic",
                "include_answer": True
            }
        )
        response.raise_for_status()
        data = response.json()
        return data.get("answer", "No direct answer found, but results were retrieved.")
    except Exception as e:
        return f"Live search failed: {str(e)}"

def get_weather(location: str) -> str:
    """
    Fetches the current weather and 3-day forecast for a given location in Uttar Pradesh.
    Uses Open-Meteo API (free, no auth required).
    
    Args:
        location: The district or city name (e.g., "Prayagraj", "Varanasi").
        
    Returns:
        A string describing the weather, temperature, and any upcoming rain.
    """
    # Simple geocoding dictionary for common UP districts for the hackathon
    # In a real app, we'd use the Open-Meteo Geocoding API
    coordinates = {
        "prayagraj": {"lat": 25.4358, "lon": 81.8463},
        "allahabad": {"lat": 25.4358, "lon": 81.8463},
        "varanasi": {"lat": 25.3176, "lon": 82.9739},
        "lucknow": {"lat": 26.8467, "lon": 80.9462},
        "kanpur": {"lat": 26.4499, "lon": 80.3319},
        "default": {"lat": 26.8467, "lon": 80.9462} # Default to Lucknow
    }
    
    loc_key = location.lower().strip()
    coords = coordinates.get(loc_key, coordinates["default"])
    
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=temperature_2m,relative_humidity_2m,precipitation,rain&daily=precipitation_sum,rain_sum&timezone=Asia%2FKolkata&forecast_days=3"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        current_temp = data["current"]["temperature_2m"]
        current_humidity = data["current"]["relative_humidity_2m"]
        
        # Check for upcoming rain in the next 3 days
        daily_rain = data["daily"]["rain_sum"]
        will_rain = any(rain > 5.0 for rain in daily_rain) # if any day has > 5mm rain
        
        forecast = f"Current temperature is {current_temp}°C with {current_humidity}% humidity in {location.title()}."
        if will_rain:
            forecast += " Heavy rain is expected in the next 3 days. High risk for fungal disease spread."
        else:
            forecast += " No significant rain expected in the next 3 days. Dry conditions."
            
        return forecast
    except Exception as e:
        return f"Could not fetch weather for {location}: {str(e)}"

def get_mandi_price(crop: str, location: str) -> str:
    """
    Fetches the current Mandi (market) price for a specific crop in a given location.
    Now attempts to use live Tavily search to prevent hallucinations, falling back to mock data if it fails.
    """
    # 1. Try Live Search First
    live_query = f"Current mandi price for {crop} in {location} UP 2024"
    live_result = search_tavily(live_query)
    
    if "failed" not in live_result and "not configured" not in live_result:
         return f"[LIVE WEB DATA] {live_result}"
         
    # 2. Fallback to mock data if search fails or is unconfigured
    mock_data = {
        "wheat": {"prayagraj": 2275, "varanasi": 2300, "lucknow": 2250},
        "rice": {"prayagraj": 2900, "varanasi": 2950, "lucknow": 2850},
        "tomato": {"prayagraj": 1500, "varanasi": 1600, "lucknow": 1400},
        "potato": {"prayagraj": 1200, "varanasi": 1250, "lucknow": 1150},
        "sugarcane": {"prayagraj": 340, "varanasi": 340, "lucknow": 340}
    }
    
    crop_key = crop.lower().strip()
    loc_key = location.lower().strip()
    
    crop_prices = mock_data.get(crop_key, {})
    price = crop_prices.get(loc_key)
    
    if price is None:
        price = sum(crop_prices.values()) // len(crop_prices) if crop_prices else 2000
            
    return f"[MOCK FALLBACK] The current mandi price for {crop.title()} in {location.title()} is approximately ₹{price} per quintal."

# Tools dictionary for easy access in the LLM loop
AVAILABLE_TOOLS = {
    "get_weather": get_weather,
    "get_mandi_price": get_mandi_price
}

# Define the tools for Gemini API format (for later use when keys are provided)
gemini_tools = [
    {
        "function_declarations": [
            {
                "name": "get_weather",
                "description": "Fetches the current weather and 3-day forecast for a given location in Uttar Pradesh.",
                "parameters": {
                    "type_": "OBJECT",
                    "properties": {
                        "location": {
                            "type_": "STRING",
                            "description": "The district or city name (e.g., Prayagraj, Varanasi)."
                        }
                    },
                    "required": ["location"]
                }
            },
            {
                "name": "get_mandi_price",
                "description": "Fetches the current Mandi (market) price for a specific crop in a given location.",
                "parameters": {
                    "type_": "OBJECT",
                    "properties": {
                        "crop": {
                            "type_": "STRING",
                            "description": "The name of the crop (e.g., Wheat, Tomato)."
                        },
                        "location": {
                            "type_": "STRING",
                            "description": "The district or city name."
                        }
                    },
                    "required": ["crop", "location"]
                }
            }
        ]
    }
]
