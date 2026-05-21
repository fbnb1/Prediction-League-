class UsernameAlreadyRegistered(Exception):
    """Registration with a username that already exists."""


class InvalidCredentials(Exception):
    """Login with a wrong username or password."""


class GroupNotFound(Exception):
    """Referenced group does not exist."""


class NotGroupMember(Exception):
    """The user is not a member of the group."""


class MatchNotFound(Exception):
    """Referenced match is not known to the Prediction service."""


class LockWindowClosed(Exception):
    """A pick was submitted at or after the lock time."""


class InvalidPickForBetType(Exception):
    """The predicted outcome is not valid for the group's bet type."""
