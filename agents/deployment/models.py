# agents/deployment/models.py

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class DecoyFile:
    path: str
    file_type: str
    schema: List[str]
    realism: str
    sensitivity: str = "medium"


@dataclass
class DeploymentState:
    decoy_registry: Dict
    interception_rules: Dict
    global_context: Dict