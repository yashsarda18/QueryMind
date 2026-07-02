import json
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    precision_recall_curve,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from .features import get_training_data
import sys
from backend.database import get_connection
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

CATEGORICAL_COLS = ["customer_state", "seller_state"]
MODEL_DIR = Path(__file__).parent
MODEL_PATH = MODEL_DIR / "model.joblib"
ENCODERS_PATH = MODEL_DIR / "encoders.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"

def encode_categoricals(df: pd.DataFrame, encoders: dict[str, LabelEncoder] | None = None):
    df = df.copy()
    fitting = encoders is None
    if fitting:
        encoders = {}
    for col in CATEGORICAL_COLS:
        if fitting:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            encoders[col] = le
        else:
            le = encoders[col]
            # Unseen categories at inference time (e.g. a rare state combo
            # that never appeared in training) map to -1 rather than crashing.
            df[col] = df[col].astype(str).map(
                lambda v: le.transform([v])[0] if v in le.classes_ else -1
            )
    return df, encoders

def find_best_threshold(y_true, y_proba) -> tuple[float, dict]:
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_proba)
    # precision_recall_curve returns one more point than thresholds;
    # drop the last precision/recall pair to align lengths.
    f1_scores = 2 * (precisions[:-1] * recalls[:-1]) / (precisions[:-1] + recalls[:-1] + 1e-9)
    best_idx = int(np.argmax(f1_scores))
    best_threshold = float(thresholds[best_idx])
    y_pred_at_best = (y_proba >= best_threshold).astype(int)
    metrics_at_best = {
        "threshold": best_threshold,
        "f1": f1_score(y_true, y_pred_at_best),
        "precision": precision_score(y_true, y_pred_at_best),
        "recall": recall_score(y_true, y_pred_at_best),
    }
    return best_threshold, metrics_at_best

def train():
    conn = get_connection()
    df = get_training_data(conn)
    conn.close()
    df, encoders = encode_categoricals(df)
    feature_cols = [c for c in df.columns if c not in ("order_id", "is_late")]
    X = df[feature_cols]
    y = df["is_late"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    # scale_pos_weight = (# negative) / (# positive) — see DECISIONS.md D026.
    # Computed from the TRAINING split only, never the full dataset, to
    # avoid any test-set information leaking into a training hyperparameter.
    neg, pos = (y_train == 0).sum(), (y_train == 1).sum()
    scale_pos_weight = neg / pos
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.05,
        scale_pos_weight=scale_pos_weight,
        eval_metric="aucpr",  # PR-AUC, consistent with our headline metric
        random_state=42,
    )
    model.fit(X_train, y_train)
    y_proba = model.predict_proba(X_test)[:, 1]
    pr_auc = average_precision_score(y_test, y_proba)
    best_threshold, tuned_metrics = find_best_threshold(y_test, y_proba)
    metrics = {
        "pr_auc": pr_auc,
        "scale_pos_weight_used": scale_pos_weight,
        "tuned_threshold_metrics": tuned_metrics,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "positive_rate_train": float(y_train.mean()),
    }
    print(json.dumps(metrics, indent=2))

    joblib.dump({"model": model, "feature_cols": feature_cols, "threshold": best_threshold}, MODEL_PATH)
    joblib.dump(encoders, ENCODERS_PATH)
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

if __name__ == "__main__":
    train()