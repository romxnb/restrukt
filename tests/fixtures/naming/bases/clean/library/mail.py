"""Letters to members."""


class Mailer:
    """Queues letters; the mail worker delivers them from the outbox."""

    def __init__(self) -> None:
        self.outbox: list[tuple[str, int, str]] = []

    def send_hold_ready(self, member_id: int, isbn: str) -> None:
        """Tell the member that the held book waits at the desk."""
        self.outbox.append(("hold_ready", member_id, isbn))
