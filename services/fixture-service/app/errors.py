class MatchNotFound(Exception):
    """Raised when a match id does not exist."""


class MatchAlreadySettled(Exception):
    """Raised when a result is entered for a match that is already settled."""
