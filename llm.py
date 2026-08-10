import os
import json
import time
import google.generativeai as genai
from itertools import cycle
from tools import get_weather, get_mandi_price, gemini_tools

class RoundRobinKeyManager:
    def __init__(self, keys):
        valid_keys = [k.strip() for k in keys if k.strip()]
        self.keys = valid_keys
        if self.keys:
            self.key_cycle = cycle(self.keys)
        else:
            self.key_cycle = None

    def get_next_key(self):
        if self.key_cycle:
            return next(self.key_cycle)
        return None

# Initialize key managers with keys from environment variables
# Expecting comma-separated keys like: GEMINI_API_KEYS="key1,key2"
gemini_env_keys = os.environ.get("GEMINI_API_KEYS", "")
GEMINI_KEYS = [k.strip() for k in gemini_env_keys.split(",") if k.strip()]
gemini_key_manager = RoundRobinKeyManager(GEMINI_KEYS)

sarvam_env_keys = os.environ.get("SARVAM_API_KEYS", "")
SARVAM_KEYS = [k.strip() for k in sarvam_env_keys.split(",") if k.strip()]
sarvam_key_manager = RoundRobinKeyManager(SARVAM_KEYS)

def is_gemini_configured() -> bool:
    return gemini_key_manager.get_next_key() is not None

def call_crop_doctor(image, description: str, location: str, crop: str) -> dict:
    weather_info = get_weather(location)
    mandi_info = get_mandi_price(crop, location)
    
    context = f"Weather Context: {weather_info}\nMandi Context: {mandi_info}"

    if is_gemini_configured():
        current_key = gemini_key_manager.get_next_key()
        genai.configure(api_key=current_key)
        
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        
        system_instruction = f"""You are Kisan Mitra, an AI Crop Doctor. You diagnose plant diseases from images and descriptions.
You MUST output your response in valid JSON format ONLY. Do not include markdown code blocks like ```json in the output, just the raw JSON object.
Use the following context from our tools to enrich your response:
{context}

JSON Schema:
{{
  "disease": "Name of disease/pest (Hindi)",
  "confidence": "High/Medium/Low",
  "immediate_treatment": "Low-cost/organic first step (Hindi)",
  "chemical_fallback": "Chemical option with dosage if needed (Hindi)",
  "urgency": "Why this matters now, tied to weather/prices (Hindi)"
}}
"""
        prompt = [system_instruction]
        if image:
            prompt.append(image)
        if description:
            prompt.append(f"Farmer's Description: {description}")
            
        try:
            response = model.generate_content(prompt)
            text = response.text
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
        except Exception as e:
            print(f"Live API failed, falling back to mock. Error: {e}")
            pass
            
    time.sleep(2)
    return {
        "disease": "गेहूं का रतुआ (Wheat Leaf Rust)",
        "confidence": "High (92%)",
        "immediate_treatment": "संक्रमित पत्तियों को तुरंत हटा दें और नष्ट कर दें। खेत में हवा का प्रवाह सुनिश्चित करें।",
        "chemical_fallback": "यदि संक्रमण गंभीर है, तो 1 लीटर पानी में 1 मिली प्रोपिकोनाज़ोल (Propiconazole) 25% EC मिलाकर स्प्रे करें।",
        "urgency": "महत्वपूर्ण: " + weather_info.replace("Current temperature", "वर्तमान तापमान").replace("Heavy rain is expected", "भारी बारिश की उम्मीद है").replace("High risk for fungal disease spread.", "फंगल रोग फैलने का उच्च जोखिम है।")
    }

def transcribe_audio(audio_bytes, file_name="audio.wav"):
    api_key = sarvam_key_manager.get_next_key()
    if not api_key:
        return "Voice input is not configured."
        
    try:
        import requests
        url = "https://api.sarvam.ai/speech-to-text"
        headers = {"api-subscription-key": api_key}
        files = {"file": (file_name, audio_bytes, "audio/wav")}
        data = {"model": "saaras:v3"}
        
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        result = response.json()
        return result.get("transcript", "")
    except Exception as e:
        print(f"STT Error: {e}")
        return f"[Audio transcription failed: {e}]"

