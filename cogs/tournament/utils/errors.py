from utils import BaseParkourException


class TournamentNotActiveError(BaseParkourException):
    """There is no active tournament."""


class TournamentAlreadyExists(BaseParkourException):
    """A tournament already exists."""


class InvalidMissionType(BaseParkourException):
    """Invalid mission type given."""


class MismatchedMissionCategoryType(BaseParkourException):
    """Invalid combination of category and mission type."""


class TargetNotInteger(BaseParkourException):
    """Target must be an integer."""


class NoMissionExists(BaseParkourException):
    """There is no mission data."""
