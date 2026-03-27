from aggregator import Aggregator
import time
import json

print("🚀 Simulating real-time events...\n")

# -------- Initialize aggregator --------
agg = Aggregator(window_size=5)

# -------- Event 1 --------
agg.add_event({
    "type": "process",
    "risk_score": 0.6,
    "data": {"process_name": "cmd.exe"}
})

print("Added PROCESS event")
time.sleep(1)

# -------- Event 2 --------
agg.add_event({
    "type": "network",
    "risk_score": 0.9,
    "data": {"remote_ip": "8.8.8.8"}
})

print("Added NETWORK event")
time.sleep(1)

# -------- Event 3 --------
agg.add_event({
    "type": "file",
    "risk_score": 0.8,
    "data": {"file_path": "password.txt"}
})

print("Added FILE event")

# -------- Build state from buffer --------
state = agg.build_state_from_buffer()

# -------- Print output --------
print("\n🔥 FINAL STATE FROM BUFFER:\n")

if state:
    print(json.dumps(state, indent=4))
else:
    print("No events in buffer")