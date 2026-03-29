import os
import joblib
import pandas as pd

from data_loader import load_network_data
from feature_engineering import create_features

from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# -----------------------------------
# PATH SETUP
# -----------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = os.path.join(
    BASE_DIR,
    "../../data/raw/final_unified_dataset_10000.csv"
)

MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")


# -----------------------------------
# TRAINING PIPELINE
# -----------------------------------

def main():

    print("🚀 TRAINING NETWORK MODEL STARTED")

    # -------- Step 1: Load data --------
    df = load_network_data(DATA_PATH)
    print("Loaded shape:", df.shape)

    # -------- Step 2: Feature engineering --------
    print("🚀 Applying feature engineering...")
    df = create_features(df)
    print("After features:", df.shape)

    print("\nSample data:")
    print(df.head())

    # -------- Step 3: Select features --------
    X = df[[
        "cpu_percent",
        "memory_mb",
        "connection_freq_1min"
    ]]

    feature_names = X.columns.tolist()

    print("\n📊 Features used:", feature_names)

    # -------- Step 4: Train model --------
    print("\n🤖 Training Isolation Forest...")

    model = IsolationForest(
        contamination=0.05,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X)

    # -------- Step 5: Anomaly scoring --------
    df["anomaly_score"] = -model.decision_function(X)

    # -------- Step 6: Normalize scores --------
    min_s = df["anomaly_score"].min()
    max_s = df["anomaly_score"].max()

    df["anomaly_score"] = (
        (df["anomaly_score"] - min_s) / (max_s - min_s + 1e-8)
    )

    # -------- Step 7: Thresholding --------
    THRESHOLD = 0.4
    df["anomaly"] = (df["anomaly_score"] > THRESHOLD).astype(int)

    print("\n🔍 Anomaly count:")
    print(df["anomaly"].value_counts())

    # -------- Step 8: Evaluation --------
    if "label" in df.columns:

        print("\n" + "=" * 40)
        print("      NETWORK MODEL PERFORMANCE")
        print("=" * 40)

        y_true = df["label"]
        y_pred = df["anomaly"]

        print("Accuracy:", round(accuracy_score(y_true, y_pred), 4))
        print("Precision:", round(precision_score(y_true, y_pred), 4))
        print("Recall:", round(recall_score(y_true, y_pred), 4))
        print("F1 Score:", round(f1_score(y_true, y_pred), 4))

        print("\nConfusion Matrix:")
        print(confusion_matrix(y_true, y_pred))

        print("\nClassification Report:")
        print(classification_report(y_true, y_pred))

    # -------- Step 9: Show top anomalies --------
    print("\n🔍 Top anomalies:")
    print(df.sort_values(by="anomaly_score", ascending=False).head(10))

    # -------- Step 10: Alerts --------
    print("\n🚨 ALERTS:")

    for _, row in df.sort_values(by="anomaly_score", ascending=False).head(5).iterrows():

        print("\n--- ALERT ---")
        print(f"Anomaly Score: {row['anomaly_score']:.2f}")

        if row.get("port_scan_score", 0) > 10:
            print("⚠️ Possible PORT SCAN")

        if row.get("connection_burst", 0) > 10:
            print("⚠️ Possible BURST ATTACK")

        if row.get("high_data_transfer", 0) == 1:
            print("⚠️ Possible DATA EXFILTRATION")

    # -------- Step 11: SAVE MODEL --------
    print("\n💾 Saving model...")

    joblib.dump({
        "model": model,
        "features": feature_names
    }, MODEL_PATH)

    print("✅ Model saved at:", MODEL_PATH)


# -----------------------------------
# ENTRY POINT
# -----------------------------------

if __name__ == "__main__":
    main()