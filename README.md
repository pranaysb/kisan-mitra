<div align="center">
  <h1>🌾 Kisan Mitra Backend</h1>
  <h3>The AI Engine for Indian Agriculture</h3>
  <p><i>Winner/Submission for the Build with Gemma: TFUG Prayagraj Hackathon</i></p>

  <p>
    <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi" alt="FastAPI"></a>
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
    <a href="https://ai.google.dev/gemma"><img src="https://img.shields.io/badge/Model-Gemma_4-F4B400?style=for-the-badge&logo=google" alt="Gemma 4"></a>
  </p>
</div>

---

This is the orchestration and intelligence layer for **Kisan Mitra**, built during a 1-day sprint for the AI Prayagraj hackathon. It exposes a robust REST API that leverages Google's **Gemma 4** open models (and Gemini Flash for vision tasks) alongside localized voice models to deliver real-time agricultural intelligence.

The frontend application can be found [here](https://github.com/pranaysb/kisan-mitra-web).

## 🧠 System Architecture

Instead of rigid rule-based logic, this backend operates as an orchestration layer. It receives multimodal inputs (Images + Hindi Voice Audio), transcribes the audio, and routes highly-engineered prompts to specialized **Gemma 4** Agents to enforce structured JSON outputs.

- **Audio Pipeline:** Transcribes raw `.wav` voice notes from Hindi/English to text using Sarvam AI.
- **Vision Pipeline:** Processes crop images using `gemini-1.5-flash` for native multimodal pathogen diagnosis.
- **Reasoning Pipeline:** Uses `gemma-2-27b-it` (via API) to compute complex subsidy matching, weather advisories, and APMC market trends.
- **TTS Pipeline:** Converts the AI's final JSON response into a synthesized spoken Hindi audio file for the frontend.

## 🚀 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/diagnose` | POST | Accepts `image` & `audio`. Returns disease identification and treatment. |
| `/yojana` | POST | Accepts farmer profile (`state`, `crop`, `land_size`, `audio`). Returns matching subsidies. |
| `/mandi` | POST | Accepts location data & `audio`. Returns simulated APMC market prices and sell/hold advice. |
| `/weather` | POST | Accepts location data & `audio`. Returns weather forecasts and crop-specific advisories. |

## ⚙️ Quick Start

### Prerequisites
- Python 3.9+
- API Keys for Google Gemini and Sarvam AI

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pranaysb/kisan-mitra.git
   cd kisan-mitra
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   The backend uses a Round-Robin key manager to handle rate limits. Export your keys as comma-separated strings:
   ```bash
   export GEMINI_API_KEYS="your_gemma_api_key_1,your_gemma_api_key_2"
   export SARVAM_API_KEYS="your_sarvam_api_key"
   ```

5. **Run the Server:**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## 🤝 Acknowledgments
Built with ❤️ during the Build with Gemma Hackathon 2026. Special thanks to the Google DeepMind team for providing access to the highly capable Gemma models!
