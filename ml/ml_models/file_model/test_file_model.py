import os
import json
import pickle
import numpy as np
import pandas as pd

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)


# =========================================================
# PATHS
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "../../data/processed/file_dataset.csv")
)

MODEL_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "../../ml_models/file_model/file_hybrid_final.pkl")
)


# =========================================================
# HELPERS
# =========================================================
def clamp01(x):
    return max(0.0, min(1.0, float(x)))


def safe_fill(df, cols):
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    return df


# =========================================================
# SAME RULE ENGINE AS TRAINING
# =========================================================
def compute_rule_score(row):
    score = 0.0
    reasons = []

    system_score = float(row.get("system_score", 0) or 0)
    severity = float(row.get("severity", 0) or 0)
    behavioral_flag = float(row.get("behavioral_anomaly_flag", 0) or 0)
    sensitive_access = float(row.get("sensitive_access_flag", 0) or 0)

    is_sensitive_path = float(row.get("is_sensitive_path", 0) or 0)
    is_executable = float(row.get("is_executable", 0) or 0)
    file_freq = float(row.get("file_freq_1min", 0) or 0)
    file_rarity = float(row.get("file_rarity", 0) or 0)

    if system_score >= 4:
        score += 0.28
        reasons.append("high_system_score")
    elif system_score >= 3:
        score += 0.18
        reasons.append("elevated_system_score")
    elif system_score >= 2:
        score += 0.08

    if severity >= 2:
        score += 0.14
        reasons.append("high_severity")
    elif severity >= 1:
        score += 0.06

    if behavioral_flag == 1:
        score += 0.15
        reasons.append("behavioral_anomaly_flag")

    if sensitive_access == 1:
        score += 0.16
        reasons.append("sensitive_access_flag")

    if is_sensitive_path == 1:
        score += 0.12
        reasons.append("sensitive_file_path")

    if is_executable == 1:
        score += 0.08
        reasons.append("executable_file_event")

    if file_freq >= 2.0:
        score += 0.05
        reasons.append("high_file_frequency")

    if file_rarity >= 0.85:
        score += 0.10
        reasons.append("rare_file_behavior")

    return clamp01(score), reasons


# =========================================================
# AGGREGATOR-READY STATE GENERATION
# =========================================================
def build_aggregator_states(pred_df):
    states = []

    for _, row in pred_df.iterrows():
        rf_prob = float(row["rf_prob"])
        iso_prob = float(row["iso_prob"])
        rule_score = float(row["rule_score"])
        hybrid_score = float(row["hybrid_score"])
        pred_label = int(row["hybrid_pred"])
        rule_reasons = str(row.get("rule_reasons", "none"))

        if rule_score >= 0.75:
            reason = "Explicit suspicious file rule triggered"
        elif rf_prob >= 0.70:
            reason = "Known suspicious file pattern detected"
        elif iso_prob >= 0.88:
            reason = "Novel abnormal file behavior detected"
        elif hybrid_score >= 0.42:
            reason = "Moderately suspicious file activity"
        else:
            reason = "Normal file activity"

        state = {
            "risk_score": round(hybrid_score, 4),
            "pred_label": pred_label,
            "events": [
                {
                    "type": "file",
                    "data": {
                        "timestamp": str(row.get("timestamp", "")),
                        "file_path": str(row.get("file_path", "unknown")),
                        "file_action": str(row.get("file_action", "unknown")),
                        "file_extension": str(row.get("file_extension", "unknown")),
                        "is_sensitive_path": float(row.get("is_sensitive_path", 0)),
                        "is_executable": float(row.get("is_executable", 0)),
                        "file_freq_1min": float(row.get("file_freq_1min", 0)),
                        "file_rarity": float(row.get("file_rarity", 0)),
                        "process_name": str(row.get("process_name", "unknown")),
                        "parent_process": str(row.get("parent_process", "unknown")),
                        "cpu_percent": float(row.get("cpu_percent", 0)),
                        "memory_mb": float(row.get("memory_mb", 0)),
                        "cpu_zscore": float(row.get("cpu_zscore", 0)),
                        "memory_zscore": float(row.get("memory_zscore", 0)),
                        "rule_score": round(rule_score, 4),
                        "rule_reasons": rule_reasons,
                        "rf_prob": round(rf_prob, 4),
                        "iso_prob": round(iso_prob, 4),
                        "iso_flag": int(row.get("iso_flag", 0)),
                        "hybrid_score": round(hybrid_score, 4),
                        "reason": reason
                    }
                }
            ]
        }

        states.append(state)

    return states


