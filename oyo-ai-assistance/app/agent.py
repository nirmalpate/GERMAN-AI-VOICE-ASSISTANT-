import os
from datetime import datetime
from zoneinfo import ZoneInfo

from groq import Groq

from app.store import SessionStore

HOTEL_NAME = os.environ.get("HOTEL_NAME", "OYO Hotel")

SYSTEM_PROMPT = (
    f"Du bist die freundliche Telefon-Assistenz des {HOTEL_NAME}. "
    "Antworte immer auf Deutsch, kurz (max. 2 Sätze), höflich und für Telefon geeignet. "
    "Hilf bei Fragen zu Zimmern, Frühstück, Check-in/out und Anreise. "
    "Erfinde keine Preise oder Verfügbarkeiten. Wenn du etwas nicht weißt oder der Gast "
    "ausdrücklich einen Menschen sprechen will oder es dringend ist, hänge am Ende "
    "exakt [TRANSFER] an."
)


class HotelAgent:
    def __init__(self, call_id: str, store: SessionStore):
        self.call_id = call_id
        self.store = store
        self._client = None

    @property
    def is_night_shift(self) -> bool:
        hour = datetime.now(ZoneInfo("Europe/Berlin")).hour
        return hour >= 22 or hour < 6

    def reply(self, speech: str) -> str:
        if self._client is None:
            self._client = Groq(api_key=os.environ["GROQ_API_KEY"])
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages += [{"role": r, "content": t} for r, t in self.store.history(self.call_id)]
        messages.append({"role": "user", "content": speech})

        resp = self._client.chat.completions.create(
            model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=messages,
            temperature=0.3,
            max_tokens=150,
        )
        text = (resp.choices[0].message.content or "").strip()

        if "[TRANSFER]" in text:
            text = text.replace("[TRANSFER]", "").strip()
            self.store.set_transfer(self.call_id, True)

        self.store.add_message(self.call_id, "user", speech)
        self.store.add_message(self.call_id, "assistant", text)
        return text
