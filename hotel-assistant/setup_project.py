import os

# Ordnerstruktur erstellen
directories = ["app", "data", "knowledge", "snowflake"]
for d in directories:
    os.makedirs(d, exist_ok=True)

# 1. requirements.txt
with open("requirements.txt", "w", encoding="utf-8") as f:
    f.write("""groq
rank_bm25
fastapi
uvicorn[standard]
python-multipart
snowflake-connector-python
""")

# 2. .gitignore
with open(".gitignore", "w", encoding="utf-8") as f:
    f.write("""venv/
__pycache__/
*.pyc
.env
data/call_logs/
""")

# 3. README.md
with open("README.md", "w", encoding="utf-8") as f:
    f.write("""# Hotel Sonnenhof - AI Phone Assistant
Deutscher KI-Telefonassistent basierend auf FastAPI, Groq LLM und Twilio Webhooks (<Gather>).
""")

# 4. app/__init__.py
with open("app/__init__.py", "w", encoding="utf-8") as f:
    f.write("# Marks app as a Python package.\n")

# 5. knowledge/hotel_info.md
with open("knowledge/hotel_info.md", "w", encoding="utf-8") as f:
    f.write("""# Hotel Sonnenhof Informationen

## Check-in & Check-out
- Check-in: Ab 15:00 Uhr
- Check-out: Bis 11:00 Uhr
- Rezeption: 24 Stunden besetzt

## Frühstück
- Zeiten: Täglich von 07:00 bis 10:30 Uhr
- Preis: 18 Euro pro Person (Buffet)

## Ausstattung & Service
- WLAN: Kostenfrei im gesamten Haus verfügbar
- Parken: Tiefgarage für 15 Euro pro Tag
- Haustiere: Auf Anfrage erlaubt (10 Euro pro Nacht)
""")

# 6. app/knowledge.py
with open("app/knowledge.py", "w", encoding="utf-8") as f:
    f.write('''import os

def load_hotel_knowledge():
    path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "hotel_info.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Hotel Sonnenhof: Check-in ab 15 Uhr, Check-out bis 11 Uhr, Frühstück 7:00-10:30 Uhr."
''')

# 7. app/call_log.py
with open("app/call_log.py", "w", encoding="utf-8") as f:
    f.write('''import json
import os
from datetime import datetime

class CallLogger:
    def __init__(self):
        self.log_dir = os.path.join(os.path.dirname(__file__), "..", "data", "call_logs")
        os.makedirs(self.log_dir, exist_ok=True)

    def log_turn(self, call_id, role, text):
        file_path = os.path.join(self.log_dir, f"{call_id}.jsonl")
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "role": role,
            "text": text
        }
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\\n")
''')

# 8. app/snowflake_sink.py
with open("app/snowflake_sink.py", "w", encoding="utf-8") as f:
    f.write('''def sync_to_snowflake(call_id):
    # Platzhalter für Snowflake-Synchronisation
    pass
''')

# 9. app/tools.py
with open("app/tools.py", "w", encoding="utf-8") as f:
    f.write('''def check_room_availability(date_str, room_type="single"):
    return f"Am {date_str} sind noch freie Zimmer verfügbar."
''')

# 10. app/agent.py
with open("app/agent.py", "w", encoding="utf-8") as f:
    f.write('''import os
import logging
from groq import Groq
from app.knowledge import load_hotel_knowledge
from app.call_log import CallLogger

logger = logging.getLogger("hotel-agent")

FALLBACK = "Entschuldigung, das habe ich leider nicht verstanden. Wie kann ich Ihnen weiterhelfen?"

class HotelAgent:
    def __init__(self, channel="phone", caller=""):
        self.channel = channel
        self.caller = caller
        self.call_id = f"call_{os.urandom(4).hex()}"
        self.log = CallLogger()
        
        api_key = os.environ.get("GROQ_API_KEY")
        model = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
        self.client = Groq(api_key=api_key) if api_key else None
        self.model = model
        
        knowledge_text = load_hotel_knowledge()
        system_prompt = f"""Du bist der freundliche, digitale Telefon-Assistent des Hotels Sonnenhof.
Nutze dieses Wissen zur Beantwortung:
{knowledge_text}

Regeln:
- Antworte extrem kurz, höflich und in leicht verständlichem Deutsch (maximal 2 kurze Sätze).
- Es erfolgt eine telefonische Sprachausgabe, verzichte daher auf Sonderzeichen oder lange Aufzählungen.
"""
        self.history = [{"role": "system", "content": system_prompt}]

    def reply(self, user_text: str) -> str:
        self.log.log_turn(self.call_id, "user", user_text)
        if not self.client:
            return "Der KI-Dienst ist zurzeit leider nicht erreichbar."
        
        self.history.append({"role": "user", "content": user_text})
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.history,
                temperature=0.3,
                max_tokens=150
            )
            answer = response.choices[0].message.content.strip()
            self.history.append({"role": "assistant", "content": answer})
            self.log.log_turn(self.call_id, "assistant", answer)
            return answer
        except Exception as e:
            logger.error(f"Groq Error: {e}")
            return FALLBACK

    def end(self):
        pass
''')

