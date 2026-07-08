from enum import Enum
from typing import Any, Dict, Optional


class StatMindErrorLevel(str, Enum):
    """Hierarchy of error and alert levels for StatMind AI."""
    INFO = "info"                             # Level 1: Informational (no action needed)
    WARNING = "warning"                       # Level 2: Warning (analysis can proceed, user should know)
    ASSUMPTION_VIOLATION = "assumption_violation"  # Level 3: Assumption Violation (analysis may be invalid)
    USER_ERROR = "user_error"                 # Level 4: User Error (wrong input, can be fixed)
    SYSTEM_ERROR = "system_error"             # Level 5: System Error (something broke, not user's fault)


class StatMindException(Exception):
    """Base exception class for StatMind AI errors with user-friendly translation."""
    def __init__(
        self,
        error_code: str,
        level: StatMindErrorLevel = StatMindErrorLevel.USER_ERROR,
        format_kwargs: Optional[Dict[str, Any]] = None,
        raw_error: Optional[Exception] = None
    ):
        self.error_code = error_code
        self.level = level
        self.format_kwargs = format_kwargs or {}
        self.raw_error = raw_error
        self.translation = self.get_translation()
        super().__init__(self.translation["message"])

    def get_translation(self) -> Dict[str, str]:
        template = ERROR_TRANSLATIONS.get(self.error_code, {
            "title": "Unexpected Error",
            "message": "An unexpected issue occurred while processing your request.",
            "action": "Please try again or contact support if the issue persists.",
            "icon": "alert-circle"
        })
        return {
            "title": template["title"],
            "message": template["message"].format(**self.format_kwargs),
            "action": template["action"].format(**self.format_kwargs),
            "icon": template["icon"]
        }


ERROR_TRANSLATIONS = {
    # Data errors
    "FileNotFoundError": {
        "title": "Dataset Not Found",
        "message": "We couldn't find your dataset. It may have been deleted or the session expired.",
        "action": "Please upload your dataset again.",
        "icon": "file-x"
    },
    "EmptyDataError": {
        "title": "Empty Dataset",
        "message": "Your dataset appears to be empty (0 rows).",
        "action": "Check that your file contains data and try uploading again.",
        "icon": "database"
    },
    "ParserError": {
        "title": "File Format Error",
        "message": "We couldn't read your file. This usually means the file format is corrupted or unsupported.",
        "action": "Try saving your file as CSV or XLSX and upload again.",
        "icon": "file-warning"
    },
    
    # Variable errors
    "VariableNotFound": {
        "title": "Variable Not Found",
        "message": "The variable '{variable_name}' doesn't exist in your dataset.",
        "action": "Available variables: {available_variables}",
        "icon": "search-x"
    },
    "WrongVariableType": {
        "title": "Wrong Variable Type",
        "message": "The {method_name} requires a {required_type} variable for '{role}', but '{variable_name}' is detected as {actual_type}.",
        "action": "You can: (1) Select a different variable, (2) Change the variable type in the dataset panel, or (3) Use a different method.",
        "icon": "type"
    },
    
    # Statistical errors
    "InsufficientData": {
        "title": "Insufficient Sample Size",
        "message": "The {method_name} requires at least {min_n} observations, but only {actual_n} are available (after removing missing values).",
        "action": "Consider: (1) Including more rows in your dataset, (2) Using a different variable with fewer missing values, or (3) Using a method suitable for small samples.",
        "icon": "users"
    },
    "ConstantVariable": {
        "title": "Zero Variance Detected",
        "message": "The variable '{variable_name}' has identical values for all rows in the analysis sample.",
        "action": "Statistical comparisons require variation. Please select a variable with at least two distinct values.",
        "icon": "alert-triangle"
    },
    "MulticollinearityError": {
        "title": "Severe Multicollinearity",
        "message": "The predictor variables are too highly correlated with each other (VIF > {max_vif}).",
        "action": "Remove redundant predictor variables or combine them into a single index.",
        "icon": "git-merge"
    },
    "StatisticalViolation": {
        "title": "Statistical Requirement Violation",
        "message": "{message}",
        "action": "{remedy}",
        "icon": "alert-triangle"
    },
    "AnalysisFailed": {
        "title": "Analysis Execution Failed",
        "message": "{message}",
        "action": "Please check your dataset columns and analysis options.",
        "icon": "alert-circle"
    },
    "ResourceExceeded": {
        "title": "Resource Limit Exceeded",
        "message": "{message}",
        "action": "Please reduce the dataset size or operation complexity to stay within sandbox limits.",
        "icon": "cpu"
    }
}


class AnalysisFailedException(StatMindException):
    """Exception raised when an analysis procedure fails to complete or cannot be found."""
    def __init__(self, message: str, user_friendly_message: Optional[str] = None):
        self.message = message
        self.user_friendly_message = user_friendly_message or message
        super().__init__(error_code="AnalysisFailed", level=StatMindErrorLevel.SYSTEM_ERROR, format_kwargs={"message": self.user_friendly_message})


class StatisticalViolationException(StatMindException):
    """Exception raised when dataset or variable role violations prevent valid statistical analysis."""
    def __init__(self, message: str, violation_type: str = "variable_error", remedy: Optional[str] = None):
        self.message = message
        self.violation_type = violation_type
        self.remedy = remedy or "Double check your selected variables to make sure they match the required columns and data types."
        super().__init__(error_code="StatisticalViolation", level=StatMindErrorLevel.ASSUMPTION_VIOLATION, format_kwargs={"message": message, "remedy": self.remedy})


class ResourceExceededException(StatMindException):
    """Exception raised when memory, row count, or execution timeouts exceed sandbox limits."""
    def __init__(self, message: str, resource_type: str, limit: str):
        self.message = message
        self.resource_type = resource_type
        self.limit = limit
        super().__init__(error_code="ResourceExceeded", level=StatMindErrorLevel.SYSTEM_ERROR, format_kwargs={"message": message})
