from enum import EnumStr


class ErrorType(EnumStr):
    """Enumeration of high-level domain error categories."""

    BUSINESS_RULE_VIOLATION = "BusinessRuleViolation"
    ENTITY_NOT_FOUND = "EntityNotFound"
    VALIDATION_ERROR = "ValidationError"
    CONFLICT_ERROR = "ConflictError"
    UNAUTHORIZED_ACCESS = "UnauthorizedAccess"
    FORBIDDEN_ACCESS = "ForbiddenAccess"
    INFRASTRUCTURE_ERROR = "InfrastructureError"
    INTERNAL_ERROR = "InternalError"


class ErrorCode(EnumStr):
    """Enumeration of well-known domain error codes."""

    BUSINESS_RULE_VIOLATION = "BusinessRuleViolation"
    INVALID_INPUT = "InvalidInput"
    ENTITY_NOT_FOUND = "EntityNotFound"
    UNAUTHORIZED_ACCESS = "UnauthorizedAccess"
    FORBIDDEN_ACCESS = "ForbiddenAccess"
    CONFLICT_ERROR = "ConflictError"
    INFRASTRUCTURE_FAILURE = "InfrastructureFailure"
    INTERNAL_ERROR = "InternalError"
    INVALID_EMAIL_ADDRESS = "InvalidEmailAddress"
    INVALID_PASSWORD = "InvalidPassword"
    VALIDATION_ERROR = "ValidationError"
    SESSION_EXPIRATION_INVALID = "SessionExpirationInvalid"
