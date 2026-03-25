import pandas as pd
import numpy as np
import pickle
import os

# --- 1. LOAD THE "ROBUST" STACK ---
MODEL_PATH = "/home/hp/AutoDevX/ml/ml_models/file_model/file_hybrid_final.pkl"
with open(MODEL_PATH, 'rb') as f:
    stack = pickle.load(f)
    rf = stack['rf']
    features = stack['features']

# --- 2. CREATE ADVERSARIAL SAMPLES ---
# We will create "Gray Zone" events that SHOULD be hard to classify.
test_cases = [
    {
        "name": "The Stealth Hacker",
        "data": {
            'system_score': 90, 
            'behavioral_anomaly_flag': 1, 
            'unknown_process_flag': 0,  # Hacker hijacked a KNOWN process (Hard!)
            'sensitive_access_flag': 1, 
            'file_rarity': 0.8, 
            'is_executable': 0
        }
    },
    {
        "name": "The Busy Admin",
        "data": {
            'system_score': 30, 
            'behavioral_anomaly_flag': 0, 
            'unknown_process_flag': 1,  # Admin is running a new, rare script (False Alarm?)
            'sensitive_access_flag': 0, 
            'file_rarity': 0.1, 
            'is_executable': 1
        }
    }
]

print(f"{'Test Case':<20} | {'Prediction':<10} | {'Probability'}")
print("-" * 50)

for case in test_cases:
    df_live = pd.DataFrame([case['data']])[features]
    prob = rf.predict_proba(df_live)[:, 1][0]
    pred = 1 if prob > 0.5 else 0
    print(f"{case['name']:<20} | {pred:<10} | {prob:.4f}")