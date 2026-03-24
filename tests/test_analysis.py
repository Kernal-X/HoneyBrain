import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.analysis.analysis_agent import analysis_agent


state = {
    "risk_score": 0.85,
    "events": [
        {"type": "auth", "data": {"username": "guest", "status": "success", "source_ip": "192.168.1.7"}},
        {
            "type": "process",
            "data": {
                "process_name": "cmd.exe",
                "parent_process": "unknown",
                "cpu_percent": 15,
                "memory_mb": 50,
                "reason": "elevated privilege attempt"
            }
        }
    ]
}




result = analysis_agent(state)

print("\n=== ANALYSIS OUTPUT ===")
print(result)