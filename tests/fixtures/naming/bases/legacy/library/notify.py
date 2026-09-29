class Beacon:
    """Sends letters to members; the outbox keeps what was sent."""

    def __init__(self):
        self.outbox = []

    def ping(self, client_id, msg_code):
        self.outbox.append((client_id, msg_code))
