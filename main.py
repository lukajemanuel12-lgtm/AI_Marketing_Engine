import os
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
import uvicorn

# 1. KONFIGURIMI I SERVERIT
app = FastAPI(title="BiznesBoost AI Backend")

# Lejojmë Lovable të komunikojë me kompjuterin tënd
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Vendos API Key-in tënd këtu
client = Groq(api_key=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")
MODEL_AI = "llama-3.3-70b-versatile"

# 2. STRUKTURA E TË DHËNAVE (Sipas Onboarding në Foto 437-439)
class BiznesInfo(BaseModel):
    emri: str
    kategoria: str
    adresa: str
    telefoni: str
    toni: str  # psh. Profesional, Miqësor

class ChatRequest(BaseModel):
    message: str
    biz_data: BiznesInfo

# 3. MOTORI I VIDEOS (Sipas Foto 446)
@app.post("/generate-video-plan")
async def generate_video(request: Request):
    data = await request.json()
    prompt = f"""
    Krijo një plan fushate virale për {data['biz_name']}. 
    Kategoria: {data['category']}. Toni: {data['tone']}.
    Videoja duhet të zgjasë 15 sekonda.
    Ndaje në 3 skena:
    1. Hook (Skena 1): 5 sekonda me zoom-in.
    2. Value (Skena 2): 5 sekonda fokus te produkti.
    3. CTA (Skena 3): 5 sekonda me detajet e kontaktit.
    Ktheje vetëm si JSON STRICT.
    """
    
    completion = client.chat.completions.create(
        model=MODEL_AI,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(completion.choices[0].message.content)

# 4. CHATBOTI DHE REZERVIMET (Sipas Foto 449 & 445)
@app.post("/chat-assistant")
async def chat_assistant(request: ChatRequest):
    # Këtu AI mëson gjithçka për biznesin tënd nga hapat e Onboarding
    instruksionet = f"""
    Ti je menaxheri virtual i {request.biz_data.emri}.
    Lloji i biznesit: {request.biz_data.kategoria}.
    Adresa: {request.biz_data.adresa}. 
    Toni i bisedës: {request.biz_data.toni}.
    
    Rregullat:
    - Nëse klienti pyet për menu, shpik pjata që i përshtaten kategorisë {request.biz_data.kategoria}.
    - Nëse klienti kërkon rezervim, thuaj: "Patjetër! Për sa persona dhe në çfarë ore?"
    - Kur të japin orën, konfirmoje dhe thuaj që u regjistrua te seksioni 'Planifikimi'.
    - Përgjigju gjithmonë në SHQIP dhe shkurt.
    """

    chat_completion = client.chat.completions.create(
        model=MODEL_AI,
        messages=[
            {"role": "system", "content": instruksionet},
            {"role": "user", "content": request.message}
        ]
    )
    return {"reply": chat_completion.choices[0].message.content}

# 5. NISJA E SERVERIT
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
