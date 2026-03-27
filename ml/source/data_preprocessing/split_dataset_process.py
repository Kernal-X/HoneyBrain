import os
import pandas as pd


def extract_process_dataset(input_file, output_dir):

    # ---------------- SETUP ----------------
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "process_dataset.csv")

    # ---------------- LOAD ----------------
    df = pd.read_csv(input_file)

    # Normalize columns
    df.columns = df.columns.str.lower().str.strip()

    # ---------------- FILTER ----------------
    process_df = df[df['event_type'] == 'process'].copy()

    # ---------------- SELECT FEATURES ----------------
    process_features = [
        'timestamp',
        'system_score',
        'severity',
        'behavioral_anomaly_flag',
        'external_connection_flag',
        'unknown_process_flag',
        'sensitive_access_flag',
        'label',

        # Process-specific
        'process_name',
        'parent_process',
        'cpu_percent',
        'memory_mb',
        'cpu_zscore',
        'memory_zscore',
        'parent_child_rarity',
        'cmd_entropy',
        'process_freq_5min',
        'is_known_binary'
    ]

    # Keep only existing columns
    process_features = [col for col in process_features if col in process_df.columns]
    process_df = process_df[process_features]

    # ---------------- CLEAN ----------------
    process_df.fillna({
        'process_name': 'unknown',
        'parent_process': 'unknown'
    }, inplace=True)

    # Fill numeric NaNs
    num_cols = process_df.select_dtypes(include=['float64', 'int64']).columns
    process_df[num_cols] = process_df[num_cols].fillna(0)

    # ---------------- SAVE ----------------
    process_df.to_csv(output_file, index=False)

    print(f"✅ Process dataset created at: {output_file}")
    print("Shape:", process_df.shape)


# ---------------- PATH SETUP ----------------
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

INPUT_FILE = os.path.normpath(
    os.path.join(CURRENT_DIR, "../../data/raw/final_unified_dataset_10000.csv")
)

OUTPUT_DIR = os.path.normpath(
    os.path.join(CURRENT_DIR, "../../data/processed/")
)


# ---------------- ENTRY POINT ----------------
if __name__ == "__main__":
    extract_process_dataset(INPUT_FILE, OUTPUT_DIR)