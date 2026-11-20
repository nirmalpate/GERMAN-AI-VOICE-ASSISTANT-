import os, time, uuid, jwt, requests
from dotenv import load_dotenv

load_dotenv()
app_id = os.environ["VONAGE_APPLICATION_ID"].strip()
key_path = os.environ.get("VONAGE_PRIVATE_KEY_PATH", "private.key").strip()
key = open(key_path, "r", encoding="utf-8-sig").read().strip()

now = int(time.time())
token = jwt.encode(
{"application_id": app_id, "iat": now, "exp": now + 300, "jti": str(uuid.uuid4())},
key,
algorithm="RS256",
)
r = requests.get("https://api.nexmo.com/v1/calls", headers={"Authorization": f"Bearer {token}"})
print("APP_ID:", app_id)
print("STATUS:", r.status_code)
print("BODY:", r.text)