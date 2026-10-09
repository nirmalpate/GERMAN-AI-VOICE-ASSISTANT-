import os

def load_hotel_knowledge():
    path = os.path.join(os.path.dirname(__file__), "..", "knowledge", "hotel_info.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "Hotel Sonnenhof: Check-in ab 15 Uhr, Check-out bis 11 Uhr, Frühstück 7:00-10:30 Uhr."
