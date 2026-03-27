import pandas as pd
import pickle
import os
from sklearn.inspection import permutation_importance
from sklearn.model_selection import train_test_split

# 1. USE THE EXACT SAME PATH LOGIC AS YOUR WORKING TRAIN.PY
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.normpath(os.path.join(BASE_DIR, "../../data/processed/file_dataset.csv"))
# Match the filename from your train.py output
MODEL_PATH = os.path.join(BASE_DIR, "file_hybrid_final.pkl") 

def run_final_audit():
    print(f"Checking Data at: {DATA_PATH}")
    print(f"Checking Model at: {MODEL_PATH}")

    if not os.path.exists(DATA_PATH) or not os.path.exists(MODEL_PATH):
        print("❌ ERROR: Files not found. Ensure you ran train.py first!")
        return

    # 2. LOAD
    df = pd.read_csv(DATA_PATH)
    with open(MODEL_PATH, 'rb') as f:
        stack = pickle.load(f)
        rf = stack['rf']
        features = stack['features']

    X = df[features].fillna(0)
    y = df['label']
    
    # Test on a 30% holdout to see if it's "cheating" on unseen data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

    # 3. PERMUTATION IMPORTANCE
    # This shuffles each column. If accuracy drops, that feature is the "Anchor."
    print("\nAuditing Feature Addiction (Shuffling 5x per feature)...")
    result = permutation_importance(rf, X_test, y_test, n_repeats=5, random_state=42)

    # 4. OUTPUT
    importance_df = pd.DataFrame({
        'feature': features,
        'importance_mean': result.importances_mean
    }).sort_values(by='importance_mean', ascending=False)

    print("\n" + "="*40)
    print("      FINAL FEATURE ADDICTION AUDIT")
    print("="*40)
    print(importance_df)
    print("="*40)
    print("INTERPRETATION:")
    print("- High Score (>0.4): Model is 'Addicted' (Cheat Code).")
    print("- Low/Even Scores: Model is 'Robust' (Holistic Logic).")

if __name__ == "__main__":
    run_final_audit()