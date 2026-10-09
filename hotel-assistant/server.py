import logging
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
