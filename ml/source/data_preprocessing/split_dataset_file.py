import os
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler


# ---------------- MAIN FUNCTION ----------------
def split_and_enhance_datasets(input_file, output_dir):

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "file_dataset.csv")

    # ---------------- LOAD ----------------
    df = pd.read_csv(input_file)
    df.columns = df.columns.str.lower().str.strip()

    # ---------------- FILTER ----------------
    file_df = df[df['event_type'] == 'file'].copy()

    # ---------------- SELECT FEATURES ----------------
    file_features = [
        'timestamp',
        'system_score',
        'severity',
        'behavioral_anomaly_flag',
        'sensitive_access_flag',
        'label',

        'file_path',
        'file_action',
        'file_extension',
        'is_sensitive_path',
        'is_executable',
        'file_freq_1min',
        'file_rarity',

        'process_name',
        'parent_process',
        'cpu_percent',
        'memory_mb',
        'cpu_zscore',
        'memory_zscore'
    ]

    file_features = [col for col in file_features if col in file_df.columns]
    file_df = file_df[file_features]

    # ---------------- CLEAN ----------------
    file_df.fillna({
        'file_extension': 'unknown',
        'file_action': 'unknown',
        'process_name': 'unknown',
        'parent_process': 'unknown'
    }, inplace=True)

    # ---------------- ENCODING ----------------
    cat_cols = ['file_action', 'file_extension', 'process_name', 'parent_process']

    for col in cat_cols:
        if col in file_df.columns:
            le = LabelEncoder()
            file_df[col] = le.fit_transform(file_df[col].astype(str))

    # ---------------- SCALING ----------------
    num_cols = [
        'cpu_percent','memory_mb','cpu_zscore',
        'memory_zscore','file_freq_1min','file_rarity'
    ]

    num_cols = [col for col in num_cols if col in file_df.columns]

    scaler = StandardScaler()
    file_df[num_cols] = scaler.fit_transform(file_df[num_cols])

    # ---------------- SAVE ----------------
    file_df.to_csv(output_file, index=False)

    print(f"✅ File dataset created at: {output_file}")
    print("Shape:", file_df.shape)


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
    split_and_enhance_datasets(INPUT_FILE, OUTPUT_DIR)