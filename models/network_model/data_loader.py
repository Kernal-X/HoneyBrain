import pandas as pd

def load_network_data(path):
    print("📂 Loading from:", path)

    # -------- Step 1: Load CSV --------
    df = pd.read_csv(path)

    print("Initial shape:", df.shape)
    print("Columns:", df.columns.tolist())

    # -------- Step 2: Filter only network events --------
    if "event_type" in df.columns:
        df = df[df["event_type"].astype(str).str.lower().str.contains("network")]
        print("After filtering network events:", df.shape)
    else:
        print("⚠️ 'event_type' column not found — skipping filter")

    # -------- Step 3: Handle missing values --------
    df = df.fillna(0)

    # -------- Step 4: Ensure timestamp is valid --------
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    # -------- Step 5: Drop completely empty rows --------
    df = df.dropna(how="all")

    print("✅ Final loaded shape:", df.shape)

    return df