from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd
from backend.app.models.assumptions import AssumptionRule, AssumptionResult
from backend.app.models.analysis import MethodResult
from backend.app.services.assumptions.checker import AssumptionChecker


class BaseStatisticalMethod(ABC):
    """Base class for all statistical methods in StatMind AI."""
    
    # Subclasses MUST define these
    method_id: str
    method_name: str
    method_family: str
    description: str
    required_variables: Dict[str, List[str]]  # {"dependent": ["continuous"], "grouping": ["categorical"]}
    optional_variables: Dict[str, List[str]] = {}
    assumptions: List[AssumptionRule] = []
    
    def _normalize_variables(self, variables: Dict[str, Any]) -> None:
        """Safely map any incoming variable role dict to what the method expects."""
        if "variables" in self.required_variables and ("variables" not in variables or not variables.get("variables")):
            if "var1" in variables and "var2" in variables and variables["var1"] and variables["var2"]:
                variables["variables"] = [variables["var1"], variables["var2"]]
            elif "row_var" in variables and "col_var" in variables and variables["row_var"] and variables["col_var"]:
                variables["variables"] = [variables["row_var"], variables["col_var"]]
            elif "dependent" in variables and variables["dependent"]:
                var_list = [variables["dependent"]] if isinstance(variables["dependent"], str) else list(variables["dependent"])
                if "grouping" in variables and variables["grouping"]:
                    var_list.extend(variables["grouping"] if isinstance(variables["grouping"], list) else [variables["grouping"]])
                elif "independent" in variables and variables["independent"]:
                    var_list.extend(variables["independent"] if isinstance(variables["independent"], list) else [variables["independent"]])
                variables["variables"] = var_list
        if "dependent" in self.required_variables and ("dependent" not in variables or not variables.get("dependent")):
            if "var1" in variables and variables["var1"]:
                variables["dependent"] = variables["var1"]
            elif "row_var" in variables and variables["row_var"]:
                variables["dependent"] = variables["row_var"]
            elif "variables" in variables and variables["variables"]:
                v_list = variables["variables"] if isinstance(variables["variables"], list) else [variables["variables"]]
                if v_list: variables["dependent"] = v_list[0]
        if "grouping" in self.required_variables and ("grouping" not in variables or not variables.get("grouping")):
            if "var2" in variables and variables["var2"]:
                variables["grouping"] = variables["var2"]
            elif "col_var" in variables and variables["col_var"]:
                variables["grouping"] = variables["col_var"]
            elif "independent" in variables and variables["independent"]:
                variables["grouping"] = variables["independent"][0] if isinstance(variables["independent"], list) else variables["independent"]
            elif "variables" in variables and variables["variables"]:
                v_list = variables["variables"] if isinstance(variables["variables"], list) else [variables["variables"]]
                if len(v_list) > 1: variables["grouping"] = v_list[1]
        if "independent" in self.required_variables and ("independent" not in variables or not variables.get("independent")):
            if "grouping" in variables and variables["grouping"]:
                variables["independent"] = variables["grouping"] if isinstance(variables["grouping"], list) else [variables["grouping"]]
            elif "var2" in variables and variables["var2"]:
                variables["independent"] = [variables["var2"]]
            elif "variables" in variables and variables["variables"]:
                v_list = variables["variables"] if isinstance(variables["variables"], list) else [variables["variables"]]
                if len(v_list) > 1: variables["independent"] = v_list[1:]

    def check_assumptions(self, data: pd.DataFrame, variables: Dict[str, Any]) -> List[AssumptionResult]:
        """Check all assumptions for this method using the AssumptionChecker engine."""
        self._normalize_variables(variables)
        return AssumptionChecker.check_all(self.method_id, data, variables)
    
    @abstractmethod
    def run(self, data: pd.DataFrame, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> MethodResult:
        """Execute the statistical analysis."""
        pass
    
    @abstractmethod
    def generate_r_code(self, variables: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> str:
        """Generate equivalent R code."""
        pass
    
    @abstractmethod
    def generate_plots(self, data: pd.DataFrame, variables: Dict[str, Any], results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate Plotly figure JSONs."""
        pass
    
    @abstractmethod
    def interpret(self, results: Dict[str, Any], variables: Dict[str, Any]) -> str:
        """Generate plain English interpretation."""
        pass
    
    def validate_variables(self, data: pd.DataFrame, variables: Dict[str, Any]) -> List[str]:
        """Validate that required variables exist and have compatible data types."""
        self._normalize_variables(variables)
        errors = []
        for role, expected_types in self.required_variables.items():
            if role not in variables or variables[role] is None:
                errors.append(f"Missing required variable role: '{role}'")
                continue
            var_value = variables[role]
            
            # Can be single string column name or list of column names
            var_names = [var_value] if isinstance(var_value, str) else var_value
            if not var_names:
                errors.append(f"No variables provided for role: '{role}'")
                continue
                
            for v in var_names:
                if v not in data.columns:
                    errors.append(f"Variable '{v}' not found in dataset columns")
                else:
                    # Check for zero variance / all nulls
                    col_data = data[v].dropna()
                    if col_data.empty:
                        errors.append(f"Variable '{v}' contains only missing values")
                    elif col_data.nunique() <= 1 and role != "covariates":
                        errors.append(f"Variable '{v}' has zero variance (all identical values)")
                        
        return errors
