import os
import joblib
import pickle
import pandas as pd
import numpy as np

from ml_models.network_model.feature_engineering import create_features


class ModelRouter:
    def __init__(self):

        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ML_MODELS_DIR = os.path.abspath(os.path.join(BASE_DIR, ".."))

        # ---------------- PROCESS MODEL ----------------
        process_model_path = os.path.join(
            ML_MODELS_DIR,
            "process_model",
            "process_final_model.pkl"
        )

        with open(process_model_path, "rb") as f:
            bundle = pickle.load(f)

        self.process_model = bundle["model"]
        self.process_features = bundle["features"]

        # ---------------- NETWORK MODEL ----------------
        network_model_path = os.path.join(
            ML_MODELS_DIR,
            "network_model",
            "model.pkl"
        )

        bundle = joblib.load(network_model_path)

        self.network_model = bundle["model"]
        self.network_features = bundle["features"]

        print("✅ Models loaded successfully")

    # -----------------------------------
    def route(self, event: dict):

        if event["type"] == "process":
            return self._predict_process(event)

        elif event["type"] == "network":
            return self._predict_network(event)

        else:
            raise ValueError("Unknown event type")

    # -----------------------------------
    # PROCESS MODEL
    # -----------------------------------
    def _predict_process(self, event):

        df = pd.DataFrame([event])
        df = df.fillna(0)

        # -------- Feature Engineering --------
        df['resource_spike'] = np.sqrt(
            df.get('cpu_zscore', 0)**2 + df.get('memory_zscore', 0)**2
        )

        df['behavior_risk'] = df['resource_spike'] * (1 - df.get('is_known_binary', 0))

        df['freq_entropy_combo'] = df.get('process_freq_5min', 0) * df.get('cmd_entropy', 0)

        df['stealth_risk'] = (
            (df.get('is_known_binary', 0) == 0) &
            (df['resource_spike'] < df['resource_spike'].median())
        ).astype(int)

        df['combined_anomaly'] = (
            (abs(df.get('cpu_zscore', 0)) > 2).astype(int) +
            (abs(df.get('memory_zscore', 0)) > 2).astype(int)
        )

        # -------- Select trained features --------
        X = df[self.process_features]

        probs = self.process_model.predict_proba(X)[:, 1]
        prediction = (probs > 0.30).astype(int)[0]

        return {
            "model": "process",
            "prediction": int(prediction),
            "risk_score": float(probs[0])
        }

    # -----------------------------------
    # NETWORK MODEL
    # -----------------------------------
    def _predict_network(self, event):

        df = pd.DataFrame([event])

        df = create_features(df)

        X = df[self.network_features]

        prediction = self.network_model.predict(X)[0]

        return {
            "model": "network",
            "prediction": int(prediction),
            "label": "anomaly" if prediction == -1 else "normal"
        }