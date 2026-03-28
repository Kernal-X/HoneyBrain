import os
import json
import pickle
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


# =========================================================
# PATHS
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "../../data/processed/file_dataset.csv")
)

MODEL_SAVE_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "../../ml_models/file_model/file_hybrid_final.pkl")
)

os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)


# =========================================================
# MODEL FEATURES (NO CHEAT FEATURES INSIDE RF)
# =========================================================
RF_FEATURES = [
    "is_sensitive_path",
    "is_executable",
    "file_freq_1min",
    "file_rarity",
    "cpu_zscore",
    "memory_zscore",
    "hour",
    "is_off_hours"
]

ISO_FEATURES = [
    "sensitive_access_flag",
    "is_sensitive_path",
    "is_executable",
    "file_freq_1min",
    "file_rarity",
    "cpu_zscore",
    "memory_zscore",
    "hour",
    "is_off_hours"
]


# =========================================================
# HELPERS
# =========================================================
def existing_features(df, cols):
    return [c for c in cols if c in df.columns]


def safe_fill(df, cols):
    df = df.copy()
    for col in cols:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    return df


def clamp01(x):
    return max(0.0, min(1.0, float(x)))


# =========================================================
# RULE / CHEAT-CODE ENGINE
# =========================================================
def compute_rule_score(row):
    """
    Deterministic security heuristic score.
    This is NOT ML. This is your explicit 'known suspiciousness' logic.
    """

    score = 0.0
    reasons = []

    system_score = float(row.get("system_score", 0) or 0)
    severity = float(row.get("severity", 0) or 0)
    behavioral_flag = float(row.get("behavioral_anomaly_flag", 0) or 0)
    sensitive_access = float(row.get("sensitive_access_flag", 0) or 0)

    # ----------------------------
    # System score contribution
    # ----------------------------
    if system_score >= 4:
        score += 0.45
        reasons.append("high_system_score")
    elif system_score >= 3:
        score += 0.30
        reasons.append("elevated_system_score")
    elif system_score >= 2:
        score += 0.15

    # ----------------------------
    # Severity contribution
    # ----------------------------
    if severity >= 2:
        score += 0.20
        reasons.append("high_severity")
    elif severity >= 1:
        score += 0.10

    # ----------------------------
    # Behavioral anomaly contribution
    # ----------------------------
    if behavioral_flag == 1:
        score += 0.20
        reasons.append("behavioral_anomaly_flag")

    # ----------------------------
    # Sensitive access contribution
    # ----------------------------
    if sensitive_access == 1:
        score += 0.15
        reasons.append("sensitive_access_flag")

    return clamp01(score), reasons


