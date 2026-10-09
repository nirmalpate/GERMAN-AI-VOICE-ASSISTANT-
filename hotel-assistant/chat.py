from app.agent import HotelAgent
if __name__ == "__main__":
    agent = HotelAgent(channel="cli")
    print("Hotel Assistent CLI Chat (Beenden mit Ctrl+C)")
    while True:
        try:
            inp = input("Sie: ")
            print("KI:", agent.reply(inp))
        except KeyboardInterrupt:
            break
