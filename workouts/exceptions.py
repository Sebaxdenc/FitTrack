class WorkoutDomainError(Exception):
    """Base exception for workout domain operations."""


class ExerciseError(WorkoutDomainError):
    """Base exception for exercise operations."""


class RoutineError(WorkoutDomainError):
    """Base exception for routine operations."""


class ExerciseAccessDeniedError(ExerciseError):
    """Raised when a user cannot manage an exercise."""


class ExerciseNotFoundError(ExerciseError):
    """Raised when the requested exercise does not exist."""


class ExerciseDescriptionGenerationError(ExerciseError):
    """Raised when an exercise description cannot be generated."""


class ExerciseDescriptionConfigurationError(ExerciseDescriptionGenerationError):
    """Raised when AI generation is not configured."""


class RoutineAccessDeniedError(RoutineError):
    """Raised when a user cannot manage a routine."""


class RoutineNotFoundError(RoutineError):
    """Raised when the requested routine does not exist."""


class RoutineValidationError(RoutineError):
    """Raised when routine input data is invalid."""


class RoutineAlreadyScheduledError(RoutineError):
    """Raised when a routine day assignment is duplicated."""
