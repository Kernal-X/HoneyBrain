from data_loader import load_network_data
from feature_engineering import create_features

from sklearn.ensemble import IsolationForest
import os
import joblib


BASE_DIR = os.path.dirname(__file__)
DATA_PATH = os.path.join(BASE_DIR, "../../data/raw/final_unified_dataset_10000.csv")


def main():
    print("🚀 TRAINING PIPELINE STARTED")

    # -------- Step 1: Load data --------
    df = load_network_data(DATA_PATH)
    print("Loaded shape:", df.shape)

    # -------- Step 2: Feature engineering --------
    df = create_features(df)
    print("After features:", df.shape)

    print("\nSample data:")
    print(df.head())

    # -------- Step 3: Select numeric features --------
    X = df.select_dtypes(include=["int64", "float64", "uint8"])

    # -------- Step 4: Train model --------
    print("\nTraining Isolation Forest...")
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X)

    # -------- Step 5: Get anomaly scores --------
    # decision_function: higher = normal → so invert
    df["anomaly_score"] = -model.decision_function(X)

    # -------- Step 6: Normalize scores (0 → 1) --------
    min_s = df["anomaly_score"].min()
    max_s = df["anomaly_score"].max()
    df["anomaly_score"] = (df["anomaly_score"] - min_s) / (max_s - min_s + 1e-8)

    # -------- Step 7: Apply threshold --------
    THRESHOLD = 0.7
    df["anomaly"] = (df["anomaly_score"] > THRESHOLD).astype(int)

    print("\nAnomaly count:")
    print(df["anomaly"].value_counts())

    # -------- Step 8: Risk score --------
    df["risk_score"] = 0

    # use dataset-native features
    if "port_risk" in df.columns:
        df["risk_score"] += df["port_risk"]

    if "connection_freq_1min" in df.columns:
        df["risk_score"] += (df["connection_freq_1min"] > 10).astype(int)

    if "unique_ip_5min" in df.columns:
        df["risk_score"] += (df["unique_ip_5min"] > 5).astype(int)

    if "behavioral_anomaly_flag" in df.columns:
        df["risk_score"] += df["behavioral_anomaly_flag"]

    if "external_connection_flag" in df.columns:
        df["risk_score"] += df["external_connection_flag"]

    # -------- Step 9: Final combined score --------
    df["final_score"] = df["anomaly_score"] * 0.7 + df["risk_score"] * 0.3

    # -------- Step 10: Show results --------
    print("\n🔍 Top anomalies (by anomaly score):")
    print(df.sort_values(by="anomaly_score", ascending=False).head(10))

    print("\n🚨 Top high-risk events:")
    print(df.sort_values(by="final_score", ascending=False).head(10))

    # -------- Step 11: Alerts --------
    print("\n🚨 ALERTS:")
    for _, row in df.sort_values(by="final_score", ascending=False).head(5).iterrows():
        print("\n--- ALERT ---")
        print(f"Anomaly Score: {row['anomaly_score']:.2f}")
        print(f"Risk Score: {row['risk_score']}")
        print(f"Final Score: {row['final_score']:.2f}")

        if row.get("port_scan_score", 0) > 10:
            print("⚠️ Possible PORT SCAN")

        if row.get("connection_burst", 0) > 10:
            print("⚠️ Possible BURST ATTACK")

        if row.get("high_data_transfer", 0) == 1:
            print("⚠️ Possible DATA EXFILTRATION")

    # -------- Step 12: Save model --------
    model_path = os.path.join(BASE_DIR, "model.pkl")
    joblib.dump(model, model_path)

    print("\n✅ Model saved at:", model_path)


if __name__ == "__main__":
    main()