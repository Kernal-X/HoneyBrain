import pandas as pd

def create_features(df):

    print("🚀 Feature engineering started")

    # -------- Basic numeric safety --------
    numeric_cols = ["bytes_sent", "bytes_received", "duration", "dst_port"]
    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0

    # -------- Categorical encoding --------
    if "protocol" in df.columns:
        df = pd.get_dummies(df, columns=["protocol"])

    if "connection_state" in df.columns:
        df = pd.get_dummies(df, columns=["connection_state"])

    # -------- TIME-BASED FEATURES --------
    if "timestamp" in df.columns and "src_ip" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.sort_values(by="timestamp")

        df["rolling_conn_count"] = (
            df.groupby("src_ip")["timestamp"]
            .rolling(window=10)
            .count()
            .reset_index(level=0, drop=True)
        )

        df["time_diff"] = (
            df.groupby("src_ip")["timestamp"]
            .diff()
            .dt.total_seconds()
        )

        df["rolling_conn_count"] = df["rolling_conn_count"].fillna(0)
        df["time_diff"] = df["time_diff"].fillna(0)

        # BURST FLAG (must come AFTER time_diff)
        df["is_rapid_fire"] = (df["time_diff"] < 1).astype(int)

    # -------- Behavioral features --------
    if "src_ip" in df.columns:
        df["conn_count_per_src_ip"] = df.groupby("src_ip")["src_ip"].transform("count")

        if "dst_port" in df.columns:
            df["unique_ports"] = df.groupby("src_ip")["dst_port"].transform("nunique")

        if "bytes_sent" in df.columns:
            df["avg_bytes"] = df.groupby("src_ip")["bytes_sent"].transform("mean")

    # -------- Suspicious flags --------
    if "dst_port" in df.columns:
        df["is_high_port"] = (df["dst_port"] > 1024).astype(int)

    if "bytes_sent" in df.columns:
        df["is_large_transfer"] = (df["bytes_sent"] > 100000).astype(int)

    # -------- Security features --------
    if "src_ip" in df.columns and "dst_port" in df.columns:
        df["port_scan_score"] = df.groupby("src_ip")["dst_port"].transform("nunique")

    if "src_ip" in df.columns:
        df["connection_burst"] = df.groupby("src_ip")["src_ip"].transform("count")

    if "bytes_sent" in df.columns:
        df["high_data_transfer"] = (df["bytes_sent"] > df["bytes_sent"].mean()).astype(int)

    if "dst_ip" in df.columns:
        freq = df["dst_ip"].value_counts()
        df["rare_dst_ip"] = df["dst_ip"].map(freq)
        df["rare_dst_ip"] = (df["rare_dst_ip"] < 5).astype(int)

    # -------- Drop non-numeric / identifiers --------
    drop_cols = ["src_ip", "dst_ip", "timestamp"]
    df = df.drop(columns=[col for col in drop_cols if col in df.columns], errors="ignore")
    
    return df