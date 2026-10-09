import json
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
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