# 11. server.py (Aktualisierte HTTP/Gather Version)
with open("server.py", "w", encoding="utf-8") as f:
    f.write('''import logging
import os
from fastapi import FastAPI, Request, Response
from starlette.concurrency import run_in_threadpool

from app.agent import HotelAgent, FALLBACK

logger = logging.getLogger("hotel-server")

LANGUAGE = os.environ.get("CALL_LANGUAGE", "de-DE")
GREETING = (
    "Guten Tag, hier ist der digitale Assistent des Hotels Sonnenhof. Ich bin eine KI. "
    "Es erfolgt keine Tonaufzeichnung, Anrufdaten werden zur Qualitätssicherung gespeichert. "
    "Wie kann ich helfen?"
)

app = FastAPI(title="Hotel Phone Assistant")
SESSIONS = {}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.api_route("/voice", methods=["GET", "POST"])
async def voice(request: Request):
    host = (
        os.environ.get("PUBLIC_HOST")
        or request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or ""
    )
    host = host.replace("https://", "").replace("http://", "").rstrip("/")
    action_url = f"https://{host}/respond"

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        f'<Gather input="speech" action="{action_url}" method="POST" language="{LANGUAGE}" speechTimeout="auto">'
        f'<Say language="{LANGUAGE}">{GREETING}</Say>'
        '</Gather>'
        f'<Say language="{LANGUAGE}">Ich habe Sie leider nicht gehört. Auf Wiedersehen!</Say>'
        '</Response>'
    )
    return Response(content=xml, media_type="application/xml")

@app.post("/respond")
async def respond(request: Request):
    form_data = await request.form()
    speech_result = form_data.get("SpeechResult", "").strip()
    call_sid = form_data.get("CallSid", "unknown")
    caller = form_data.get("From", "")

    host = (
        os.environ.get("PUBLIC_HOST")
        or request.headers.get("x-forwarded-host")
        or request.headers.get("host")
        or ""
    )
    host = host.replace("https://", "").replace("http://", "").rstrip("/")
    action_url = f"https://{host}/respond"

    if call_sid not in SESSIONS:
        agent = HotelAgent(channel="phone", caller=caller)
        agent.log.log_turn(agent.call_id, "assistant", GREETING)
        SESSIONS[call_sid] = agent
    else:
        agent = SESSIONS[call_sid]

    if speech_result:
        try:
            answer = await run_in_threadpool(agent.reply, speech_result)
        except Exception:
            logger.exception("Agent failed")
            answer = FALLBACK
    else:
        answer = "Ich habe Sie leider nicht verstanden."

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Response>'
        f'<Gather input="speech" action="{action_url}" method="POST" language="{LANGUAGE}" speechTimeout="auto">'
        f'<Say language="{LANGUAGE}">{answer}</Say>'
        '</Gather>'
        f'<Say language="{LANGUAGE}">Vielen Dank für Ihren Anruf beim Hotel Sonnenhof. Auf Wiedersehen!</Say>'
        '</Response>'
    )
    return Response(content=xml, media_type="application/xml")
''')

# 12. Hilfsskripte & Snowflake SQL Dateidummies
with open("chat.py", "w", encoding="utf-8") as f:
    f.write('''from app.agent import HotelAgent
if __name__ == "__main__":
    agent = HotelAgent(channel="cli")
    print("Hotel Assistent CLI Chat (Beenden mit Ctrl+C)")
    while True:
        try:
            inp = input("Sie: ")
            print("KI:", agent.reply(inp))
        except KeyboardInterrupt:
            break
''')

with open("show_calls.py", "w", encoding="utf-8") as f:
    f.write("# Zeigt Anruflogs an\n")

with open("sync_calls.py", "w", encoding="utf-8") as f:
    f.write("# Synchronisiert Anruflogs zu Snowflake\n")

with open("test_server.py", "w", encoding="utf-8") as f:
    f.write("# Unittests für FastAPI Server\n")

with open("data/.gitkeep", "w", encoding="utf-8") as f:
    f.write("")

with open("data/escalations.jsonl", "w", encoding="utf-8") as f:
    f.write("")

with open("snowflake/setup.sql", "w", encoding="utf-8") as f:
    f.write("-- Snowflake Setup DDL\n")

with open("snowflake/analytics.sql", "w", encoding="utf-8") as f:
    f.write("-- Snowflake Analytics Queries\n")

print("Projekterstellung ABGESCHLOSSEN!")
