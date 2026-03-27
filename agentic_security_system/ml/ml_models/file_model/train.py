import pandas as pd
import numpy as np
import pickle
import os
import math
import json

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
    df = df.copy()

    # File entropy
    if 'file_path' in df.columns:
        df['file_entropy'] = df['file_path'].apply(calculate_entropy)
        df['path_depth'] = df['file_path'].apply(
            lambda x: x.count('/') if isinstance(x, str) else 0
        )
    else:
        df['file_entropy'] = 0
        df['path_depth'] = 0

    # Suspicious extension
    suspicious_ext = ['exe', 'dll', 'bat', 'ps1']
    if 'file_extension' in df.columns:
        df['file_extension'] = df['file_extension'].astype(str).str.lower().str.strip()
        df['is_suspicious_ext'] = df['file_extension'].isin(suspicious_ext).astype(int)
    else:
        df['is_suspicious_ext'] = 0

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

    if 'file_rarity' in df.columns:
        df['is_rare_file'] = (df['file_rarity'] > 0.8).astype(int)
    else:
        df['file_rarity'] = 0
        df['is_rare_file'] = 0

    if 'file_freq_1min' in df.columns:
        df['high_freq_access'] = (
            df['file_freq_1min'] > df['file_freq_1min'].quantile(0.9)
        ).astype(int)
    else:
        df['file_freq_1min'] = 0
        df['high_freq_access'] = 0

    # ---------------- HANDLE CLASS IMBALANCE ----------------
    if 'label' not in df.columns:
        print("❌ Error: 'label' column not found in dataset.")
        return

    df_majority = df[df.label == 0]
    df_minority = df[df.label == 1]

    if len(df_minority) > 0 and len(df_majority) > 0:
        df_minority_upsampled = resample(
            df_minority,
            replace=True,
            n_samples=len(df_majority),
            random_state=42
        )
        df = pd.concat([df_majority, df_minority_upsampled], ignore_index=True)

    # ---------------- SELECT FEATURES ----------------
    features = [
        'is_rare_file',
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

    # Keep only available features
    features = [f for f in features if f in df.columns]

    if len(features) == 0:
        print("❌ Error: No valid features found.")
        return

    X = df[features].copy()
    y = df['label'].copy()

    # Save original rows for aggregator output
    raw_df = df.copy()

    # ---------------- HANDLE NaNs ----------------
    num_cols = X.select_dtypes(include=[np.number]).columns
    X[num_cols] = X[num_cols].fillna(0)
    X = X.fillna(0)

    if X.isna().sum().sum() > 0:
        print("⚠️ Warning: NaNs still present, dropping rows")
        X = X.dropna()
        y = y.loc[X.index]
        raw_df = raw_df.loc[X.index]

    # ---------------- SPLIT ----------------
    X_train, X_test, y_train, y_test, raw_train, raw_test = train_test_split(
        X, y, raw_df,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    # ---------------- RANDOM FOREST ----------------
    rf = RandomForestClassifier(
        n_estimators=500,
        max_depth=15,
        min_samples_leaf=2,
        class_weight={0: 1, 1: 3},
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

    # ---------------- HYBRID INFERENCE ----------------
    rf_probs = rf.predict_proba(X_test)[:, 1]
    svm_preds = oc_svm.predict(X_test_scaled)   # -1 = anomaly, 1 = normal

    HYBRID_THRESHOLD = 0.45
    RF_WEIGHT = 0.75
    SVM_WEIGHT = 0.25

    aggregator_ready_outputs = []
    final_preds = []

    for i in range(len(X_test)):
        # 1. Hybrid risk
        rf_score = rf_probs[i]
        anomaly_risk = 1.0 if svm_preds[i] == -1 else 0.0
        hybrid_risk = (RF_WEIGHT * rf_score) + (SVM_WEIGHT * anomaly_risk)

        # 2. Final binary prediction
        final_pred = 1 if hybrid_risk >= HYBRID_THRESHOLD else 0
        final_preds.append(final_pred)

        # 3. Current rows
        row = X_test.iloc[i]
        raw_row = raw_test.iloc[i]

        # 4. Dynamic reason assignment
        reason = "Behavioral baseline deviation"

        if row.get('high_freq_access', 0) == 1:
            reason = "High frequency access (Potential Exfiltration)"
        elif row.get('cpu_percent', 0) > X_train['cpu_percent'].quantile(0.95) if 'cpu_percent' in X_train.columns else False:
            reason = "Sudden CPU spike detected"
        elif row.get('is_suspicious_ext', 0) == 1:
            reason = "Execution of restricted file extension"
        elif row.get('file_rarity', 0) > 0.9:
            reason = "Extremely rare file execution"

        # 5. Construct aggregator state
        state = {
            "risk_score": round(float(hybrid_risk), 4),
            "pred_label": int(final_pred),
            "events": [
                {
                    "type": "file",
                    "data": {
                        "process_name": os.path.basename(str(raw_row.get('file_path', 'unknown.exe'))),
                        "parent_process": str(raw_row.get('parent_process', 'system_init')),
                        "cpu_percent": float(raw_row.get('cpu_percent', 0)),
                        "memory_mb": float(raw_row.get('memory_mb', 0)),
                        "file_path": str(raw_row.get('file_path', 'unknown')),
                        "file_extension": str(raw_row.get('file_extension', 'unknown')),
                        "reason": reason
                    }
                }
            ]
        }

        aggregator_ready_outputs.append(state)

    final_preds = np.array(final_preds)

    # ---------------- PREVIEW FOR AGGREGATOR ----------------
    print("\n✅ Example Output for Aggregator:")
    if len(aggregator_ready_outputs) > 0:
        print(json.dumps(aggregator_ready_outputs[0], indent=4))

    # ---------------- METRICS ----------------
    print("\n" + "=" * 40)
    print("      CYBERSECURITY PERFORMANCE")
    print("=" * 40)
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
                "no_data_leakage": True,
                "hybrid_threshold": HYBRID_THRESHOLD,
                "rf_weight": RF_WEIGHT,
                "svm_weight": SVM_WEIGHT
            }
        }, f)

    print(f"\n✅ Model saved at: {MODEL_SAVE_PATH}")


# ---------------- ENTRY POINT ----------------
if __name__ == "__main__":
    train_behavioral_model()