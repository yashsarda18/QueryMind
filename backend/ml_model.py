from pathlib import Path
import joblib
import pandas as pd

MODEL_DIR = Path(__file__).parent.parent / "ml"

RISK_BUCKETS = [
    (0.3, "green"),
    (0.6, "amber"),
    (1.01, "red"),  # 1.01 so a proba of exactly 1.0 still falls in "red"
]

class DelayRiskModel:
    def __init__(self):
        bundle = joblib.load(MODEL_DIR / "model.joblib")
        self.model = bundle["model"]
        self.feature_cols = bundle["feature_cols"]
        self.threshold = bundle["threshold"]  # tuned threshold from train.py
        self.encoders = joblib.load(MODEL_DIR / "encoders.joblib")
    def _encode(self, features: dict) -> pd.DataFrame:
        df = pd.DataFrame([features])
        for col, le in self.encoders.items():
            val = str(df.at[0, col])
            df[col] = le.transform([val])[0] if val in le.classes_ else -1
        return df[self.feature_cols]
    def _bucket(self, proba: float) -> str:
        for upper_bound, label in RISK_BUCKETS:
            if proba < upper_bound:
                return label
        return "red"
    def predict(self, features: dict) -> dict:
        X = self._encode(features)
        proba = float(self.model.predict_proba(X)[0, 1])
        return {
            "risk_score": round(proba, 4),
            "is_late_predicted": proba >= self.threshold,
            "risk_badge": self._bucket(proba),
        }
        
_model_instance: DelayRiskModel | None = None
def get_model() -> DelayRiskModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = DelayRiskModel()
    return _model_instance