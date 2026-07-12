"""
Power & Sample Size Studio API Endpoints
Provides A-Priori sample size determination and Post-Hoc power calculation endpoints.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from backend.app.services.statistics.power_engine import PowerAnalysisEngine

router = APIRouter()


class APrioriPowerRequest(BaseModel):
    test_type: str = Field("ttest_independent", description="Statistical test identifier")
    effect_size: float = Field(0.50, description="Expected or hypothesized effect size")
    alpha: float = Field(0.05, description="Significance level alpha e.g. 0.05")
    power: float = Field(0.80, description="Desired statistical power 1 - beta e.g. 0.80")
    groups: int = Field(2, description="Number of comparison groups (for ANOVA/Chi-Square)")
    predictors: int = Field(1, description="Number of independent predictors (for Regression)")


class PostHocPowerRequest(BaseModel):
    test_type: str = Field("ttest_independent", description="Statistical test identifier")
    sample_size: int = Field(..., description="Achieved total sample size N")
    effect_size: float = Field(..., description="Observed effect size")
    alpha: float = Field(0.05, description="Significance level alpha e.g. 0.05")
    groups: int = Field(2, description="Number of comparison groups")
    predictors: int = Field(1, description="Number of independent predictors")


@router.post("/calculate-sample-size", summary="Perform A-Priori sample size and power curve analysis")
async def calculate_sample_size_endpoint(request: APrioriPowerRequest) -> Dict[str, Any]:
    try:
        result = PowerAnalysisEngine.calculate_sample_size(
            test_type=request.test_type,
            effect_size=request.effect_size,
            alpha=request.alpha,
            power=request.power,
            groups=request.groups,
            predictors=request.predictors,
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to calculate A-Priori sample size: {str(e)}")


@router.post("/calculate-post-hoc-power", summary="Perform Post-Hoc statistical power and sensitivity curve analysis")
async def calculate_post_hoc_power_endpoint(request: PostHocPowerRequest) -> Dict[str, Any]:
    try:
        result = PowerAnalysisEngine.calculate_post_hoc_power(
            test_type=request.test_type,
            sample_size=request.sample_size,
            effect_size=request.effect_size,
            alpha=request.alpha,
            groups=request.groups,
            predictors=request.predictors,
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to calculate Post-Hoc statistical power: {str(e)}")


@router.get("/benchmarks", summary="Get standard effect size benchmarks by test family (Cohen, 1988)")
async def get_effect_benchmarks() -> Dict[str, Any]:
    return {"status": "success", "benchmarks": PowerAnalysisEngine.BENCHMARKS}
