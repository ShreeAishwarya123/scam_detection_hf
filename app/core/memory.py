class ConversationMemory:
    def __init__(self):
        self.history = []
        self.stage = "initial"

    def add(self, sender, message):
        self.history.append(f"{sender}: {message}")

    def context(self):
        return "\n".join(self.history[-6:])