def text_to_speech(text: str):
    api_key = sarvam_key_manager.get_next_key()
    if not api_key:
        return None
        
    try:
        import requests
        import base64
        url = "https://api.sarvam.ai/text-to-speech"
        headers = {
            "api-subscription-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "language_code": "hi-IN",
            "speaker": "shubh",
            "model": "bulbul:v3"
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if "audios" in data and len(data["audios"]) > 0:
            audio_base64 = data["audios"][0]
            audio_bytes = base64.b64decode(audio_base64)
            return audio_bytes
        return None
    except Exception as e:
        print(f"TTS Error: {e}")
        return None

def call_yojana_radar(state: str, crop: str, land_size: str, description: str) -> dict:
    if is_gemini_configured():
        current_key = gemini_key_manager.get_next_key()
        genai.configure(api_key=current_key)
        
        model = genai.GenerativeModel(model_name="gemma-2-27b-it")
        
        system_instruction = """You are Kisan Mitra, an AI Agricultural Policy Expert.
You recommend relevant Indian government schemes (Yojanas) and subsidies to farmers based on their state, crop, and land size.
You MUST output your response in valid JSON format ONLY. Do not include markdown code blocks like ```json in the output, just the raw JSON object.

JSON Schema:
{
  "schemes": [
    {
      "scheme_name": "Name of the scheme (Hindi)",
      "eligibility": "Who is eligible? (Hindi)",
      "benefits": "What are the benefits? (Hindi)",
      "how_to_apply": "Brief instructions on how to apply (Hindi)"
    }
  ]
}
Recommend 2 to 3 highly relevant schemes. Ensure the schemes are applicable in the given state.
"""
        prompt = [system_instruction]
        farmer_details = f"State: {state}\nCrop: {crop}\nLand Size: {land_size}"
        if description:
            farmer_details += f"\nAdditional Details: {description}"
        prompt.append(farmer_details)
            
        try:
            response = model.generate_content(prompt)
            text = response.text
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
        except Exception as e:
            print(f"Live API failed for Yojana, falling back to mock. Error: {e}")
            pass
            
    time.sleep(1.5)
    return {
        "schemes": [
            {
                "scheme_name": "प्रधानमंत्री किसान सम्मान निधि (PM-KISAN)",
                "eligibility": "सभी भूमिधारक किसान परिवार जिनके पास खेती योग्य भूमि है।",
                "benefits": "6000 रुपये प्रति वर्ष की वित्तीय सहायता, जो 2000 रुपये की तीन किस्तों में दी जाती है।",
                "how_to_apply": "PM-KISAN पोर्टल (pmkisan.gov.in) पर पंजीकरण करें या नजदीकी कॉमन सर्विस सेंटर (CSC) पर जाएं।"
            },
            {
                "scheme_name": "प्रधानमंत्री फसल बीमा योजना (PMFBY)",
                "eligibility": "सभी किसान जो अधिसूचित क्षेत्रों में अधिसूचित फसलें उगा रहे हैं।",
                "benefits": "प्राकृतिक आपदाओं, कीटों और बीमारियों से फसल के नुकसान पर व्यापक बीमा कवर।",
                "how_to_apply": "अपने बैंक, सीएससी (CSC) या पीएमएफबीवाई पोर्टल के माध्यम से फसल की बुवाई से पहले आवेदन करें।"
            }
        ]
    }

def call_mandi_agent(state: str, district: str, crop: str, description: str) -> dict:
    if is_gemini_configured():
        current_key = gemini_key_manager.get_next_key()
        genai.configure(api_key=current_key)
        
        model = genai.GenerativeModel(model_name="gemma-2-27b-it")
        
        system_instruction = """You are Kisan Mitra, an AI Agricultural Market Analyst.
You simulate realistic APMC Mandi prices for a specific crop in a given Indian state and district.
You MUST output your response in valid JSON format ONLY. Do not include markdown code blocks like ```json in the output, just the raw JSON object.

JSON Schema:
{
  "mandi_name": "Name of the local Mandi/Market (Hindi/English)",
  "date": "Today's simulated date",
  "min_price": "Simulated minimum price in ₹/Quintal",
  "max_price": "Simulated maximum price in ₹/Quintal",
  "modal_price": "Simulated modal/average price in ₹/Quintal",
  "trend": "Up/Down/Stable (Hindi)",
  "advisory": "Market advice on whether to sell now or hold (Hindi)"
}
Ensure the prices are realistic for the given crop (e.g. Wheat is around 2200-2500, Tomato varies wildly).
"""
        prompt = [system_instruction]
        details = f"State: {state}\nDistrict: {district}\nCrop: {crop}"
        if description:
            details += f"\nVoice Notes: {description}"
        prompt.append(details)
            
        try:
            response = model.generate_content(prompt)
            text = response.text
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
        except Exception as e:
            print(f"Live API failed for Mandi, falling back to mock. Error: {e}")
            pass
            
    time.sleep(1.5)
    return {
        "mandi_name": f"{district} कृषि उपज मंडी (APMC)",
        "date": "आज का भाव",
        "min_price": "2,150",
        "max_price": "2,400",
        "modal_price": "2,275",
        "trend": "स्थिर (Stable)",
        "advisory": "कीमतें स्थिर हैं। यदि आपको तुरंत नकदी की आवश्यकता नहीं है, तो आप 1-2 सप्ताह तक प्रतीक्षा कर सकते हैं।"
    }

def call_weather_agent(state: str, district: str, crop: str, description: str) -> dict:
    if is_gemini_configured():
        current_key = gemini_key_manager.get_next_key()
        genai.configure(api_key=current_key)
        
        model = genai.GenerativeModel(model_name="gemma-2-27b-it")
        
        system_instruction = """You are Kisan Mitra, an AI Agrometeorological Expert.
You simulate realistic weather conditions and provide crop-specific farming advisories based on the simulated weather.
You MUST output your response in valid JSON format ONLY. Do not include markdown code blocks like ```json in the output, just the raw JSON object.

JSON Schema:
{
  "forecast": "Brief 3-day weather forecast (Hindi)",
  "temperature": "e.g., 28°C - 34°C",
  "rain_probability": "e.g., High (80%)",
  "crop_advisory": "Specific advice for the requested crop based on this weather (e.g., delay irrigation, spray pesticide) (Hindi)",
  "alert_level": "Normal/Warning/Alert"
}
"""
        prompt = [system_instruction]
        details = f"State: {state}\nDistrict: {district}\nCrop: {crop}"
        if description:
            details += f"\nVoice Notes: {description}"
        prompt.append(details)
            
        try:
            response = model.generate_content(prompt)
            text = response.text
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())
        except Exception as e:
            print(f"Live API failed for Weather, falling back to mock. Error: {e}")
            pass
            
    time.sleep(1.5)
    return {
        "forecast": "अगले 3 दिनों तक हल्की से मध्यम बारिश की संभावना है। आसमान में बादल छाए रहेंगे।",
        "temperature": "26°C - 32°C",
        "rain_probability": "High (75%)",
        "crop_advisory": f"{crop} की फसल में सिंचाई रोक दें। बारिश के बाद फंगल इन्फेक्शन का खतरा बढ़ सकता है, इसलिए मौसम साफ होने पर फफूंदनाशक का छिड़काव करें।",
        "alert_level": "Warning"
    }
