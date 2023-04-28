from utils import BaseParkourException


class PlayerAlreadyInMatch(BaseParkourException):
    """Players cannot be in a match."""


class NotEnoughXP(BaseParkourException):
    """All players must have enough XP to cover the wager amount."""
