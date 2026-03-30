"""
Validate, normalize, and repair Strategy Agent output. Provides deterministic fallback plans.
"""

from __future__ import annotations

import copy
import os
import uuid
from typing import Any, Dict, List, Tuple

from .schema import (
    ACCESS_CONTROL_MODES,
    DATA_PROTECTION_KEYS,
    DEPTH_VALUES,
    ENGAGEMENT_KEYS,
    EXECUTION_LIST_KEYS,
    GENERATION_CONSTRAINT_KEYS,
    INTERACTION_LEVELS,
    MONITORING_KEYS,
    PLACEMENT_KEYS,
    REQUIRED_TOP_KEYS,
    SPREAD_STRATEGIES,
    STRATEGY_TYPES,
    confidence_to_strategy_type,
    compute_generation_limits,
    intent_to_artifact_focus,
    stage_to_depth,
)


def _new_decoy_tag() -> str:
    return f"DECOY_{uuid.uuid4().hex[:12].upper()}"


def _as_bool(v: Any, default: bool) -> bool:
    if isinstance(v, bool):
        return v
    if v in (1, "1", "true", "True"):
        return True
    if v in (0, "0", "false", "False"):
        return False
    return default


def _as_str_list(v: Any, min_len: int, fill: str) -> List[str]:
    if isinstance(v, list):
        out = [str(x).strip() for x in v if str(x).strip()]
    else:
        out = []
    while len(out) < min_len:
        out.append(fill)
    return out


def _as_int(v: Any, default: int, min_v: int, max_v: int) -> int:
    try:
        i = int(v)
    except (TypeError, ValueError):
        i = default
    return max(min_v, min(max_v, i))


def _tag_execution_item(item: Dict[str, Any]) -> Dict[str, Any]:
    o = dict(item)
    o["decoy_tagged"] = True
    if not o.get("decoy_tag") or not str(o["decoy_tag"]).startswith("DECOY_"):
        o["decoy_tag"] = _new_decoy_tag()
    return o


