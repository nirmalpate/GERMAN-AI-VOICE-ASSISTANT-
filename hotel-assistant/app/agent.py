import os
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
