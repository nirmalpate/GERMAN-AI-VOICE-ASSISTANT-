"""In-memory session store (plain Python dicts/lists).

Same interface as the Redis version, but data lives in the server process:
it is lost on restart and works with a single uvicorn worker only.
"""
import time
import threading


class SessionStore:
    def __init__(self, ttl: int = 7200, max_history: int = 20):
        self.ttl = ttl
        self.max_history = max_history
        self.sessions = {}      # uuid -> {caller, silence_count, transfer_requested, started_at, expires}
        self.histories = {}     # uuid -> [(role, text), ...]
        self.call_log = []      # finished calls (details only, no audio)
        self._lock = threading.Lock()

    def _purge(self):
        now = time.time()
        for u in [u for u, s in self.sessions.items() if s["expires"] < now]:
            self._end_locked(u, "expired")

    def _touch(self, uuid):
        self.sessions[uuid]["expires"] = time.time() + self.ttl

    def active_count(self) -> int:
        with self._lock:
            self._purge()
            return len(self.sessions)

    def exists(self, uuid) -> bool:
        with self._lock:
            self._purge()
            return uuid in self.sessions

    def create(self, uuid, caller="Unbekannt"):
        with self._lock:
            self.sessions[uuid] = {
                "caller": caller,
                "silence_count": 0,
                "transfer_requested": False,
                "started_at": int(time.time()),
                "expires": time.time() + self.ttl,
            }
            self.histories[uuid] = []

    def caller(self, uuid) -> str:
        with self._lock:
            return self.sessions.get(uuid, {}).get("caller", "Unbekannt")

    def incr_silence(self, uuid) -> int:
        with self._lock:
            self.sessions[uuid]["silence_count"] += 1
            return self.sessions[uuid]["silence_count"]

    def reset_silence(self, uuid):
        with self._lock:
            self.sessions[uuid]["silence_count"] = 0

    def set_transfer(self, uuid, flag: bool = True):
        with self._lock:
            self.sessions[uuid]["transfer_requested"] = flag

    def pop_transfer(self, uuid) -> bool:
        with self._lock:
            s = self.sessions.get(uuid)
            if not s:
                return False
            flag, s["transfer_requested"] = s["transfer_requested"], False
            return flag

    def add_message(self, uuid, role: str, text: str):
        with self._lock:
            h = self.histories.setdefault(uuid, [])
            h.append((role, text))
            del h[:-self.max_history]
            if uuid in self.sessions:
                self._touch(uuid)

    def history(self, uuid) -> list[tuple[str, str]]:
        with self._lock:
            return list(self.histories.get(uuid, []))

    def _end_locked(self, uuid, reason):
        s = self.sessions.pop(uuid, None)
        h = self.histories.pop(uuid, [])
        if s:
            self.call_log.append({
                "uuid": uuid,
                "caller": s["caller"],
                "started_at": s["started_at"],
                "ended_at": int(time.time()),
                "turns": len(h),
                "reason": reason,
            })
            self.call_log = self.call_log[-1000:]

    def end(self, uuid, reason: str):
        with self._lock:
            self._end_locked(uuid, reason)
