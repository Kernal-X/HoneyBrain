"""
Build strict prompts for the Strategy Agent (executable deception plans).
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

from .schema import (
    compute_generation_limits,
    confidence_to_strategy_type,
    intent_to_artifact_focus,
    stage_to_depth,
)


def _json_block(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def build_strategy_prompt(
    analysis: Dict[str, Any],
    deterministic_hints: Dict[str, Any],
    staging_root: str,
) -> str:
    intent = analysis.get("intent", "unknown")
    attack_stage = analysis.get("attack_stage", "unknown")
    confidence = analysis.get("confidence", 0.0)
    reasoning = analysis.get("reasoning") or []
    if not isinstance(reasoning, list):
        reasoning = [str(reasoning)]

    hints_txt = _json_block(deterministic_hints)

    return f"""You are a deception engineering strategist. The security monitoring stack has ALREADY confirmed malicious activity; your task is to materialize a FULLY EXECUTABLE decoy plan for a downstream Generation Agent.

STRICT RULES:
- Output JSON ONLY. No markdown fences, no commentary, no prose before or after the JSON.
- Every field in the required schema MUST be present. No nulls. No placeholders such as TBD, N/A, example, sample, or similar.
- Use concrete absolute paths under this staging root ONLY (never reference production user home, real DB paths, or live credential stores):
  STAGING_ROOT = "{staging_root}"
- Every object inside files_to_create, credentials_to_create, system_artifacts, and network_artifacts MUST include "decoy_tagged": true and a unique "decoy_tag" string beginning with DECOY_.
- Filenames must be explicit (e.g., "Payroll_Export_Q3_DECOY.csv"), not generic.
- For credentials_to_create: use obviously synthetic values (e.g., password starting with FakePw!) — never copy real secrets.
- generation_constraints.max_files and max_credentials MUST be integers equal to or less than the limits given in DETERMINISTIC_HINTS (never exceed them).

INPUT ANALYSIS (authoritative classification — attack is assumed TRUE; confidence measures certainty of intent/stage classification, not severity):
{{
  "intent": {json.dumps(intent, ensure_ascii=False)},
  "attack_stage": {json.dumps(attack_stage, ensure_ascii=False)},
  "confidence": {float(confidence)},
  "reasoning": {json.dumps(reasoning, ensure_ascii=False)}
}}

DETERMINISTIC_HINTS (must respect these caps and policy; align execution_plan volumes with strategy_type and depth):
{hints_txt}

REQUIRED OUTPUT JSON SCHEMA (keys and nesting EXACTLY as follows — fill every list with at least one concrete object):
{{
  "strategy_type": "targeted" | "hybrid" | "exploratory",
  "intent": "{intent}",
  "attack_stage": "{attack_stage}",
  "confidence": {float(confidence)},
  "execution_plan": {{
    "files_to_create": [
      {{
        "absolute_path": "<under STAGING_ROOT>",
        "filename": "<exact filename>",
        "mime_type_hint": "<e.g. text/csv>",
        "size_bytes_target": <int>,
        "content_profile": "<short machine-usable label, e.g. csv_financial_summary>",
        "decoy_tag": "DECOY_<unique>",
        "decoy_tagged": true
      }}
    ],
    "credentials_to_create": [
      {{
        "username": "<synthetic username>",
        "password_placeholder": "FakePw!<random_suffix>",
        "realm": "<e.g. CORP-DECOY-WIN>",
        "decoy_tag": "DECOY_<unique>",
        "decoy_tagged": true
      }}
    ],
    "system_artifacts": [
      {{
        "artifact_type": "<e.g. scheduled_task_xml | service_stub | registry_export_stub>",
        "absolute_path": "<under STAGING_ROOT>",
        "definition_summary": "<one sentence the generator can implement>",
        "decoy_tag": "DECOY_<unique>",
        "decoy_tagged": true
      }}
    ],
    "network_artifacts": [
      {{
        "hostname": "<internal-looking decoy host>",
        "ip_address": "<RFC1918 style decoy>",
        "port": <int>,
        "protocol": "<tcp|udp|smb|http|https|rdp|winrm>",
        "bait_uri_or_share": "<\\\\host\\share or https://host/path — decoy only>",
        "decoy_tag": "DECOY_<unique>",
        "decoy_tagged": true
      }}
    ]
  }},
  "placement_plan": {{
    "directories_to_use": ["<absolute path 1>", "..."],
    "spread_strategy": "single_directory | clustered_directories | distributed_shares | hilbert_hostname_mirror | network_island",
    "depth": "minimal_deception | moderate | data_heavy | high_deception | network_expansion"
  }},
  "data_protection": {{
    "real_files_lock": true,
    "redirect_access_to_decoy": true,
    "backup_original_data": true,
    "access_control": "deny_non_privileged_to_production | read_only_decoys_for_clients | isolate_decoys_in_sandbox_accounts | iacl_lockdown_source_trees"
  }},
  "engagement_policy": {{
    "interaction_level": "passive_sniffer | low_interaction | medium_interaction | active_engagement",
    "allow_attacker_progress": true,
    "delay_responses": false
  }},
  "monitoring_plan": {{
    "track_events": ["<specific measurable events, e.g. file_open on decoy path>"],
    "alert_on": ["<specific alert predicates>"]
  }},
  "generation_constraints": {{
    "max_files": <int <= DETERMINISTIC_HINTS.limits.max_files>,
    "max_credentials": <int <= DETERMINISTIC_HINTS.limits.max_credentials>,
    "ensure_believability": true
  }},
  "reasoning_summary": [
    "<how intent maps to chosen artifacts>",
    "<how attack_stage maps to depth and spread>"
  ]
}}

FINAL CHECK BEFORE YOU OUTPUT:
- Confirm JSON parses.
- Confirm counts of files_to_create and credentials_to_create are <= respective max_* limits in DETERMINISTIC_HINTS.
- Confirm every decoy object has decoy_tag + decoy_tagged true.
- Confirm data_protection.real_files_lock, backup_original_data, redirect_access_to_decoy are exactly true as shown.
"""


def build_deterministic_hints(analysis: Dict[str, Any], staging_root: str) -> Dict[str, Any]:
    try:
        conf = float(analysis.get("confidence", 0))
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    intent = str(analysis.get("intent", "unknown"))
    stage = str(analysis.get("attack_stage", "unknown"))
    stype = confidence_to_strategy_type(conf)
    depth = stage_to_depth(stage)
    max_files, max_credentials = compute_generation_limits(stype, depth)
    return {
        "staging_root": staging_root,
        "strategy_type_band": stype,
        "placement_depth_rule": depth,
        "artifact_focus": intent_to_artifact_focus(intent),
        "limits": {"max_files": max_files, "max_credentials": max_credentials},
        "safety": {
            "real_files_lock": True,
            "backup_original_data": True,
            "redirect_access_to_decoy": True,
            "decoy_tag_prefix": "DECOY_",
        },
    }


def build_reasoning_payload(reasoning_summary: List[str]) -> List[str]:
    out = [str(r).strip() for r in reasoning_summary if str(r).strip()]
    return out[:6] if len(out) > 6 else out
