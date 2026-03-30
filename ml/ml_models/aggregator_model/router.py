import os
import pickle
import joblib
import pandas as pd
import numpy as np


class ModelRouter:

    def __init__(self):

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ML_MODELS_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

        # ---------------- PROCESS MODEL ----------------
        process_path = os.path.join(
            ML_MODELS_DIR,
            "process_model",
            "process_hybrid_final.pkl"
        )

        with open(process_path, "rb") as f:
            bundle = pickle.load(f)

        self.process_rf = bundle["rf_model"]
        self.process_iso = bundle["iso_model"]
        self.process_rf_features = bundle["rf_features"]
        self.process_iso_features = bundle["iso_features"]

        # ---------------- NETWORK MODEL ----------------
        network_path = os.path.join(
            ML_MODELS_DIR,
            "network_model",
            "network_hybrid_model.pkl"
        )

        with open(network_path, "rb") as f:
            bundle = pickle.load(f)

        self.network_rf = bundle["rf_model"]
        self.network_iso = bundle["iso_model"]
        self.network_rf_features = bundle["rf_features"]
        self.network_iso_features = bundle["iso_features"]

        # ---------------- FILE MODEL ----------------
        file_path = os.path.join(
            ML_MODELS_DIR,
            "file_model",
            "file_hybrid_final.pkl"
        )

        with open(file_path, "rb") as f:
            bundle = pickle.load(f)

        self.file_rf = bundle["rf_model"]
        self.file_iso = bundle["iso_model"]
        self.file_rf_features = bundle["rf_features"]
        self.file_iso_features = bundle["iso_features"]

        print("✅ All models loaded successfully")

    # =====================================================
    # ROUTER
    # =====================================================
    def route(self, event):

        if event["type"] == "process":
            return self._predict_process(event)

        elif event["type"] == "network":
            return self._predict_network(event)

        elif event["type"] == "file":
            return self._predict_file(event)

        else:
            raise ValueError("Unknown event type")

    # =====================================================
    # PROCESS
    # =====================================================
    def _predict_process(self, event):

        df = pd.DataFrame([event])
         # Ensure all required RF features exist
        for col in self.process_rf_features:
            if col not in df.columns:
                df[col] = 0

        # Ensure all required ISO features exist
        for col in self.process_iso_features:
            if col not in df.columns:
                df[col] = 0

        df = df.fillna(0)

        # -------- RF --------
        X_rf = df[self.process_rf_features]
        rf_prob = self.process_rf.predict_proba(X_rf)[:, 1][0]

        # -------- ISO --------
        X_iso = df[self.process_iso_features]
        iso_raw = self.process_iso.decision_function(X_iso)[0]
        iso_prob = 1 / (1 + np.exp(-(-iso_raw)))

        # -------- RULE --------
        rule_score = 0

        if event.get("system_score", 0) >= 3:
            rule_score += 0.22

        if event.get("unknown_process_flag", 0) == 1:
            rule_score += 0.18

        if event.get("behavioral_anomaly_flag", 0) == 1:
            rule_score += 0.15

        # -------- HYBRID --------
        hybrid_score = (
            0.32 * rule_score +
            0.44 * rf_prob +
            0.24 * iso_prob
        )

        prediction = int(hybrid_score >= 0.46)

        return {
            "type": "process",
            "prediction": prediction,
            "risk_score": float(hybrid_score)
        }

    # =====================================================
    # NETWORK
    # =====================================================
    def _predict_network(self, event):
        df = pd.DataFrame([event])

        # Ensure all required RF features exist
        for col in self.network_rf_features:
            if col not in df.columns:
                df[col] = 0

        # Ensure all required ISO features exist
        for col in self.network_iso_features:
            if col not in df.columns:
                df[col] = 0

        df = df.fillna(0)

        # -------- RF --------
        X_rf = df[self.network_rf_features]
        rf_prob = self.network_rf.predict_proba(X_rf)[:, 1][0]

        # -------- ISO --------
        X_iso = df[self.network_iso_features]
        iso_raw = self.network_iso.decision_function(X_iso)[0]
        iso_prob = 1 / (1 + np.exp(-(-iso_raw)))

        # -------- RULE --------
        rule_score = 0

        if event.get("severity", 0) >= 2:
            rule_score += 0.2

        if event.get("is_known_ip", 1) == 0:
            rule_score += 0.15

        if event.get("connection_freq_1min", 0) > 20:
            rule_score += 0.1

        # -------- HYBRID --------
        hybrid_score = (
            0.45 * rule_score +
            0.30 * rf_prob +
            0.25 * iso_prob
        )

        prediction = int(hybrid_score >= 0.4)

        return {
            "type": "network",
            "prediction": prediction,
            "risk_score": float(hybrid_score)
        }

    # =====================================================
    # FILE
    # =====================================================
    def _predict_file(self, event):

        df = pd.DataFrame([event])
        # Ensure all required RF features exist
        for col in self.file_rf_features:
            if col not in df.columns:
                df[col] = 0

        # Ensure all required ISO features exist
        for col in self.file_iso_features:
            if col not in df.columns:
                df[col] = 0

        df = df.fillna(0)

        # -------- RF --------
        X_rf = df[self.file_rf_features]
        rf_prob = self.file_rf.predict_proba(X_rf)[:, 1][0]

        # -------- ISO --------
        X_iso = df[self.file_iso_features]
        iso_raw = self.file_iso.decision_function(X_iso)[0]
        iso_prob = 1 / (1 + np.exp(-(-iso_raw)))

        # -------- RULE --------
        rule_score = 0

        if event.get("system_score", 0) >= 3:
            rule_score += 0.3

        if event.get("sensitive_access_flag", 0) == 1:
            rule_score += 0.15

        if event.get("behavioral_anomaly_flag", 0) == 1:
            rule_score += 0.2

        # -------- HYBRID --------
        hybrid_score = (
            0.40 * rule_score +
            0.35 * rf_prob +
            0.25 * iso_prob
        )

        prediction = int(hybrid_score >= 0.42)

        return {
            "type": "file",
            "prediction": prediction,
            "risk_score": float(hybrid_score)
        }