from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional


class VariableType(str, Enum):
    """Supported variable data types in StatMind AI."""
    CONTINUOUS = "continuous"   # Numeric, can take any value (height, weight, income)
    CATEGORICAL = "categorical" # Named categories (gender, color, department)
    ORDINAL = "ordinal"         # Ordered categories (education level, Likert scale)
    BINARY = "binary"           # Exactly two categories (yes/no, male/female, pass/fail)
    COUNT = "count"             # Non-negative integers (number of children, errors)
    DATETIME = "datetime"       # Date or time values


class VariableRole(str, Enum):
    """Roles variables can play in statistical models."""
    DEPENDENT = "dependent"     # Outcome / target variable (Y)
    INDEPENDENT = "independent" # Predictor / explanatory variable (X)
    GROUPING = "grouping"       # Categorical split / factor variable
    COVARIATES = "covariates"   # Control variables
    VARIABLES = "variables"     # General variables list (e.g., for correlation)


class VariableRequirement(BaseModel):
    """Specifies what type and properties a variable role requires for a statistical method."""
    type: VariableType
    min_levels: Optional[int] = None
    max_levels: Optional[int] = None
    count: Optional[int] = None
    description: Optional[str] = None
