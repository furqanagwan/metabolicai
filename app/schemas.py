from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import datetime


class Entry(BaseModel):
    date: datetime.date = Field(..., examples={"default": {"value": "2025-07-13"}})
    weight: Optional[float] = Field(None, examples={"default": {"value": 74.5}})
    calories: Optional[float] = Field(None, examples={"default": {"value": 2200}})


class EntryUpdate(BaseModel):
    date: datetime.date = Field(..., examples={"default": {"value": "2025-07-13"}})
    weight: Optional[float] = Field(None, examples={"default": {"value": 74.5}})
    calories: Optional[float] = Field(None, examples={"default": {"value": 2200}})


class UserProfile(BaseModel):
    user_id: str
    age: int
    gender: str
    height_cm: Optional[float] = None
    body_fat_pct: Optional[float] = None
    current_weight: Optional[float] = None


class TDEEPrediction(BaseModel):
    tdee: float


class Analytics(BaseModel):
    weight_change: Optional[float] = None
    avg_calories: Optional[float] = None
    tdee_trend: Optional[List[float]] = None
    feature_importance: Optional[Dict[str, float]] = None
