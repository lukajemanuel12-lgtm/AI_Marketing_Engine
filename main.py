from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import httpx
import uuid
from datetime import datetime, timedelta

app = FastAPI()

# --- 1. SETUP DHE KONFIGURIME ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Këtu ruhet gjithçka (Database në Memorie)
state = {
    "reservations": [],
    "waitlist": [],
    "settings": {
        "business_name": "BiznesBoost Elite",
        "business_type": "Lounge Bar",  # Opsione: Restorant, Club, Familjar
        "capacity": 5,                  # Numri i tavolinave
        "kafe_min": 45,                 # Koha për kafe
        "dreke_min": 90,                # Koha për drekë
        "darke_min": 120,               # Koha për darkë
        "buffer_min": 15                # Koha e pastrimit (Buffer Time)
    }
}

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# --- 2. TRURI INTELIGJENT (AI CHAT) ---
@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    
    # Personalizimi i AI sipas biznesit
    b_type = state["settings"]["business_type"]
    b_name = state["settings"]["business_name"]
    
    style_prompt = ""
    if b_type == "Lounge Bar":
        style_prompt = "Ji modern, 'cool', përdor emoji 🍸, fol për muzikë chill dhe kokteje."
    elif b_type == "Night Club":
        style_prompt = "Ji energjik, 'hype', fol për DJ, tavolina VIP dhe festë 🔥."
    else: # Restorant Familjar
        style_prompt = "Ji shumë i edukuar, mikpritës, tradicional dhe i ngrohtë 🍽️."

    system_prompt = f"""
    Ti je Menaxheri Digjital i '{b_name}'. Lloji: {b_type}.
    Stili yt i të folurit: {style_prompt}
    
    RREGULLAT KRITIKE:
    1. Nëse klienti do rezervim: Pyet për Datën, Orën, Personat dhe Qëllimin (Kafe/Drekë/Darkë).
    2. Nëse klienti thotë "Anulo": Thuaji 'Po e verifikoj dhe e anulo menjëherë'. (Backend-i e bën këtë te paneli).
    3. Mos premto tavolina nëse nuk i ke konfirmuar.
    """

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7
            }
        )
    return response.json()

# --- 3. SISTEMI I REZERVIMIT DHE WAITLIST ---
@app.post("/reserve")
async def make_reservation(request: Request):
    data = await request.json()
    visit_type = data.get("type", "kafe").lower()
    
    # Kontrolli i Kapacitetit
    if len(state["reservations"]) >= state["settings"]["capacity"]:
        return JSONResponse(content={
            "status": "full", 
            "message": "Jemi plot! A dëshironi t'ju fus në Listën e Pritjes Inteligjente?"
        })

    # Llogaritja e Kohës (Duration + Buffer)
    duration = state["settings"].get(f"{visit_type}_min", 60)
    buffer = state["settings"].get("buffer_min", 15)
    
    now = datetime.now()
    end_time = now + timedelta(minutes=duration)       # Kur ikën klienti
    ready_time = end_time + timedelta(minutes=buffer)  # Kur tavolina është gati (pas pastrimit)
    
    ticket_code = str(uuid.uuid4())[:6].upper() # Kod unik psh: #AF32D1
    
    new_res = {
        "id": ticket_code,
        "customer": data.get("name", "Klient"),
        "date": data.get("date"),
        "time": data.get("time"),
        "people": data.get("people"),
        "type": visit_type,
        "ends_at": end_time.strftime("%H:%M"),
        "ready_at": ready_time.strftime("%H:%M"),
        "ticket": ticket_code
    }
    state["reservations"].append(new_res)
    return {"status": "success", "ticket": ticket_code}

@app.post("/join_waitlist")
async def join_waitlist(request: Request):
    data = await request.json()
    state["waitlist"].append({
        "customer": data.get("name", "Anonim"),
        "time": datetime.now().strftime("%H:%M")
    })
    return {"status": "joined", "message": "Jeni në pritje. Do t'ju njoftojmë!"}

