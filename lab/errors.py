"""Shared exception types."""


class LabError(Exception):
    """Base class for expected, user-facing lab errors."""


class DataError(LabError):
    """Raised when teacher-provided company data cannot be read or queried."""


class InstructionError(LabError):
    """Raised when a student instruction file is invalid or missing."""


class SkillError(LabError):
    """Raised when a built-in skill is invalid or missing."""


class SessionError(LabError):
    """Raised when a session or turn cannot be recorded or loaded."""


class ExportError(LabError):
    """Raised when a PDF or ZIP cannot be produced."""
