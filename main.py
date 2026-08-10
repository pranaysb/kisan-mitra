from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
from PIL import Image
import base64
from llm import call_crop_doctor, transcribe_audio, text_to_speech, call_yojana_radar, call_mandi_agent, call_weather_agent
import uvicorn

app = FastAPI(title="Kisan Mitra API")

# Allow CORS for local React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/diagnose")
async def diagnose_crop(
    image: UploadFile = File(...),
    location: str = Form(...),
    crop_name: str = Form(...),
    description: str = Form(None),
    audio: UploadFile = File(None)
):
    # 1. Read Image
    img_bytes = await image.read()
    img = Image.open(BytesIO(img_bytes))
    
    # 2. Process Audio if present
    final_description = description or ""
    if audio:
        audio_bytes = await audio.read()
        transcript = transcribe_audio(audio_bytes, audio.filename)
        if transcript and "failed" not in transcript.lower():
            final_description = f"{final_description} [Voice]: {transcript}"
            
    # 3. Call AI Doctor
    result = call_crop_doctor(
        image=img,
        description=final_description,
        location=location,
        crop=crop_name
    )
    
    # 4. Generate TTS
    if "error" not in result:
        hindi_script = f"रोग का नाम है {result.get('disease', 'अज्ञात')}। {result.get('immediate_treatment', '')}। {result.get('chemical_fallback', '')}। {result.get('urgency', '')}"
        audio_bytes = text_to_speech(hindi_script)
        if audio_bytes:
            result["audio_b64"] = base64.b64encode(audio_bytes).decode('utf-8')
            
    return result

@app.post("/yojana")
async def get_yojanas(
    state: str = Form(...),
    crop: str = Form(...),
    land_size: str = Form(...),
    description: str = Form(None),
    audio: UploadFile = File(None)
):
    # Process Audio if present
    final_description = description or ""
    if audio:
        audio_bytes = await audio.read()
        transcript = transcribe_audio(audio_bytes, audio.filename)
        if transcript and "failed" not in transcript.lower():
            final_description = f"{final_description} [Voice]: {transcript}"
            
    # Call AI Policy Expert
    result = call_yojana_radar(
        state=state,
        crop=crop,
        land_size=land_size,
        description=final_description
    )
    
    # Generate TTS summary for the top scheme
    if "schemes" in result and len(result["schemes"]) > 0:
        top_scheme = result["schemes"][0]
        hindi_script = f"आपके लिए सबसे उपयुक्त योजना है {top_scheme.get('scheme_name', '')}। लाभ: {top_scheme.get('benefits', '')}।"
        audio_bytes = text_to_speech(hindi_script)
        if audio_bytes:
            result["audio_b64"] = base64.b64encode(audio_bytes).decode('utf-8')
            
    return result

@app.post("/mandi")
async def get_mandi(
    state: str = Form(...),
    district: str = Form(...),
    crop: str = Form(...),
    description: str = Form(None),
    audio: UploadFile = File(None)
):
    # Process Audio if present
    final_description = description or ""
    if audio:
        audio_bytes = await audio.read()
        transcript = transcribe_audio(audio_bytes, audio.filename)
        if transcript and "failed" not in transcript.lower():
            final_description = f"{final_description} [Voice]: {transcript}"
            
    # Call AI Mandi Agent
    result = call_mandi_agent(
        state=state,
        district=district,
        crop=crop,
        description=final_description
    )
    
    # Generate TTS summary
    if "error" not in result:
        hindi_script = f"{result.get('mandi_name', 'मंडी')} में {crop} का औसत भाव {result.get('modal_price', '')} रुपये प्रति क्विंटल है। {result.get('advisory', '')}"
        audio_bytes = text_to_speech(hindi_script)
        if audio_bytes:
            result["audio_b64"] = base64.b64encode(audio_bytes).decode('utf-8')
            
    return result

@app.post("/weather")
async def get_weather_advisory(
    state: str = Form(...),
    district: str = Form(...),
    crop: str = Form(...),
    description: str = Form(None),
    audio: UploadFile = File(None)
):
    # Process Audio if present
    final_description = description or ""
    if audio:
        audio_bytes = await audio.read()
        transcript = transcribe_audio(audio_bytes, audio.filename)
        if transcript and "failed" not in transcript.lower():
            final_description = f"{final_description} [Voice]: {transcript}"
            
    # Call AI Weather Agent
    result = call_weather_agent(
        state=state,
        district=district,
        crop=crop,
        description=final_description
    )
    
    # Generate TTS summary
    if "error" not in result:
        hindi_script = f"मौसम का पूर्वानुमान: {result.get('forecast', '')} {crop} के लिए सलाह: {result.get('crop_advisory', '')}"
        audio_bytes = text_to_speech(hindi_script)
        if audio_bytes:
            result["audio_b64"] = base64.b64encode(audio_bytes).decode('utf-8')
            
    return result

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
