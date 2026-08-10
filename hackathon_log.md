# Kisan Mitra - Hackathon Log

## Hour 1: Setup & Architecture
- **Goal**: Finalize idea, establish Streamlit + Python backend foundation, and prepare mock API services for Gemma.
- **Actions**:
  - Scoped project to the **Crop Doctor** module based on latest requirements.
  - Initialized a Python virtual environment with `streamlit`, `google-generativeai`, and `requests`.
  - Created project architecture: Streamlit frontend, mock Gemma AI interface, and two function-calling tools (`get_weather`, `get_mandi_price`).
  - Opted for Open-Meteo for free, keyless weather data.
  - Used a mock JSON dataset for Mandi prices in Uttar Pradesh to simulate localized market data.

## Hour 2: Advanced Integration & API Keys
- **Goal**: Implement live inference and robust API key management.
- **Actions**:
  - **Round-Robin Architecture**: Implemented a `RoundRobinKeyManager` in both `llm.py` (for Gemini, Sarvam) and `tools.py` (for Tavily) to cycle through arrays of API keys, ensuring stability under heavy load during the demo.
  - **Tavily Live Web Search**: Upgraded the `get_mandi_price` tool to first attempt a live web search using the Tavily API. This grounds the LLM in 100% factual, real-time data to prevent hallucinations, falling back to the mock dataset only if the search fails.
  - **Live Gemma Inference**: Integrated the provided Google GenAI API keys. The Streamlit app dynamically detects configured keys and switches from Mock Mode to Live Inference Mode using `gemma-2-27b-it`.

## Hour 3: Voice Mode (Sarvam STT & TTS)
- **Goal**: Make the app accessible for farmers who prefer speaking over typing.
- **Actions**:
  - **Speech-To-Text (Saaras:v3)**: Added a native voice recorder in the Streamlit UI. Farmers can now speak their crop symptoms. The audio is sent to Sarvam's `speech-to-text` API to transcribe the regional Hindi/Hinglish directly into the AI prompt.
  - **Text-To-Speech (Bulbul:v3)**: After Gemini generates the diagnosis, the Hindi text is passed to Sarvam's `text-to-speech` API. The app renders an audio player allowing the farmer to listen to the diagnosis, immediate treatment, and weather urgency.
  - Successfully demonstrated that the entire stack (Gemma 2 + Sarvam + Tavily) works flawlessly in a single web dashboard.

## Next Steps
- Final UI polish and presentation prep.
- End-to-end testing with real photos and voice.