def enforce_safety_and_tags(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Mandatory safety flags and decoy tagging for all execution artifacts."""
    data = copy.deepcopy(payload)
    dp = data.get("data_protection")
    if not isinstance(dp, dict):
        dp = {}
    dp["real_files_lock"] = True
    dp["backup_original_data"] = True
    dp["redirect_access_to_decoy"] = True
    if dp.get("access_control") not in ACCESS_CONTROL_MODES:
        dp["access_control"] = "isolate_decoys_in_sandbox_accounts"
    data["data_protection"] = dp

    ep = data.get("execution_plan")
    if not isinstance(ep, dict):
        ep = {}
    for key in EXECUTION_LIST_KEYS:
        items = ep.get(key)
        if not isinstance(items, list):
            items = []
        ep[key] = [_tag_execution_item(x) for x in items if isinstance(x, dict)]
    data["execution_plan"] = ep
    return data


def validate_strategy_shape(
    data: Dict[str, Any],
    analysis: Dict[str, Any],
    max_files: int,
    max_credentials: int,
) -> Tuple[bool, List[str]]:
    errors: List[str] = []
    if not isinstance(data, dict):
        return False, ["root must be object"]

    missing = REQUIRED_TOP_KEYS - data.keys()
    if missing:
        errors.append(f"missing keys: {sorted(missing)}")

    st = data.get("strategy_type")
    if st not in STRATEGY_TYPES:
        errors.append("invalid strategy_type")

    intent = data.get("intent")
    if intent != analysis.get("intent"):
        errors.append("intent mismatch with analysis")

    stage = data.get("attack_stage")
    if stage != analysis.get("attack_stage"):
        errors.append("attack_stage mismatch with analysis")

    try:
        conf = float(data.get("confidence", 0))
    except (TypeError, ValueError):
        conf = -1.0
    if conf < 0 or conf > 1:
        errors.append("confidence out of range")
    try:
        aconf = float(analysis.get("confidence", 0))
    except (TypeError, ValueError):
        aconf = 0.0
    if round(conf, 4) != round(float(aconf), 4):
        errors.append("confidence must match analysis confidence exactly")

    ep = data.get("execution_plan")
    if not isinstance(ep, dict):
        errors.append("execution_plan invalid")
    else:
        for k in EXECUTION_LIST_KEYS:
            if k not in ep or not isinstance(ep[k], list) or len(ep[k]) < 1:
                errors.append(f"execution_plan.{k} must be non-empty list")
            else:
                for idx, obj in enumerate(ep[k]):
                    if not isinstance(obj, dict):
                        errors.append(f"execution_plan.{k}[{idx}] not object")
                        continue
                    if not obj.get("decoy_tagged") is True:
                        errors.append(f"execution_plan.{k}[{idx}] decoy_tagged not true")
                    dt = obj.get("decoy_tag")
                    if not dt or not str(dt).startswith("DECOY_"):
                        errors.append(f"execution_plan.{k}[{idx}] invalid decoy_tag")

    pp = data.get("placement_plan")
    if not isinstance(pp, dict):
        errors.append("placement_plan invalid")
    else:
        for pk in PLACEMENT_KEYS:
            if pk not in pp:
                errors.append(f"placement_plan missing {pk}")
        if pp.get("spread_strategy") not in SPREAD_STRATEGIES:
            errors.append("invalid spread_strategy")
        if pp.get("depth") not in DEPTH_VALUES:
            errors.append("invalid depth")
        dirs = pp.get("directories_to_use")
        if not isinstance(dirs, list) or len(dirs) < 1:
            errors.append("directories_to_use must be non-empty")
        else:
            for p in dirs:
                if not isinstance(p, str) or not p.strip():
                    errors.append("invalid directory path")

    dp = data.get("data_protection")
    if not isinstance(dp, dict):
        errors.append("data_protection invalid")
    else:
        for dk in DATA_PROTECTION_KEYS:
            if dk not in dp:
                errors.append(f"data_protection missing {dk}")
        if dp.get("access_control") not in ACCESS_CONTROL_MODES:
            errors.append("invalid access_control")
        for safety_k in ("real_files_lock", "redirect_access_to_decoy", "backup_original_data"):
            if dp.get(safety_k) is not True:
                errors.append(f"data_protection.{safety_k} must be true")

    eng = data.get("engagement_policy")
    if not isinstance(eng, dict):
        errors.append("engagement_policy invalid")
    else:
        for ek in ENGAGEMENT_KEYS:
            if ek not in eng:
                errors.append(f"engagement_policy missing {ek}")
        if eng.get("interaction_level") not in INTERACTION_LEVELS:
            errors.append("invalid interaction_level")
        if not isinstance(eng.get("allow_attacker_progress"), bool):
            errors.append("allow_attacker_progress must be bool")
        if not isinstance(eng.get("delay_responses"), bool):
            errors.append("delay_responses must be bool")

    mon = data.get("monitoring_plan")
    if not isinstance(mon, dict):
        errors.append("monitoring_plan invalid")
    else:
        for mk in MONITORING_KEYS:
            if mk not in mon or not isinstance(mon.get(mk), list) or len(mon[mk]) < 1:
                errors.append(f"monitoring_plan.{mk} must be non-empty list")

    gc = data.get("generation_constraints")
    if not isinstance(gc, dict):
        errors.append("generation_constraints invalid")
    else:
        for gk in GENERATION_CONSTRAINT_KEYS:
            if gk not in gc:
                errors.append(f"generation_constraints missing {gk}")
        mf = gc.get("max_files")
        mc = gc.get("max_credentials")
        try:
            if int(mf) > max_files or int(mf) < 1:
                errors.append("max_files out of allowed range")
            if int(mc) > max_credentials or int(mc) < 1:
                errors.append("max_credentials out of allowed range")
        except (TypeError, ValueError):
            errors.append("generation_constraints ints invalid")
        if gc.get("ensure_believability") is not True:
            errors.append("ensure_believability must be true")

    rs = data.get("reasoning_summary")
    if not isinstance(rs, list) or len(rs) < 2:
        errors.append("reasoning_summary must have at least 2 strings")

    return len(errors) == 0, errors


def normalize_strategy_enumerations(data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Repair invalid enum-like fields so validation can pass without falling back."""
    d = copy.deepcopy(data)
    stage = str(analysis.get("attack_stage", "unknown"))
    stype = d.get("strategy_type")

    pp = d.get("placement_plan")
    if isinstance(pp, dict):
        if pp.get("spread_strategy") not in SPREAD_STRATEGIES:
            if stage == "lateral_movement":
                pp["spread_strategy"] = "network_island"
            elif stage in {"collection", "exfiltration"}:
                pp["spread_strategy"] = "distributed_shares"
            else:
                pp["spread_strategy"] = "clustered_directories" if stype == "targeted" else "single_directory"
        if pp.get("depth") not in DEPTH_VALUES:
            pp["depth"] = stage_to_depth(stage)

    eng = d.get("engagement_policy")
    if isinstance(eng, dict):
        if eng.get("interaction_level") not in INTERACTION_LEVELS:
            eng["interaction_level"] = (
                "active_engagement"
                if stype == "targeted" and stage == "exfiltration"
                else "medium_interaction"
                if stype == "targeted"
                else "low_interaction"
            )
        eng["allow_attacker_progress"] = _as_bool(eng.get("allow_attacker_progress"), True)
        eng["delay_responses"] = _as_bool(eng.get("delay_responses"), False)

    dp = d.get("data_protection")
    if isinstance(dp, dict) and dp.get("access_control") not in ACCESS_CONTROL_MODES:
        dp["access_control"] = "isolate_decoys_in_sandbox_accounts"

    return d


def trim_execution_to_limits(data: Dict[str, Any], max_files: int, max_credentials: int) -> Dict[str, Any]:
    d = copy.deepcopy(data)
    ep = d.get("execution_plan", {})
    files = ep.get("files_to_create") or []
    creds = ep.get("credentials_to_create") or []
    ep["files_to_create"] = files[:max_files] if len(files) > max_files else files
    ep["credentials_to_create"] = creds[:max_credentials] if len(creds) > max_credentials else creds
    d["execution_plan"] = ep
    gc = d.get("generation_constraints", {})
    try:
        mf_cur = int(gc.get("max_files", max_files))
    except (TypeError, ValueError):
        mf_cur = max_files
    try:
        mc_cur = int(gc.get("max_credentials", max_credentials))
    except (TypeError, ValueError):
        mc_cur = max_credentials
    gc["max_files"] = min(max(1, mf_cur), max_files)
    gc["max_credentials"] = min(max(1, mc_cur), max_credentials)
    d["generation_constraints"] = gc
    return d


def apply_deterministic_overrides(data: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Policy: strategy_type follows confidence bands; depth follows stage."""
    d = copy.deepcopy(data)
    try:
        conf = float(analysis.get("confidence", 0))
    except (TypeError, ValueError):
        conf = 0.0
    d["strategy_type"] = confidence_to_strategy_type(conf)
    d["intent"] = analysis.get("intent", "unknown")
    d["attack_stage"] = analysis.get("attack_stage", "unknown")
    d["confidence"] = max(0.0, min(1.0, conf))

    depth = stage_to_depth(str(d["attack_stage"]))
    pp = d.get("placement_plan", {})
    if isinstance(pp, dict):
        pp["depth"] = depth
    d["placement_plan"] = pp
    return d


def build_fallback_strategy(
    analysis: Dict[str, Any],
    staging_root: str,
) -> Dict[str, Any]:
    """Fully specified executable plan when the LLM is unavailable or invalid."""
    try:
        conf = float(analysis.get("confidence", 0))
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))
    intent = str(analysis.get("intent", "unknown"))
    stage = str(analysis.get("attack_stage", "unknown"))
    reasoning = analysis.get("reasoning") or []
    if not isinstance(reasoning, list):
        reasoning = [str(reasoning)]

    stype = confidence_to_strategy_type(conf)
    depth = stage_to_depth(stage)
    max_files, max_credentials = compute_generation_limits(stype, depth)
    focus = intent_to_artifact_focus(intent)

    d_root = os.path.abspath(staging_root)
    dir_a = os.path.join(d_root, "finance_decoys")
    dir_b = os.path.join(d_root, "identity_decoys")

    tags_f = _new_decoy_tag()
    tags_c = _new_decoy_tag()
    tags_s = _new_decoy_tag()
    tags_n = _new_decoy_tag()

    file_path = os.path.join(dir_a, f"M_Drive_Export_{tags_f[-6:]}.csv")

    spread = "clustered_directories" if depth in {"data_heavy", "high_deception"} else "single_directory"
    if stage == "lateral_movement":
        spread = "network_island"

    payload: Dict[str, Any] = {
        "strategy_type": stype,
        "intent": intent,
        "attack_stage": stage,
        "confidence": conf,
        "execution_plan": {
            "files_to_create": [
                {
                    "absolute_path": file_path,
                    "filename": f"M_Drive_Export_{tags_f[-6:]}.csv",
                    "mime_type_hint": "text/csv",
                    "size_bytes_target": 65536 if depth in {"data_heavy", "high_deception"} else 16384,
                    "content_profile": f"csv_{focus[0]}_summary",
                    "decoy_tag": tags_f,
                    "decoy_tagged": True,
                }
            ],
            "credentials_to_create": [
                {
                    "username": "svc_decoy_sfreader",
                    "password_placeholder": f"FakePw!{tags_c[-8:]}",
                    "realm": "CORP-DECOY-LAB",
                    "decoy_tag": tags_c,
                    "decoy_tagged": True,
                }
            ],
            "system_artifacts": [
                {
                    "artifact_type": "scheduled_task_stub",
                    "absolute_path": os.path.join(dir_b, f"DecoyTask_{tags_s[-6:]}.xml"),
                    "definition_summary": "Registers a non-executable stub task that logs invocation attempts only.",
                    "decoy_tag": tags_s,
                    "decoy_tagged": True,
                }
            ],
            "network_artifacts": [
                {
                    "hostname": "fs01-decoy.internal",
                    "ip_address": "10.64.32.50",
                    "port": 445,
                    "protocol": "smb",
                    "bait_uri_or_share": "\\\\fs01-decoy.internal\\FinanceShare_DECOY",
                    "decoy_tag": tags_n,
                    "decoy_tagged": True,
                }
            ],
        },
        "placement_plan": {
            "directories_to_use": _as_str_list([dir_a, dir_b], 2, dir_a),
            "spread_strategy": spread,
            "depth": depth,
        },
        "data_protection": {
            "real_files_lock": True,
            "redirect_access_to_decoy": True,
            "backup_original_data": True,
            "access_control": "isolate_decoys_in_sandbox_accounts",
        },
        "engagement_policy": {
            "interaction_level": "medium_interaction" if stype == "targeted" else "low_interaction",
            "allow_attacker_progress": True,
            "delay_responses": False,
        },
        "monitoring_plan": {
            "track_events": [
                f"file_open:{dir_a}",
                "auth_failure_on_decoy_credential",
                f"smb_session_to:{file_path}",
            ],
            "alert_on": [
                "decoy_file_read_threshold>3_in_60s",
                "non_sandbox_account_touching_decoy_root",
            ],
        },
        "generation_constraints": {
            "max_files": max_files,
            "max_credentials": max_credentials,
            "ensure_believability": True,
        },
        "reasoning_summary": [
            f"Deterministic fallback maps intent {intent} to focus {focus} using decoys only under {staging_root}.",
            f"Stage {stage} maps to depth {depth}; spread_strategy {spread} limits blast radius while preserving realism.",
        ],
    }

    if intent == "lateral_movement":
        payload["execution_plan"]["network_artifacts"].append(
            {
                "hostname": "jump-decoy-02",
                "ip_address": "10.64.33.10",
                "port": 5985,
                "protocol": "winrm",
                "bait_uri_or_share": "http://jump-decoy-02:5985/wsman",
                "decoy_tag": _new_decoy_tag(),
                "decoy_tagged": True,
            }
        )

    payload = trim_execution_to_limits(payload, max_files, max_credentials)
    return enforce_safety_and_tags(apply_deterministic_overrides(payload, analysis))
