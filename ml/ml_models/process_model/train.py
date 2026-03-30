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
    os.path.join(BASE_DIR, "../../data/processed/process_dataset.csv")
)

MODEL_SAVE_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "../../ml_models/process_model/process_hybrid_final.pkl")
)

os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)


# =========================================================
# MODEL FEATURES (NO CHEAT FEATURES INSIDE RF)
# =========================================================
RF_FEATURES = [
    "cpu_percent",
    "memory_mb",
    "cpu_zscore",
    "memory_zscore",
    "parent_child_rarity",
    "cmd_entropy",
    "process_freq_5min",
    "is_known_binary"
]

ISO_FEATURES = [
    "cpu_percent",
    "memory_mb",
    "cpu_zscore",
    "memory_zscore",
    "parent_child_rarity",
    "cmd_entropy",
    "process_freq_5min",
    "is_known_binary"
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
    Deterministic suspiciousness logic for process events.
    This is NOT ML.
    """
    score = 0.0
    reasons = []

    system_score = float(row.get("system_score", 0) or 0)
    severity = float(row.get("severity", 0) or 0)
    behavioral_flag = float(row.get("behavioral_anomaly_flag", 0) or 0)
    external_connection = float(row.get("external_connection_flag", 0) or 0)
    unknown_process = float(row.get("unknown_process_flag", 0) or 0)
    sensitive_access = float(row.get("sensitive_access_flag", 0) or 0)

    cpu_z = float(row.get("cpu_zscore", 0) or 0)
    mem_z = float(row.get("memory_zscore", 0) or 0)
    parent_rarity = float(row.get("parent_child_rarity", 0) or 0)
    cmd_entropy = float(row.get("cmd_entropy", 0) or 0)

    # ----------------------------
    # Explicit suspiciousness
    # ----------------------------
    if system_score >= 4:
        score += 0.30
        reasons.append("high_system_score")
    elif system_score >= 3:
        score += 0.22
        reasons.append("elevated_system_score")
    elif system_score >= 2:
        score += 0.10

    if severity >= 2:
        score += 0.15
        reasons.append("high_severity")
    elif severity >= 1:
        score += 0.07

    if behavioral_flag == 1:
        score += 0.15
        reasons.append("behavioral_anomaly_flag")

    if external_connection == 1:
        score += 0.10
        reasons.append("external_connection_flag")

    if unknown_process == 1:
        score += 0.18
        reasons.append("unknown_process_flag")

    if sensitive_access == 1:
        score += 0.10
        reasons.append("sensitive_access_flag")

    # ----------------------------
    # Hard suspicious behavior hints
    # ----------------------------
    if parent_rarity >= 0.85:
        score += 0.10
        reasons.append("rare_parent_child")

    if cmd_entropy >= 4.5:
        score += 0.08
        reasons.append("high_cmd_entropy")

    if cpu_z >= 2.5:
        score += 0.06
        reasons.append("high_cpu_anomaly")

    if mem_z >= 2.5:
        score += 0.06
        reasons.append("high_memory_anomaly")

    return clamp01(score), reasons


# =========================================================
# TRAIN PROCESS HYBRID MODEL
# =========================================================
def train_process_hybrid_model():
    print("Loading process dataset...")
    df = pd.read_csv(DATA_PATH)
    df.columns = df.columns.str.lower().str.strip()

    if "label" not in df.columns:
        raise ValueError("❌ 'label' column missing from process dataset")

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
    # RANDOM FOREST (Recall-Oriented)
    # =====================================================
    rf_model = RandomForestClassifier(
        n_estimators=300,
        max_depth=7,
        min_samples_split=8,
        min_samples_leaf=3,
        max_features="sqrt",
        class_weight={0: 1, 1: 1.8},
        random_state=42
    )

    rf_model.fit(X_rf_train, y_train)

    rf_probs = rf_model.predict_proba(X_rf_test)[:, 1]
    rf_preds = (rf_probs >= 0.42).astype(int)

    # =====================================================
    # ISOLATION FOREST
    # Train only on normal rows
    # =====================================================
    X_iso_train_normal = X_iso_train[y_train == 0]

    iso_model = IsolationForest(
        n_estimators=250,
        contamination=0.06,
        random_state=42
    )

    iso_model.fit(X_iso_train_normal)

    iso_preds_raw = iso_model.predict(X_iso_test)
    iso_flags = np.where(iso_preds_raw == -1, 1, 0)

    iso_scores_raw = iso_model.decision_function(X_iso_test)
    iso_scores_inverted = -iso_scores_raw

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
    # Process should trust ML slightly more than file
    # =====================================================
    hybrid_score = (
        0.32 * rule_scores +
        0.44 * rf_probs +
        0.24 * iso_probs
    )

    hybrid_preds = (hybrid_score >= 0.46).astype(int)

    # Security override rules
    hybrid_preds = np.where(
        (rule_scores >= 0.60) | (rf_probs >= 0.62) | (iso_probs >= 0.64),
        1,
        hybrid_preds
    )

    # =====================================================
    # EVALUATION
    # =====================================================
    print("\n" + "=" * 72)
    print("PROCESS HYBRID MODEL - TEST PERFORMANCE")
    print("Rule Engine + RF + ISO (Recall-Oriented)")
    print("=" * 72)

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

    print(f"\n✅ Process hybrid model saved to: {MODEL_SAVE_PATH}")

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

        if rule_score >= 0.60:
            reason = "Explicit suspicious process rule triggered"
        elif rf_prob >= 0.62:
            reason = "Known suspicious process pattern detected"
        elif iso_prob >= 0.64:
            reason = "Novel abnormal process behavior detected"
        elif hybrid_score >= 0.38:
            reason = "Moderately suspicious process activity"
        else:
            reason = "Normal process activity"

        state = {
            "risk_score": round(hybrid_score, 4),
            "pred_label": pred_label,
            "events": [
                {
                    "type": "process",
                    "data": {
                        "timestamp": str(row.get("timestamp", "")),
                        "process_name": str(row.get("process_name", "unknown")),
                        "parent_process": str(row.get("parent_process", "unknown")),
                        "cpu_percent": float(row.get("cpu_percent", 0)),
                        "memory_mb": float(row.get("memory_mb", 0)),
                        "cpu_zscore": float(row.get("cpu_zscore", 0)),
                        "memory_zscore": float(row.get("memory_zscore", 0)),
                        "cmd_entropy": float(row.get("cmd_entropy", 0)),
                        "parent_child_rarity": float(row.get("parent_child_rarity", 0)),
                        "process_freq_5min": float(row.get("process_freq_5min", 0)),
                        "is_known_binary": float(row.get("is_known_binary", 0)),
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
    rf_model, iso_model, pred_df = train_process_hybrid_model()

    states = build_aggregator_states(pred_df)

    print("\n" + "=" * 72)
    print("SAMPLE AGGREGATOR STATE")
    print("=" * 72)
    print(json.dumps(states[0], indent=4))