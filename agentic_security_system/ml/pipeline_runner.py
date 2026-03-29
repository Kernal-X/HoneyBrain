import time
from ml.ml_models.aggregator_model.router import ModelRouter


def main():

    print("🚀 Starting FULL PIPELINE...\n")

    router = ModelRouter()

    # ---------------- SAMPLE EVENTS ----------------
    events = [
        {
            "type": "process",
            "cpu_zscore": 1.2,
            "memory_zscore": 0.8,
            "process_freq_5min": 5,
            "is_known_binary": 0,
            "unknown_process_flag": 1,
            "external_connection_flag": 1,
            "cmd_entropy": 3.5
        },
        {
    "type": "network",
    "cpu_percent": 0.6,
    "memory_mb": 300,
    "connection_freq_1min": 5
}
    ]

    # ---------------- PIPELINE ----------------
    for event in events:

        print(f"\n📥 Incoming Event: {event['type']}")
        print("Raw Event:", event)

        try:
            result = router.route(event)
            print("✅ Result:", result)

        except Exception as e:
            print("❌ Error:", str(e))

        time.sleep(1)


if __name__ == "__main__":
    main()