# --- 4. PANELI I PRONARIT (DASHBOARD) ---
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel():
    settings = state["settings"]
    
    # Gjenerimi i tabelës së rezervimeve
    res_rows = ""
    for r in state["reservations"]:
        res_rows += f"""
        <tr style="border-bottom:1px solid #eee;">
            <td style="padding:10px;"><b>{r['customer']}</b></td>
            <td style="padding:10px;">{r['time']}</td>
            <td style="padding:10px;">
                <span style="color:green;">Ikën: {r['ends_at']}</span><br>
                <span style="color:gray; font-size:0.8em;">Gati: {r['ready_at']}</span>
            </td>
            <td style="padding:10px;"><span style="background:#e3f2fd; color:#1565c0; padding:4px 8px; border-radius:4px;">#{r['ticket']}</span></td>
            <td style="padding:10px;"><a href='/delete/{r['id']}' style="color:red; text-decoration:none; font-weight:bold;">Liro Tavolinën</a></td>
        </tr>
        """
        
    wait_rows = "".join([f"<li>{w['customer']} (Pret nga ora {w['time']}) <button>Njofto</button></li>" for w in state["waitlist"]])

    html = f"""
    <html>
    <head>
        <title>Paneli i Menaxhimit</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: -apple-system, sans-serif; background: #f4f6f8; margin: 0; padding: 20px; }}
            .container {{ max-width: 900px; margin: 0 auto; }}
            .card {{ background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
            h2 {{ margin-top: 0; color: #333; }}
            label {{ font-weight: 600; display: block; margin-top: 10px; color: #555; }}
            input, select {{ width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ddd; border-radius: 8px; }}
            button {{ background: #222; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; margin-top: 15px; width: 100%; font-size: 16px; }}
            button:hover {{ background: #000; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ text-align: left; color: #888; padding: 10px; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <h2>⚙️ Konfigurimi i Biznesit</h2>
                <form action="/update_settings" method="post">
                    <label>Emri i Lokal: <input type="text" name="b_name" value="{settings['business_name']}"></label>
                    <label>Lloji (AI Stili): 
                        <select name="b_type">
                            <option value="Lounge Bar" {'selected' if settings['business_type']=='Lounge Bar' else ''}>Lounge Bar</option>
                            <option value="Restorant Familjar" {'selected' if settings['business_type']=='Restorant Familjar' else ''}>Restorant Familjar</option>
                            <option value="Night Club" {'selected' if settings['business_type']=='Night Club' else ''}>Night Club</option>
                        </select>
                    </label>
                    <div style="display:flex; gap:10px;">
                        <div style="flex:1;"><label>Kapaciteti: <input type="number" name="cap" value="{settings['capacity']}"></label></div>
                        <div style="flex:1;"><label>Koha e Pastrimit (min): <input type="number" name="buf" value="{settings['buffer_min']}"></label></div>
                    </div>
                    <button type="submit">Ruaj Ndryshimet</button>
                </form>
            </div>

            <div class="card">
                <h2>📅 Rezervimet Aktive ({len(state["reservations"])})</h2>
                <table>
                    <tr><th>Klienti</th><th>Ora</th><th>Statusi (Mbaron/Gati)</th><th>Kuponi</th><th>Veprimi</th></tr>
                    {res_rows if res_rows else "<tr><td colspan='5' style='text-align:center; padding:20px; color:#999;'>Asnjë rezervim aktiv</td></tr>"}
                </table>
            </div>

            <div class="card" style="border-left: 5px solid #ff9800;">
                <h2>⏳ Lista e Pritjes Inteligjente</h2>
                <ul>{wait_rows if wait_rows else "<li style='color:#999;'>Askush në pritje</li>"}</ul>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.post("/update_settings")
async def update_settings(b_name: str=Form(...), b_type: str=Form(...), cap: int=Form(...), buf: int=Form(...)):
    state["settings"].update({"business_name": b_name, "business_type": b_type, "capacity": cap, "buffer_min": buf})
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/delete/{res_id}")
async def delete_reservation(res_id: str):
    state["reservations"] = [r for r in state["reservations"] if r['id'] != res_id]
    return RedirectResponse(url="/admin", status_code=303)
