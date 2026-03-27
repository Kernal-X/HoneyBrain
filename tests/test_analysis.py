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

# state = {
#     "risk_score": 0.88,
#     "events": [
#         {"type": "auth", "data": {"username": "admin", "status": "failed"}},
#         {"type": "auth", "data": {"username": "admin", "status": "success"}},
#         {"type": "process", "data": {"process_name": "cmd.exe", "parent_process": "unknown", "cpu_percent": 50}},
#         {"type": "file", "data": {"file_path": "secrets.txt", "action": "read"}},
#         {"type": "network", "data": {"remote_ip": "9.9.9.9", "remote_port": 443}}
#     ]
# }

# state = {
#     "risk_score": 0.75,
#     "events": [
#         {"type": "auth", "data": {"username": "employee", "status": "success"}},
#         {"type": "file", "data": {"file_path": "confidential.docx", "action": "read"}},
#         {"type": "file", "data": {"file_path": "admin_data.csv", "action": "read"}}
#     ]
# }

result = analysis_agent(state)

print("\n=== ANALYSIS OUTPUT ===")
print(result["analysis"])