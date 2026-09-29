"""Member registration."""

from .models import Member
from .storage import Storage


def register_member(storage: Storage, member_id: int, name: str, email: str) -> Member:
    """Register a new member; registering an existing member returns the stored record unchanged."""
    member = storage.find_member(member_id)
    if member is None:
        member = Member(member_id, name, email)
        storage.add_member(member)
    return member
