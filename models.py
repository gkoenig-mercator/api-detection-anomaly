# models.py
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class VariableType(str, Enum):
    temperature = "temperature"
    salinity = "salinity"


class ComparisonOperator(str, Enum):
    greater_than = "gt"
    less_than = "lt"
    greater_or_equal = "gte"
    less_or_equal = "lte"


class AnomalyRequest(BaseModel):
    variable: VariableType
    threshold: float
    operator: ComparisonOperator = ComparisonOperator.greater_than

    # Optional spatial filtering
    min_longitude: Optional[float] = Field(None, ge=-180, le=180)
    max_longitude: Optional[float] = Field(None, ge=-180, le=180)
    min_latitude: Optional[float] = Field(None, ge=-90, le=90)
    max_latitude: Optional[float] = Field(None, ge=-90, le=90)

    # Optional depth filtering (in meters, for temperature/salinity)
    depth: Optional[float] = Field(None, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "variable": "temperature",
                "threshold": 25.0,
                "operator": "gt",
                "min_longitude": -10.0,
                "max_longitude": 10.0,
                "min_latitude": 35.0,
                "max_latitude": 50.0,
                "depth": 0.5,
            }
        }


class AnomalyPoint(BaseModel):
    latitude: float
    longitude: float
    depth: Optional[float]
    datetime: str
    value: float


class AnomalyResponse(BaseModel):
    variable: str
    unit: str
    threshold: float
    operator: str
    forecast_range: dict
    total_anomalies: int
    anomalies: list[AnomalyPoint]
    metadata: dict