# =========================================================
# MAIN TEST FUNCTION
# =========================================================
def test_file_hybrid_model():
    print("Loading file dataset...")
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.lower().str.strip()

    if "label" not in df.columns:
        raise ValueError("❌ 'label' column missing from dataset")

    print("Loading saved model...")
    with open(MODEL_PATH, "rb") as f:
        bundle = pickle.load(f)

    rf_model = bundle["rf_model"]
    iso_model = bundle["iso_model"]
    rf_features = bundle["rf_features"]
    iso_features = bundle["iso_features"]

    print("\nRF Features Loaded:", rf_features)
    print("ISO Features Loaded:", iso_features)

    df = safe_fill(df, list(set(rf_features + iso_features)))

    X_rf = df[rf_features]
    X_iso = df[iso_features]
    y = df["label"]

    # =====================================================
    # RF PREDICTIONS
    # =====================================================
    rf_probs = rf_model.predict_proba(X_rf)[:, 1]
    rf_preds = (rf_probs >= 0.38).astype(int)

    # =====================================================
    # ISO PREDICTIONS
    # =====================================================
    iso_preds_raw = iso_model.predict(X_iso)
    iso_flags = np.where(iso_preds_raw == -1, 1, 0)

    iso_scores_raw = iso_model.decision_function(X_iso)
    iso_scores_inverted = -iso_scores_raw

    iso_min = iso_scores_inverted.min()
    iso_max = iso_scores_inverted.max()

    if iso_max - iso_min == 0:
        iso_probs = np.zeros_like(iso_scores_inverted)
    else:
        iso_probs = (iso_scores_inverted - iso_min) / (iso_max - iso_min)

    # =====================================================
    # RULE ENGINE
    # =====================================================
    rule_scores = []
    rule_reasons = []

    for _, row in df.iterrows():
        r_score, r_reason = compute_rule_score(row)
        rule_scores.append(r_score)
        rule_reasons.append(r_reason)

    rule_scores = np.array(rule_scores)

    # =====================================================
    # HYBRID FUSION
    # =====================================================
    hybrid_score = (
        0.34 * rule_scores +
        0.42 * rf_probs +
        0.24 * iso_probs
    )

    hybrid_preds = (hybrid_score >= 0.42).astype(int)

    hybrid_preds = np.where(
        (rule_scores >= 0.75) | (rf_probs >= 0.70) | (iso_probs >= 0.88),
        1,
        hybrid_preds
    )

    # =====================================================
    # RESULTS
    # =====================================================
    print("\n" + "=" * 72)
    print("FILE HYBRID MODEL - FULL DATASET TEST")
    print("=" * 72)

    print("\n--- Random Forest Only ---")
    print(classification_report(y, rf_preds, digits=4))

    print("\n--- Hybrid Model (Rule + RF + ISO) ---")
    print(classification_report(y, hybrid_preds, digits=4))

    print("\nConfusion Matrix (Hybrid):")
    print(confusion_matrix(y, hybrid_preds))

    print("\nSummary Metrics (Hybrid):")
    print(f"Accuracy : {accuracy_score(y, hybrid_preds):.4f}")
    print(f"Precision: {precision_score(y, hybrid_preds):.4f}")
    print(f"Recall   : {recall_score(y, hybrid_preds):.4f}")
    print(f"F1 Score : {f1_score(y, hybrid_preds):.4f}")

    # =====================================================
    # BUILD PREDICTION DATAFRAME
    # =====================================================
    pred_df = df.copy()
    pred_df["rf_prob"] = rf_probs
    pred_df["iso_prob"] = iso_probs
    pred_df["iso_flag"] = iso_flags
    pred_df["rule_score"] = rule_scores
    pred_df["rule_reasons"] = [",".join(r) if r else "none" for r in rule_reasons]
    pred_df["hybrid_score"] = hybrid_score
    pred_df["hybrid_pred"] = hybrid_preds

    # =====================================================
    # SHOW TOP SUSPICIOUS EVENTS
    # =====================================================
    print("\n" + "=" * 72)
    print("TOP 10 MOST SUSPICIOUS FILE EVENTS")
    print("=" * 72)

    suspicious_cols = [
        "timestamp",
        "file_path",
        "file_action",
        "file_extension",
        "process_name",
        "label",
        "rule_score",
        "rf_prob",
        "iso_prob",
        "hybrid_score",
        "hybrid_pred"
    ]

    suspicious_cols = [c for c in suspicious_cols if c in pred_df.columns]

    top_suspicious = pred_df.sort_values("hybrid_score", ascending=False).head(10)
    print(top_suspicious[suspicious_cols].to_string(index=False))

    # =====================================================
    # AGGREGATOR STATES
    # =====================================================
    states = build_aggregator_states(pred_df)

    print("\n" + "=" * 72)
    print("SAMPLE AGGREGATOR STATE")
    print("=" * 72)
    print(json.dumps(states[0], indent=4))

    return pred_df, states


# =========================================================
# ENTRY POINT
# =========================================================
if __name__ == "__main__":
    pred_df, states = test_file_hybrid_model()