# =========================================================
# TRAIN FILE HYBRID MODEL
# =========================================================
def train_file_hybrid_model():
    print("Loading file dataset...")
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.lower().str.strip()

    if "label" not in df.columns:
        raise ValueError("❌ 'label' column missing from file dataset")

    rf_features = existing_features(df, RF_FEATURES)
    iso_features = existing_features(df, ISO_FEATURES)

    print("\nRF Features:", rf_features)
    print("ISO Features:", iso_features)

    df = safe_fill(df, list(set(rf_features + iso_features)))

    X_rf = df[rf_features]
    X_iso = df[iso_features]
    y = df["label"]

    # =====================================================
    # TRAIN / TEST SPLIT
    # =====================================================
    X_rf_train, X_rf_test, X_iso_train, X_iso_test, y_train, y_test, train_idx, test_idx = train_test_split(
        X_rf, X_iso, y, df.index,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # =====================================================
    # RANDOM FOREST
    # Recall-oriented settings
    # =====================================================
    rf_model = RandomForestClassifier(
        n_estimators=250,
        max_depth=6,
        min_samples_split=10,
        min_samples_leaf=4,
        max_features="sqrt",
        class_weight={0: 1, 1: 2.2},   # bias toward catching attacks
        random_state=42
    )

    rf_model.fit(X_rf_train, y_train)

    # Lower threshold to improve recall
    rf_probs = rf_model.predict_proba(X_rf_test)[:, 1]
    rf_preds = (rf_probs >= 0.38).astype(int)

    # =====================================================
    # ISOLATION FOREST
    # Train only on normal rows
    # =====================================================
    X_iso_train_normal = X_iso_train[y_train == 0]

    iso_model = IsolationForest(
        n_estimators=200,
        contamination=0.12,  # more anomaly sensitivity
        random_state=42
    )

    iso_model.fit(X_iso_train_normal)

    iso_preds_raw = iso_model.predict(X_iso_test)
    iso_flags = np.where(iso_preds_raw == -1, 1, 0)

    iso_scores_raw = iso_model.decision_function(X_iso_test)
    iso_scores_inverted = -iso_scores_raw  # higher = more suspicious

    iso_min = iso_scores_inverted.min()
    iso_max = iso_scores_inverted.max()

    if iso_max - iso_min == 0:
        iso_probs = np.zeros_like(iso_scores_inverted)
    else:
        iso_probs = (iso_scores_inverted - iso_min) / (iso_max - iso_min)

    # =====================================================
    # RULE ENGINE ON TEST SET
    # =====================================================
    test_rows = df.loc[test_idx].copy().reset_index(drop=True)

    rule_scores = []
    rule_reasons = []

    for _, row in test_rows.iterrows():
        r_score, r_reason = compute_rule_score(row)
        rule_scores.append(r_score)
        rule_reasons.append(r_reason)

    rule_scores = np.array(rule_scores)

    # =====================================================
    # FINAL HYBRID FUSION
    # Recall-oriented fusion
    # =====================================================
    hybrid_score = (
        0.40 * rule_scores +
        0.35 * rf_probs +
        0.25 * iso_probs
    )

    # Lower threshold for higher recall
    hybrid_preds = (hybrid_score >= 0.42).astype(int)

    # Security override rules
    hybrid_preds = np.where(
        (rule_scores >= 0.75) | (rf_probs >= 0.72) | (iso_probs >= 0.88),
        1,
        hybrid_preds
    )

    # =====================================================
    # EVALUATION
    # =====================================================
    print("\n" + "=" * 70)
    print("FILE HYBRID MODEL - TEST PERFORMANCE")
    print("Rule Engine + RF + ISO (Recall-Oriented)")
    print("=" * 70)

    print("\n--- Random Forest Only ---")
    print(classification_report(y_test, rf_preds, digits=4))

    print("\n--- Hybrid Model (Rule + RF + ISO) ---")
    print(classification_report(y_test, hybrid_preds, digits=4))

    print("\nConfusion Matrix (Hybrid):")
    print(confusion_matrix(y_test, hybrid_preds))

    print("\nTop RF Feature Importances:")
    importances = pd.Series(
        rf_model.feature_importances_,
        index=rf_features
    ).sort_values(ascending=False)
    print(importances)

    # =====================================================
    # SAVE MODEL
    # =====================================================
    with open(MODEL_SAVE_PATH, "wb") as f:
        pickle.dump({
            "rf_model": rf_model,
            "iso_model": iso_model,
            "rf_features": rf_features,
            "iso_features": iso_features
        }, f)

    print(f"\n✅ File hybrid model saved to: {MODEL_SAVE_PATH}")

    # =====================================================
    # BUILD TEST PREDICTION DF
    # =====================================================
    pred_df = test_rows.copy()
    pred_df["rf_prob"] = rf_probs
    pred_df["iso_prob"] = iso_probs
    pred_df["iso_flag"] = iso_flags
    pred_df["rule_score"] = rule_scores
    pred_df["rule_reasons"] = [",".join(r) if r else "none" for r in rule_reasons]
    pred_df["hybrid_score"] = hybrid_score
    pred_df["hybrid_pred"] = hybrid_preds

    return rf_model, iso_model, pred_df


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
            reason = "Explicit suspicious file-event rule triggered"
        elif rf_prob >= 0.72:
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
                        "process_name": str(row.get("process_name", "unknown")),
                        "parent_process": str(row.get("parent_process", "unknown")),
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
# MAIN
# =========================================================
if __name__ == "__main__":
    rf_model, iso_model, pred_df = train_file_hybrid_model()

    states = build_aggregator_states(pred_df)

    print("\n" + "=" * 70)
    print("SAMPLE AGGREGATOR STATE")
    print("=" * 70)
    print(json.dumps(states[0], indent=4))