import pandas as pd
import os
import pickle
import numpy as np

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score


# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.normpath(os.path.join(BASE_DIR, "../../data/processed/process_dataset.csv"))
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "process_final_model.pkl")


def train_process_model():

    # ---------------- LOAD ----------------
    df = pd.read_csv(DATA_PATH)

    # ---------------- REMOVE LEAKAGE ----------------
    df = df.drop(columns=[
        'system_score',
        'severity',
        'behavioral_anomaly_flag'
    ], errors='ignore')

    # ---------------- CLEAN ----------------
    df = df.fillna(0)

    # ---------------- LABEL CREATION ----------------
    df['label'] = (
        (df['unknown_process_flag'] == 1) |
        (df['external_connection_flag'] == 1) |
        ((df['cmd_entropy'] > 4) & (df['is_known_binary'] == 0)) |
        (df['parent_child_rarity'] > 0.9)
    ).astype(int)

    # ---------------- FEATURE ENGINEERING ----------------

    # Core behavior
    df['resource_spike'] = np.sqrt(
        df['cpu_zscore']**2 + df['memory_zscore']**2
    )

    # Activity spike
    df['burst_flag'] = (
        df['process_freq_5min'] > df['process_freq_5min'].median()
    ).astype(int)

    # Behavior + trust interaction
    df['behavior_risk'] = df['resource_spike'] * (1 - df['is_known_binary'])

    # Frequency + entropy (attack repetition)
    df['freq_entropy_combo'] = df['process_freq_5min'] * df['cmd_entropy']

    # Stealth attack detection
    df['stealth_risk'] = (
        (df['is_known_binary'] == 0) &
        (df['resource_spike'] < df['resource_spike'].median())
    ).astype(int)

    # Extreme anomaly detector
    df['combined_anomaly'] = (
        (abs(df['cpu_zscore']) > 2).astype(int) +
        (abs(df['memory_zscore']) > 2).astype(int)
    )


    # ---------------- FINAL FEATURE SET ----------------
    features = [
        'resource_spike',
        'process_freq_5min',
        'is_known_binary',

        # 🔥 alignment features (critical)
        'unknown_process_flag',
        
    'external_connection_flag',
        'cmd_entropy',

        # engineered features
        'behavior_risk',
        'freq_entropy_combo',
        'stealth_risk',
        'combined_anomaly'
    ]

    features = [f for f in features if f in df.columns]

    print("✅ Features used:", features)

    X = df[features]
    y = df['label']

    # ---------------- SPLIT ----------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # ---------------- MODEL ----------------
    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=10,
        min_samples_leaf=4,
        class_weight={0:1, 1:2},
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    # ---------------- PREDICTION ----------------
    probs = model.predict_proba(X_test)[:, 1]

    # Slightly recall-focused threshold
    y_pred = (probs > 0.30).astype(int)

    # ---------------- METRICS ----------------
    print("\n" + "="*40)
    print("      🚀 FINAL PROCESS MODEL")
    print("="*40)

    print(f"\nAccuracy: {accuracy_score(y_test, y_pred):.4f}")

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # ---------------- FEATURE IMPORTANCE ----------------
    importances = pd.Series(model.feature_importances_, index=features)
    print("\nTop Features:")
    print(importances.sort_values(ascending=False))

    # ---------------- SAVE ----------------
    with open(MODEL_SAVE_PATH, 'wb') as f:
        pickle.dump({
            'model': model,
            'features': features
        }, f)

    print(f"\n✅ Model saved at: {MODEL_SAVE_PATH}")


# ---------------- ENTRY ----------------
if __name__ == "__main__":
    train_process_model()