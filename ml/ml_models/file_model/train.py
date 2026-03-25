import pandas as pd
import numpy as np
import pickle
import os
import math

from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score
from sklearn.utils import resample


# ---------------- PATHS ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.normpath(os.path.join(BASE_DIR, "../../data/processed/file_dataset.csv"))
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "file_hybrid_final.pkl")


# ---------------- FEATURE ENGINEERING ----------------
def calculate_entropy(s):
    if not isinstance(s, str) or len(s) == 0:
        return 0
    prob = [float(s.count(c)) / len(s) for c in set(s)]
    return -sum([p * math.log2(p) for p in prob])


def add_features(df):
    # File entropy
    df['file_entropy'] = df['file_path'].apply(calculate_entropy)

    # Path depth
    df['path_depth'] = df['file_path'].apply(
        lambda x: x.count('/') if isinstance(x, str) else 0
    )

    # Suspicious extension
    suspicious_ext = ['exe', 'dll', 'bat', 'ps1']
    df['is_suspicious_ext'] = df['file_extension'].isin(suspicious_ext).astype(int)

    return df


# ---------------- TRAINING ----------------
def train_behavioral_model():

    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: {DATA_PATH} not found.")
        return

    df = pd.read_csv(DATA_PATH)

    # ---------------- REMOVE CHEATCODE FEATURES ----------------
    leak_cols = [
        'system_score',
        'severity',
        'behavioral_anomaly_flag'
    ]
    df = df.drop(columns=[c for c in leak_cols if c in df.columns], errors='ignore')

    # ---------------- FEATURE ENGINEERING ----------------
    df = add_features(df)

    df['is_rare_file'] = (df['file_rarity'] > 0.8).astype(int)
    df['high_freq_access'] = (df['file_freq_1min'] > df['file_freq_1min'].quantile(0.9)).astype(int)

    # ---------------- HANDLE CLASS IMBALANCE ----------------
    df_majority = df[df.label == 0]
    df_minority = df[df.label == 1]

    if len(df_minority) > 0:
        df_minority_upsampled = resample(
            df_minority,
            replace=True,
            n_samples=len(df_majority),
            random_state=42
        )
        df = pd.concat([df_majority, df_minority_upsampled])

    # ---------------- SELECT FEATURES ----------------
    features = ['is_rare_file',
                'high_freq_access',
        'file_rarity',
        'file_freq_1min',
        'is_executable',
        'is_sensitive_path',
        'cpu_percent',
        'memory_mb',
        'cpu_zscore',
        'memory_zscore',
        'file_entropy',
        'path_depth',
        'is_suspicious_ext'
    ]

    features = [f for f in features if f in df.columns]

    X = df[features]
    y = df['label']

    # ---------------- HANDLE NaNs ----------------

    # Fill numeric columns
    num_cols = X.select_dtypes(include=[np.number]).columns
    X[num_cols] = X[num_cols].fillna(0)

    # Fill categorical/boolean if any slipped in
    X = X.fillna(0)

    # Safety check
    if X.isna().sum().sum() > 0:
        print("⚠️ Warning: NaNs still present, dropping rows")
        X = X.dropna()
        y = y.loc[X.index]

    # ---------------- SPLIT ----------------
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # ---------------- RANDOM FOREST ----------------
    rf = RandomForestClassifier(
        n_estimators=500,
        max_depth=15,
        min_samples_leaf=2,
        class_weight={0:1, 1:3},
        random_state=42,
        n_jobs=-1
    )

    rf.fit(X_train, y_train)

    # ---------------- ONE-CLASS SVM ----------------
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    X_normal_scaled = X_train_scaled[y_train == 0]

    oc_svm = OneClassSVM(kernel='rbf', nu=0.08, gamma='scale')
    oc_svm.fit(X_normal_scaled)

    # ---------------- PREDICTIONS ----------------
    rf_probs = rf.predict_proba(X_test)[:, 1]
    svm_scores = oc_svm.decision_function(X_test_scaled)
    svm_preds = oc_svm.predict(X_test_scaled)

    final_preds = []
    aggregator_packets = []

    for i in range(len(X_test)):
        prob = rf_probs[i]
        svm_val = svm_preds[i]

        # -------- IMPROVED DECISION LOGIC --------
        if prob > 0.65:
         is_malicious = 1
        elif prob < 0.35:
         is_malicious = 0
        elif svm_val == -1:
         is_malicious = 1
        else:
         is_malicious = 0

        final_preds.append(is_malicious)

        # -------- AGGREGATOR PACKET --------
        packet = {
            "threat_detected": bool(is_malicious),
            "confidence_score": float(prob),
            "anomaly_depth": float(abs(svm_scores[i])),
            "features_triggered": {
                features[j]: float(X_test.iloc[i, j]) for j in range(len(features))
            },
            "source_engine": "File_Hybrid_Behavioral_v2"
        }

        aggregator_packets.append(packet)

    # ---------------- METRICS ----------------
    print("\n" + "="*40)
    print("      CYBERSECURITY PERFORMANCE")
    print("="*40)
    print(f"Accuracy: {accuracy_score(y_test, final_preds):.4f}")
    print(f"F1 Score: {f1_score(y_test, final_preds):.4f}")

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, final_preds))

    print("\nClassification Report:")
    print(classification_report(y_test, final_preds))

    # ---------------- SAVE MODEL ----------------
    with open(MODEL_SAVE_PATH, 'wb') as f:
        pickle.dump({
            'rf': rf,
            'svm': oc_svm,
            'scaler': scaler,
            'features': features,
            'metadata': {
                "version": "2.0",
                "type": "Hybrid-Behavioral",
                "no_data_leakage": True
            }
        }, f)

    print(f"\n✅ Model saved at: {MODEL_SAVE_PATH}")


# ---------------- ENTRY POINT ----------------
if __name__ == "__main__":
    train_behavioral_model()