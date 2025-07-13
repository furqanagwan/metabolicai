from fastapi import FastAPI, Depends, HTTPException, Body
from app.auth import verify_api_key, get_user_id
from app.database import (
    init_db,
    upsert_user,
    get_user,
    upsert_entry,
    get_entry,
    get_entries,
    get_user_profile,
)
from app.model import (
    predict_tdee,
    retrain_on_new_entry,
    get_feature_importance,
    tdee_trend,
)
from app.schemas import (
    Entry,
    EntryUpdate,
    UserProfile,
    TDEEPrediction,
    Analytics,
    UserProfileUpdate,  # <-- Added!
)
from typing import List, Optional
from contextlib import asynccontextmanager


# --- FastAPI App with Lifespan Event ---
@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(
    title="MetabolicAI",
    description="Track your weight, calories, and get AI-powered TDEE predictions.",
    version="1.0.0",
    lifespan=lifespan,
)


# --- User Profile Endpoints ---
@app.post("/user", tags=["User"], dependencies=[Depends(verify_api_key)])
def create_user(profile: UserProfile):
    upsert_user(profile)
    return {"msg": "Profile created/updated", "profile": profile}


@app.patch("/user", tags=["User"], dependencies=[Depends(verify_api_key)])
def patch_user(
    patch: UserProfileUpdate = Body(
        ...,
        examples={
            "default": {
                "summary": "Partial user profile update",
                "value": {"user_id": "demo", "body_fat_pct": 15.5},
            }
        },
    )
):
    profile = get_user(patch.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    update_data = profile.model_dump()
    for field in ["age", "gender", "height_cm", "body_fat_pct", "current_weight"]:
        if getattr(patch, field, None) is not None:
            update_data[field] = getattr(patch, field)
    upsert_user(UserProfile(**update_data))
    return {"msg": "Profile patched", "profile": update_data}


@app.get("/user", tags=["User"], dependencies=[Depends(verify_api_key)])
def get_user_endpoint(user_id: str = Depends(get_user_id)):
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


# --- Entry Management Endpoints ---
@app.post("/entry", tags=["Entries"], dependencies=[Depends(verify_api_key)])
def post_entry(entry: Entry, user_id: str = Depends(get_user_id)):
    upsert_entry(user_id, entry)
    retrain_on_new_entry(user_id)
    return {"msg": "Entry logged", "entry": entry}


@app.patch("/entry", tags=["Entries"], dependencies=[Depends(verify_api_key)])
def patch_entry(patch: EntryUpdate, user_id: str = Depends(get_user_id)):
    entry = get_entry(user_id, patch.date.isoformat())
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found for that date")
    update_data = entry.copy()
    if patch.weight is not None:
        update_data["weight"] = patch.weight
    if patch.calories is not None:
        update_data["calories"] = patch.calories
    upsert_entry(user_id, Entry(**update_data))
    retrain_on_new_entry(user_id)
    return {"msg": "Entry patched", "entry": update_data}


@app.get("/history", tags=["Entries"], dependencies=[Depends(verify_api_key)])
def get_history(user_id: str = Depends(get_user_id)):
    entries = get_entries(user_id)
    return {"entries": entries}


# --- TDEE Prediction ---
@app.get("/tdee", tags=["Prediction"], dependencies=[Depends(verify_api_key)])
def get_tdee(user_id: str = Depends(get_user_id)):
    profile = get_user_profile(user_id)
    entries = get_entries(user_id)
    if (
        not profile
        or not entries
        or len([e for e in entries if e["weight"] and e["calories"]]) < 3
    ):
        raise HTTPException(
            status_code=400,
            detail="Not enough data. Log at least 3 entries with both weight and calories.",
        )
    tdee = predict_tdee(user_id)
    if tdee is None:
        raise HTTPException(
            status_code=400, detail="Model not trained or not enough data."
        )
    return {"tdee": tdee}


# --- Analytics Endpoints ---
@app.get(
    "/analytics",
    response_model=Analytics,
    tags=["Analytics"],
    dependencies=[Depends(verify_api_key)],
)
def analytics(user_id: str = Depends(get_user_id)):
    entries = get_entries(user_id)
    if not entries or len(entries) < 2:
        raise HTTPException(status_code=400, detail="Not enough entries for analytics.")
    first = next((e for e in entries if e["weight"] is not None), None)
    last = next((e for e in reversed(entries) if e["weight"] is not None), None)
    weight_change = None
    if first and last and first["weight"] is not None and last["weight"] is not None:
        weight_change = round(last["weight"] - first["weight"], 2)
    avg_calories = round(
        sum(e["calories"] for e in entries if e["calories"] is not None)
        / max(1, len([e for e in entries if e["calories"] is not None])),
        2,
    )
    tdee_trend_data = tdee_trend(user_id, window=min(len(entries), 7))
    feature_imp = get_feature_importance(user_id)
    return Analytics(
        weight_change=weight_change,
        avg_calories=avg_calories,
        tdee_trend=tdee_trend_data,
        feature_importance=feature_imp,
    )


@app.get(
    "/analytics/feature-importance",
    tags=["Analytics"],
    dependencies=[Depends(verify_api_key)],
)
def feature_importance(user_id: str = Depends(get_user_id)):
    imp = get_feature_importance(user_id)
    if imp is None:
        raise HTTPException(
            status_code=400, detail="Not enough data or model not trained yet."
        )
    return imp


@app.get("/")
def root():
    return {"msg": "Welcome to MetabolicAI!"}
