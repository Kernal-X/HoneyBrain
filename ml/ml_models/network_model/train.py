import os
import numpy as np
import pandas as pd
import pickle

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, precision_score, recall_score, f1_score


# =========================================================
# LOAD DATA
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.normpath(
    os.path.join(BASE_DIR, "../../data/raw/final_unified_dataset_10000.csv")
)

df = pd.read_csv(DATA_PATH)
df.columns = df.columns.str.lower().str.strip()

df = df[df["event_type"] == "network"].copy()

if "label" not in df.columns:
    raise ValueError("❌ label column missing")

print("✅ Dataset Loaded:", df.shape)


# =========================================================
# FEATURE DEFINITIONS (REAL-WORLD SAFE)
# =========================================================

# 🔹 RF = ONLY behavioral features (NO leakage)
rf_features = [
    "remote_port",
    "connection_freq_1min",
    "unique_ip_5min",
    "is_private_ip",
    "is_known_ip"
]

# 🔹 ISO = pure anomaly features
iso_features = [
    "connection_freq_1min",
    "unique_ip_5min"
]

df[rf_features] = df[rf_features].fillna(0)
df[iso_features] = df[iso_features].fillna(0)

X_rf = df[rf_features]
X_iso = df[iso_features]
y = df["label"]


# =========================================================
# TRAIN TEST SPLIT
# =========================================================
X_rf_train, X_rf_test, y_train, y_test = train_test_split(
    X_rf,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

X_iso_train = X_rf_train[iso_features]
X_iso_test = X_rf_test[iso_features]


# =========================================================
# RULE ENGINE (ALL DOMAIN SIGNALS HERE)
# =========================================================
def compute_network_rule_score(row):
    score = 0.0
    reasons = []

    # Strong signals moved here
    if row.get("severity", 0) >= 2:
        score += 0.20
        reasons.append("high_severity")

    if row.get("system_score", 0) >= 3:
        score += 0.20
        reasons.append("high_system_score")

    if row.get("behavioral_anomaly_flag", 0) == 1:
        score += 0.20
        reasons.append("behavioral_flag")

    if row.get("external_connection_flag", 0) == 1:
        score += 0.10
        reasons.append("external_connection")

    if row.get("is_known_ip", 1) == 0:
        score += 0.15
        reasons.append("unknown_ip")

    if row.get("port_risk", 0) >= 0.7:
        score += 0.15
        reasons.append("high_risk_port")

    if row.get("connection_freq_1min", 0) > 20:
        score += 0.10
        reasons.append("high_connection_rate")

    if row.get("unique_ip_5min", 0) > 15:
        score += 0.10
        reasons.append("ip_scanning")

    return min(score, 1.0), reasons


# =========================================================
# RANDOM FOREST
# =========================================================
print("\n🚀 Training Random Forest...")

rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_rf_train, y_train)

rf_probs = rf_model.predict_proba(X_rf_test)[:, 1]
rf_preds = (rf_probs >= 0.5).astype(int)


# =========================================================
# ISOLATION FOREST
# =========================================================
print("🚀 Training Isolation Forest...")

iso_model = IsolationForest(contamination=0.1, random_state=42)
iso_model.fit(X_iso_train)

iso_preds_raw = iso_model.predict(X_iso_test)
iso_flags = (iso_preds_raw == -1).astype(int)

iso_scores_raw = iso_model.decision_function(X_iso_test)
iso_scores_inverted = -iso_scores_raw

iso_min = iso_scores_inverted.min()
iso_max = iso_scores_inverted.max()

iso_probs = (iso_scores_inverted - iso_min) / (iso_max - iso_min + 1e-8)


# =========================================================
# RULE ENGINE
# =========================================================
print("🚀 Computing Rule Scores...")

df_test_full = df.loc[X_rf_test.index]  # full row access

rule_scores = []
rule_reasons = []

for _, row in df_test_full.iterrows():
    s, r = compute_network_rule_score(row)
    rule_scores.append(s)
    rule_reasons.append(r)

rule_scores = np.array(rule_scores)


# =========================================================
# HYBRID FUSION (REBALANCED)
# =========================================================
print("🚀 Computing Hybrid Score...")

hybrid_score = (
    0.45 * rule_scores +
    0.30 * rf_probs +
    0.25 * iso_probs
)

hybrid_preds = (hybrid_score >= 0.4).astype(int)

# Override logic
hybrid_preds = np.where(
    (rule_scores >= 0.6) |
    (rf_probs >= 0.8) |
    (iso_probs >= 0.7),
    1,
    hybrid_preds
)
# RESULTS
# =========================================================
print("\n" + "=" * 70)
print("NETWORK HYBRID MODEL RESULTS")
print("=" * 70)

print("\n--- Random Forest Only ---")
print(classification_report(y_test, rf_preds, digits=4))

print("\n--- Hybrid Model ---")
print(classification_report(y_test, hybrid_preds, digits=4))

print("\nConfusion Matrix (Hybrid):")
print(confusion_matrix(y_test, hybrid_preds))

print("\nSummary Metrics:")
print(f"Accuracy : {accuracy_score(y_test, hybrid_preds):.4f}")
print(f"Precision: {precision_score(y_test, hybrid_preds):.4f}")
print(f"Recall   : {recall_score(y_test, hybrid_preds):.4f}")
print(f"F1 Score : {f1_score(y_test, hybrid_preds):.4f}")


# =========================================================
# RESULTS DATAFRAME
# =========================================================
df_results = df_test_full.copy()

df_results["rf_prob"] = rf_probs
df_results["iso_prob"] = iso_probs
df_results["rule_score"] = rule_scores
df_results["hybrid_score"] = hybrid_score
df_results["hybrid_pred"] = hybrid_preds

print("\n🔝 Top 10 Suspicious Network Events:")
print(
    df_results.sort_values("hybrid_score", ascending=False)
    .head(10)[
        [
            "remote_port",
            "rule_score",
            "rf_prob",
            "iso_prob",
            "hybrid_score",
            "hybrid_pred"
        ]
    ]
)


# =========================================================
# SAVE MODEL
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "network_hybrid_model.pkl")

with open(MODEL_PATH, "wb") as f:
    pickle.dump({
        "rf_model": rf_model,
        "iso_model": iso_model,
        "rf_features": rf_features,
        "iso_features": iso_features
    }, f)

print(f"\n✅ Model saved at: {MODEL_PATH}")