import os
import numpy as np
import pandas as pd
import joblib
from xgboost import XGBRegressor
from sklearn.linear_model import LinearRegression
from app.database import get_entries_df, get_user_profile
from typing import Optional, Dict, Any


def get_model_path(user_id: str):
    os.makedirs("models", exist_ok=True)
    return os.path.join("models", f"{user_id}_model.pkl")


def build_features(df: pd.DataFrame, user_profile: dict) -> pd.DataFrame:
    df = df.sort_values("date").copy()
    df["weight_lag1"] = df["weight"].shift(1)
    df["calories_lag1"] = df["calories"].shift(1)
    df["weight_ma3"] = df["weight"].rolling(window=3, min_periods=1).mean()
    df["calories_ma3"] = df["calories"].rolling(window=3, min_periods=1).mean()
    for col in ["weight_lag1", "calories_lag1", "weight_ma3", "calories_ma3"]:
        df[col] = df[col].fillna(df[col].mean())
    if user_profile:
        df["age"] = user_profile.get("age", 30)
        df["gender"] = 1 if user_profile.get("gender") == "male" else 0
        df["height_cm"] = user_profile.get("height_cm", 170)
        df["body_fat_pct"] = user_profile.get("body_fat_pct", np.nan)
        df["current_weight"] = user_profile.get("current_weight", np.nan)
    return df


def train_and_save(user_id: str):
    df = get_entries_df(user_id)
    profile = get_user_profile(user_id)
    if df is None or df.shape[0] < 6 or not profile:
        return None, "not_enough_data"
    df = build_features(df, profile)
    X = df[
        [
            "weight",
            "calories",
            "weight_lag1",
            "calories_lag1",
            "weight_ma3",
            "calories_ma3",
            "age",
            "gender",
            "height_cm",
            "body_fat_pct",
            "current_weight",
        ]
    ].fillna(0)
    y = df["calories"]  # Target is calories for TDEE estimation

    # XGBoost if enough data, else fallback
    if len(df) >= 8:
        model = XGBRegressor(n_estimators=25, max_depth=3, random_state=42)
    else:
        model = LinearRegression()
    model.fit(X, y)
    joblib.dump(model, get_model_path(user_id))
    return model, "ok"


def load_model(user_id: str):
    path = get_model_path(user_id)
    if os.path.exists(path):
        return joblib.load(path)
    return None


def predict_tdee(user_id: str) -> Optional[float]:
    model = load_model(user_id)
    df = get_entries_df(user_id)
    profile = get_user_profile(user_id)
    if model is None or df is None or profile is None or df.empty:
        return None
    df = build_features(df, profile)
    X = df[
        [
            "weight",
            "calories",
            "weight_lag1",
            "calories_lag1",
            "weight_ma3",
            "calories_ma3",
            "age",
            "gender",
            "height_cm",
            "body_fat_pct",
            "current_weight",
        ]
    ].fillna(0)
    latest = X.iloc[[-1]]
    pred = float(model.predict(latest)[0])
    return round(pred, 2)


def get_feature_importance(user_id: str) -> Dict[str, float]:
    model = load_model(user_id)
    feature_names = [
        "weight",
        "calories",
        "weight_lag1",
        "calories_lag1",
        "weight_ma3",
        "calories_ma3",
        "age",
        "gender",
        "height_cm",
        "body_fat_pct",
        "current_weight",
    ]
    if hasattr(model, "feature_importances_"):
        fi = dict(zip(feature_names, model.feature_importances_))
        return {k: round(float(v), 3) for k, v in fi.items()}
    elif hasattr(model, "coef_"):
        coefs = dict(zip(feature_names, np.abs(model.coef_)))
        return {k: round(float(v), 3) for k, v in coefs.items()}
    else:
        return {}


def tdee_trend(user_id: str, window=5) -> Any:
    model = load_model(user_id)
    df = get_entries_df(user_id)
    profile = get_user_profile(user_id)
    if model is None or df is None or profile is None or df.empty:
        return []
    df = build_features(df, profile)
    X = df[
        [
            "weight",
            "calories",
            "weight_lag1",
            "calories_lag1",
            "weight_ma3",
            "calories_ma3",
            "age",
            "gender",
            "height_cm",
            "body_fat_pct",
            "current_weight",
        ]
    ].fillna(0)
    preds = model.predict(X)
    return list(map(lambda x: round(float(x), 2), preds[-window:]))


def retrain_on_new_entry(user_id: str):
    # Retrain model after every new or updated entry
    model, status = train_and_save(user_id)
    return status
