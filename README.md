# GERMAN-AI-VOICE-ASSISTANT-

python3 -c "
readme = '''# 🏨 AI Hotel Phone Assistant (German)

An automated, real-time German-language hotel voice assistant built using **FastAPI**, **Twilio Voice Webhooks (<Gather>)**, and **Groq LLM** (\`openai/gpt-oss-120b\`).

The assistant handles incoming telephone calls, answers questions about check-in, breakfast, amenities, and policies based on a local Knowledge Base (\`hotel_info.md\`), and records full conversational logs locally.

---

## 🏗 Architecture Overview

\`\`\`
 Caller ──> Twilio Phone Number ──(HTTP Webhook)──> FastAPI (/voice & /respond)
                                                          │
                                         ┌────────────────┴────────────────┐
                                         ▼                                 ▼
                                Knowledge Base                    Groq LLM API
                             (hotel_info.md)                  (gpt-oss-120b)
                                         │                                 │
                                         └────────────────┬────────────────┘
                                                          ▼
                                                  Call Logs (.jsonl)
\`\`\`

1. **Incoming Call (\`/voice\`):** Twilio hits the \`/voice\` endpoint. The assistant responds with a TwiML \`<Gather input=\"speech\">\` greeting.
2. **Speech Recognition & Processing (\`/respond\`):** Twilio transcribes caller speech and POSTs \`SpeechResult\` to \`/respond\`.
3. **LLM Response Generation:** \`HotelAgent\` fetches contextual facts from \`knowledge/hotel_info.md\` and streams caller input to Groq LLM to build a concise 1-2 sentence response.
4. **Text-To-Speech Output:** TwiML returns the answer wrapped in a \`<Say language=\"de-DE\">\` tag within a new \`<Gather>\` loop.
5. **Persistence:** Every turn is recorded in \`data/call_logs/<call_id>.jsonl\`.

---

## 📁 Repository Structure

\`\`\`
hotel-assistant/
├── app/
│   ├── __init__.py
│   ├── agent.py            # Core LLM Agent logic & prompt management
│   ├── call_log.py         # Local JSONL conversational logging
│   ├── knowledge.py        # Loader for local markdown knowledge base
│   ├── snowflake_sink.py   # Sink hook for Snowflake analytics integration
│   └── tools.py            # Dynamic function hooks (e.g., room availability)
├── data/
│   ├── call_logs/          # Stored conversation transcripts (.jsonl)
│   └── escalations.jsonl   # Logged caller escalation requests
├── knowledge/
│   └── hotel_info.md       # Knowledge Base (Check-in, breakfast, Wi-Fi, etc.)
├── snowflake/
│   ├── setup.sql           # Database schema DDL
│   └── analytics.sql       # Analytics & reporting queries
├── .gitignore
├── chat.py                 # CLI interface for local agent testing
├── requirements.txt        # Python dependencies
├── server.py               # Main FastAPI webhook server
└── README.md
\`\`\`

---

## 🚀 Quick Start

### 1. Prerequisites & Environment Setup

Clone the repository and create a Python virtual environment:

\`\`\`bash
git clone https://github.com/your-username/hotel-voice-assistant.git
cd hotel-voice-assistant

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
\`\`\`

### 2. Configure Environment Variables

Set your Groq API Key and public server URL (e.g., GitHub Codespaces or ngrok):

\`\`\`bash
export GROQ_API_KEY=\"your-groq-api-key\"
export GROQ_MODEL=\"openai/gpt-oss-120b\"
export PUBLIC_HOST=\"your-public-host-url.app.github.dev\"
export CALL_LANGUAGE=\"de-DE\"
\`\`\`

### 3. Run the FastAPI Server

\`\`\`bash
python3 -m uvicorn server:app --port 8000
\`\`\`

Verify server health at \`http://localhost:8000/health\`.

---

## 📞 Twilio Webhook Integration

1. Go to your **Twilio Console** > **Phone Numbers** > **Active Numbers**.
2. Under **A Call Comes In**, select **Webhook** and set the URL to:
   \`https://<YOUR_PUBLIC_HOST>/voice\`
3. Set HTTP Method to **POST**.
4. Save and place a live phone call to test the assistant.

---

## 🛠 Customizing Hotel Information

Update \`knowledge/hotel_info.md\` with your specific hotel details. The agent automatically includes this context in its prompt rules without requiring code changes.

\`\`\`markdown
# Hotel Sonnenhof Information
- Check-in: Ab 15:00 Uhr
- Check-out: Bis 11:00 Uhr
- Frühstück: 07:00 - 10:30 Uhr (18€ per person)
\`\`\`

---

## 📄 License

MIT License.
'''

with open('README.md', 'w', encoding='utf-8') as f:
    f.write(readme)
print('README.md sauber erstellt!')
"
