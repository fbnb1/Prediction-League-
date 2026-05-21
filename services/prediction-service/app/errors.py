class EmailAlreadyRegistered(Exception):
    """Registration with an email that already exists."""


class InvalidCredentials(Exception):
    """Login with a wrong email or password."""


class GroupNotFound(Exception):
    """Referenced group does not exist."""


class NotGroupMember(Exception):
    """The user is not a member of the group."""


class MatchNotFound(Exception):
    """Referenced match is not known to the Prediction service."""


class LockWindowClosed(Exception):
    """A pick was submitted at or after the lock time."""
