import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agents.analysis.analysis_agent import analysis_agent
from agents.analysis.schemas import AnalysisInput


mock_input = AnalysisInput(
    risk_score=0.2,
    signals=["unauthorized access attempt", "role change"],
    events=[
        {"event_type": "login_success", "user": "guest"},
        {"event_type": "access_attempt", "resource": "admin_panel"},
        {"event_type": "role_change", "new_role": "admin"}
    ]
)




result = analysis_agent(mock_input)

print("\n=== ANALYSIS OUTPUT ===")
print(result)