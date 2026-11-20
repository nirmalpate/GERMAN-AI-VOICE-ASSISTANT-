import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool

from app.agent import HotelAgent
from app.store import SessionStore

load_dotenv()

app = FastAPI(title="Oyo AI Assistance (Vonage + in-memory dict)")

store = SessionStore(ttl=7200)

HOTEL_NAME = os.environ.get("HOTEL_NAME", "OYO Hotel").strip()
NIGHT_PORTIER_NUMBER = os.environ.get("NIGHT_PORTIER_NUMBER", "").strip()

NO_INPUT_TEXT = "Ich habe leider nichts gehört. Vielen Dank für Ihren Anruf und einen angenehmen Aufenthalt. Auf Wiederhören."
UNCLEAR_TEXT = "Entschuldigung, das habe ich akustisch gerade nicht verstanden. Könnten Sie das bitte noch einmal sagen?"
ERROR_TEXT = "Entschuldigung, bei uns gibt es gerade eine kleine technische Störung. Bitte versuchen Sie es gleich noch einmal."


def public_base_url(request: Request) -> str:
    env_url = os.environ.get("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if env_url:
        return env_url
    proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))
    return f"{proto}://{host}"


def get_agent(uuid: str) -> HotelAgent:
    return HotelAgent(call_id=uuid, store=store)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "hotel": HOTEL_NAME,
        "telephony": "Vonage",
        "store": "in-memory dict",
        "active_calls": store.active_count(),
    }


@app.get("/debug/calls")
def debug_calls():
    return {"sessions": store.sessions, "histories": store.histories, "finished_calls": store.call_log}


def vonage_ncco(request: Request, text: str, final: bool = False) -> list:
    ncco = [{"action": "talk", "text": text, "language": "de-DE", "style": 0, "bargeIn": not final}]
    if not final:
        ncco.append({
            "action": "input",
            "type": ["speech"],
            "eventUrl": [f"{public_base_url(request)}/vonage/input"],
            "eventMethod": "POST",
            "speech": {"language": "de-DE", "endOnSilence": 1.5, "startTimeout": 10, "maxDuration": 25},
        })
    return ncco


async def _params(request: Request) -> dict:
    if request.method == "GET":
        return dict(request.query_params)
    try:
        return await request.json()
    except Exception:
        return {}


@app.api_route("/vonage/answer", methods=["GET", "POST"])
async def vonage_answer(request: Request):
    p = await _params(request)
    uuid = p.get("uuid") or p.get("conversation_uuid") or "unknown"
    caller = str(p.get("from", "Unbekannt"))

    if not store.exists(uuid):
        store.create(uuid, caller)
    agent = get_agent(uuid)

    if agent.is_night_shift:
        greeting = (
            f"Guten Abend und willkommen beim Nachtdienst im {HOTEL_NAME}. "
            "Wie kann ich Ihnen helfen – haben Sie ein dringendes Anliegen?"
        )
    else:
        greeting = (
            f"Guten Tag und herzlich willkommen an der Rezeption im {HOTEL_NAME}. "
            "Was kann ich für Sie tun?"
        )
    return vonage_ncco(request, greeting)


@app.post("/vonage/input")
async def vonage_input(request: Request):
    p = await _params(request)
    uuid = p.get("uuid") or p.get("conversation_uuid") or "unknown"

    if not store.exists(uuid):
        store.create(uuid)
    agent = get_agent(uuid)

    results = (p.get("speech") or {}).get("results") or []
    speech = (results[0].get("text", "") if results else "").strip()

    if not speech:
        if store.incr_silence(uuid) >= 2:
            store.end(uuid, "no_input")
            return vonage_ncco(request, NO_INPUT_TEXT, final=True)
        return vonage_ncco(request, UNCLEAR_TEXT)

    store.reset_silence(uuid)

    try:
        reply_text = await run_in_threadpool(agent.reply, speech)
    except Exception as e:
        print(f"[agent error] {uuid}: {e}")
        return vonage_ncco(request, ERROR_TEXT)

    if store.pop_transfer(uuid) and NIGHT_PORTIER_NUMBER:
        store.end(uuid, "transferred")
        return [
            {"action": "talk", "text": reply_text, "language": "de-DE", "style": 0},
            {"action": "connect", "endpoint": [{"type": "phone", "number": NIGHT_PORTIER_NUMBER.lstrip("+")}]},
        ]
    return vonage_ncco(request, reply_text)


@app.post("/vonage/event")
async def vonage_event(request: Request):
    p = await _params(request)
    status = p.get("status")
    if status in ("completed", "failed", "rejected", "busy", "cancelled", "timeout", "unanswered"):
        uuid = p.get("uuid", "")
        if uuid:
            store.end(uuid, status)
    return {"status": "ok"}
