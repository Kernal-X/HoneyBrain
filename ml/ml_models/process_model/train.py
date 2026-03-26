import pandas as pd
import os
import pickle
import numpy as np
import json

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.normpath(os.path.join(BASE_DIR, "../../data/processed/process_dataset.csv"))
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "process_final_model.pkl")

def train_process_model():
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: {DATA_PATH} not found.")
        return

    # ---------------- LOAD ----------------
    df = pd.read_csv(DATA_PATH)

    # ---------------- REMOVE LEAKAGE ----------------
    df = df.drop(columns=['system_score', 'severity', 'behavioral_anomaly_flag'], errors='ignore')

    # ---------------- CLEAN ----------------
    df = df.fillna(0)

    # ---------------- LABEL CREATION ----------------
    df['label'] = (
        (df['unknown_process_flag'] == 1) |
        (df['external_connection_flag'] == 1) |
        ((df.get('cmd_entropy', 0) > 4) & (df.get('is_known_binary', 0) == 0)) |
        (df.get('parent_child_rarity', 0) > 0.9)
    ).astype(int)

    # ---------------- FEATURE ENGINEERING ----------------
    df['resource_spike'] = np.sqrt(df.get('cpu_zscore', 0)**2 + df.get('memory_zscore', 0)**2)
    df['burst_flag'] = (df.get('process_freq_5min', 0) > df['process_freq_5min'].median()).astype(int)
    df['behavior_risk'] = df['resource_spike'] * (1 - df.get('is_known_binary', 0))
    df['freq_entropy_combo'] = df.get('process_freq_5min', 0) * df.get('cmd_entropy', 0)
    df['stealth_risk'] = ((df.get('is_known_binary', 0) == 0) & (df['resource_spike'] < df['resource_spike'].median())).astype(int)
    df['combined_anomaly'] = (abs(df.get('cpu_zscore', 0)) > 2).astype(int) + (abs(df.get('memory_zscore', 0)) > 2).astype(int)

    # ---------------- FINAL FEATURE SET ----------------
    features = [
        'resource_spike', 'process_freq_5min', 'is_known_binary',
        'unknown_process_flag', 'external_connection_flag', 'cmd_entropy',
        'behavior_risk', 'freq_entropy_combo', 'stealth_risk', 'combined_anomaly'
    ]
    features = [f for f in features if f in df.columns]

    # ---------------- SPLIT ----------------
    # We keep the full dataframe (train_df/test_df) so we can access non-feature columns for the aggregator
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label'])

    X_train = train_df[features]
    y_train = train_df['label']
    X_test = test_df[features]
    y_test = test_df['label']

    # ---------------- MODEL ----------------
    model = RandomForestClassifier(
        n_estimators=500, max_depth=10, min_samples_leaf=4,
        class_weight={0:1, 1:10}, random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)

    # ---------------- HYBRID INFERENCE & STATE GENERATION ----------------
    probs = model.predict_proba(X_test)[:, 1]
    
    aggregator_ready_outputs = []
    final_preds = []

    for i in range(len(X_test)):
        risk_score = float(probs[i])
        final_preds.append(1 if risk_score > 0.30 else 0)

        # Access original row metadata
        raw_row = test_df.iloc[i]
        
        # Dynamic Reasoning for the Aggregator
        reason = "Normal process behavior"
        if risk_score > 0.30:
            if raw_row.get('external_connection_flag') == 1:
                reason = "Suspicious external network connection"
            elif raw_row.get('resource_spike', 0) > 3:
                reason = "Abnormal resource consumption spike"
            elif raw_row.get('cmd_entropy', 0) > 5:
                reason = "Highly obfuscated command line arguments"
            else:
                reason = "Unusual parent-child relationship or unknown binary"

        # ---------------- CONSTRUCT STATE SCHEMA ----------------
        state = {
            "risk_score": round(risk_score, 4),
            "events": [
                {
                    "type": "process",
                    "data": {
                        "process_name": str(raw_row.get('process_name', 'unknown.exe')),
                        "parent_process": str(raw_row.get('parent_process', 'unknown')),
                        "cpu_percent": float(raw_row.get('cpu_percent', 0)),
                        "memory_mb": float(raw_row.get('memory_usage_mb', 0)),
                        "reason": reason
                    }
                }
            ]
        }
        aggregator_ready_outputs.append(state)

    # ---------------- PREVIEW FOR AGGREGATOR ----------------
    print("\n✅ Example Output for Aggregator:")
    print(json.dumps(aggregator_ready_outputs[0], indent=4))

    # ---------------- METRICS ----------------
    print("\n" + "="*40)
    print("      🚀 FINAL PROCESS MODEL")
    print("="*40)
    print(f"Accuracy: {accuracy_score(y_test, final_preds):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, final_preds))

    # ---------------- SAVE ----------------
    with open(MODEL_SAVE_PATH, 'wb') as f:
        pickle.dump({'model': model, 'features': features}, f)

    print(f"\n✅ Model saved at: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_process_model()