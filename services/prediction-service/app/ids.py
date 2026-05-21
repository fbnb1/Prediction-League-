import uuid


def new_id(prefix: str) -> str:
    """Generate a prefixed, reasonably-unique identifier (e.g. usr_a1b2c3...)."""
    return f"{prefix}_{uuid.uuid4().hex[:16]}"
