import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware

# 1. KONFIGURIMI I SERVERIT TË SHPEJTË
app = FastAPI(title="AI Marketing Engine Pro")

# 2. HAPJA E DYERVE PËR LOVABLE (Zgjidhja e problemit të lidhjes)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Lejon çdo lidhje
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. LIDHJA ME TRURIN E GROQ
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class ChatRequest(BaseModel):
    message: str
    biz_data: dict

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # 4. INTELIGJENCA E SHTUAR (Prompt Inxhinierik)
        # Kjo i jep AI-së rolin e ekspertit
        system_instruction = (
            "You are a world-class Marketing Strategist & Creative Director. "
            "Your goal is to provide high-ROI, viral, and actionable marketing advice. "
            "Analyze the user's business data deeply. Be concise, professional, and enthusiastic."
        )

        user_content = f"""
        BUSINESS CONTEXT: {request.biz_data}
        USER QUESTION: {request.message}
        
        Provide a strategic response tailored to this business.
        """

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", # Modeli më i shpejtë dhe i balancuar
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7,
            max_tokens=1024
        )
        
        return {"response": completion.choices[0].message.content}
    
    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Server Error: " + str(e))

@app.get("/")
async def root():
    return {"status": "Active", "message": "AI Marketing Engine is Live & Ready!"}
