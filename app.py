import streamlit as st
from PIL import Image
import os
from llm import call_crop_doctor, is_gemini_configured, transcribe_audio, text_to_speech

# ----------------------------------------
# Configuration & Setup
# ----------------------------------------
st.set_page_config(
    page_title="Kisan Mitra: AI Crop Doctor",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a professional look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E7D32;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #555;
        text-align: center;
        margin-bottom: 2rem;
    }
    .result-card {
        background-color: #f1f8e9;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #4CAF50;
        margin-top: 20px;
    }
    .result-key {
        font-weight: 600;
        color: #33691E;
    }
    .warning-card {
        background-color: #fff3e0;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #ff9800;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------
# Header Section
# ----------------------------------------
st.markdown('<div class="main-header">🌱 Kisan Mitra (किसान मित्र)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI Crop Doctor for Fast, Reliable Diagnosis</div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Configuration")
    if is_gemini_configured():
        st.success("✅ Round-Robin API Keys configured! (Live Inference Enabled)")
    else:
        st.info("Running in Mock Mode. No API keys found.")

# ----------------------------------------
# Main Input Section
# ----------------------------------------
st.write("### 1. Upload Crop Image")
uploaded_file = st.file_uploader("Take a photo or upload an image of the affected plant.", type=["jpg", "jpeg", "png"])

col1, col2 = st.columns(2)
with col1:
    location = st.text_input("District / Location", value="Prayagraj", help="Used to fetch local weather and mandi prices.")
with col2:
    crop_name = st.text_input("Crop Name", value="Wheat", help="e.g., Wheat, Tomato, Rice")

st.write("### 2. Describe the Issue (Text or Voice)")
voice_input = None
try:
    voice_input = st.audio_input("Record Voice Description (Optional)")
except AttributeError:
    st.info("Please update Streamlit to >=1.36 for native voice recording.")

description = st.text_area("Optional: Type your description (हिंदी या English)", placeholder="e.g., पत्तियां पीली पड़ रही हैं / Leaves are turning yellow")

# ----------------------------------------
# Processing & Results Section
# ----------------------------------------
if st.button("🔍 Diagnose Plant (रोग का निदान करें)", type="primary", use_container_width=True):
    if uploaded_file is None:
        st.error("Please upload an image first.")
    else:
        # Display the uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Crop Image", use_container_width=True)
        
        with st.spinner("Analyzing image, fetching weather, and generating diagnosis..."):
            
            # 1. Process Voice if available
            final_description = description
            if voice_input is not None:
                st.toast("Transcribing voice input...")
                transcript = transcribe_audio(voice_input.getvalue())
                if transcript and "failed" not in transcript.lower():
                    final_description = f"{description} [Voice]: {transcript}"
            
            # 2. Call the AI Doctor
            result = call_crop_doctor(
                image=image, 
                description=final_description, 
                location=location,
                crop=crop_name
            )
            
            if "error" in result:
                st.error(f"Error during analysis: {result['error']}")
            else:
                # 3. Generate Audio for the result
                st.toast("Generating Voice Diagnosis...")
                hindi_script = f"रोग का नाम है {result.get('disease', 'अज्ञात')}। {result.get('immediate_treatment', '')}। {result.get('chemical_fallback', '')}। {result.get('urgency', '')}"
                audio_bytes = text_to_speech(hindi_script)
                
                # Render the Results Card
                st.markdown("### Diagnosis Results (निदान परिणाम)")
                
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/wav")
                
                st.markdown(f"""
                <div class="result-card">
                    <p><span class="result-key">🦠 Disease (रोग):</span> {result.get('disease', 'N/A')}</p>
                    <p><span class="result-key">📊 Confidence (सटीकता):</span> {result.get('confidence', 'N/A')}</p>
                    <hr>
                    <p><span class="result-key">🌿 Immediate Step (तत्काल उपाय):</span><br/> {result.get('immediate_treatment', 'N/A')}</p>
                    <p><span class="result-key">🧪 Chemical Fallback (रासायनिक उपचार):</span><br/> {result.get('chemical_fallback', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Render the Urgency/Weather Card
                st.markdown(f"""
                <div class="warning-card">
                    <p><span style="color: #e65100; font-weight: bold;">⚠️ Urgency Context (मौसम और मंडी की जानकारी):</span><br/> 
                    {result.get('urgency', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Disclaimer (Responsible AI)
                st.caption("Note: This diagnosis is AI-generated. For low confidence cases, please consult your local Krishi Vigyan Kendra (KVK).")
