import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.analysis.analysis_agent import analysis_agent

state = {
    "risk_score": 0.65,
    "events": [
        {
            "type": "process",
            "data": {
                "process_name": "unknown.exe",
                "parent_process": "unknown",
                "cpu_percent": 95,
                "memory_mb": 500,
                "reason": "high resource usage"
            }
        }
    ]
}



result = analysis_agent(state)

print("\n=== ANALYSIS OUTPUT ===")
print(result)