# Agentic Security System

LangGraph-orchestrated host monitoring and deception pipeline for process, file, and network telemetry.

This project combines:
- live telemetry collection
- rule-based detection
- ML routing and risk aggregation
- LLM-based attacker analysis
- LLM-based deception strategy planning
- decoy deployment and file-response interception

The current runtime is centered around [main.py](/E:/agentic_ai/defense system/main.py), [agents/system_agent.py](/E:/agentic_ai/defense system/agents/system_agent.py), and [langgraph_pipeline.py](/E:/agentic_ai/defense system/langgraph_pipeline.py).

![Workflow Diagram](/E:/agentic_ai/defense system/visual_flows.svg)

## Overview

At a high level, the system works like this:

1. Collect process, file, and network events from the host.
2. Enrich those events with behavioral and ML-friendly features.
3. Filter known-noise telemetry.
4. Score suspicious activity with rule-based logic.
5. Route suspicious events into file/process/network ML models.
6. Aggregate model outputs into a global incident risk score.
7. If the risk is high enough, analyze likely attacker intent and attack stage.
8. Convert that analysis into a structured deception strategy.
9. Register decoys and interception rules.
10. When a protected path is requested through the system flow, serve real, partial, or fake content.

## Architecture

The active architecture is the `agents/`, `core/`, `collectors/`, `detectors/`, `logs/`, and `ml/` stack. The older `src/` tree exists, but most of it is legacy or placeholder code and is not the primary runtime path.

### Main runtime path

`main.py -> SystemAgent -> LangGraphSecurityPipeline -> monitor -> enrich -> filter -> score -> ML aggregate -> analysis -> strategy -> deployment -> interception`

### Core orchestration files

- [langgraph_pipeline.py](/E:/agentic_ai/defense system/langgraph_pipeline.py): full LangGraph workflow
- [state_schema.py](/E:/agentic_ai/defense system/state_schema.py): shared graph state schema
- [agents/system_agent.py](/E:/agentic_ai/defense system/agents/system_agent.py): long-running runtime loop
- [system_analysis.md](/E:/agentic_ai/defense system/system_analysis.md): detailed repository analysis

## LangGraph Workflow

The system is orchestrated as a `StateGraph(SecuritySystemState)` with these nodes:

- `prepare_state`
- `collect_events`
- `enrich_events`
- `filter_events`
- `score_events`
- `emit_alerts`
- `analysis`
- `strategy`
- `deployment`
- `interception`

### Shared state

The graph passes a single shared state object across all nodes, including:

- `mode`
- `input_events`
- `raw_events`
- `enriched_events`
- `filtered_events`
- `detections`
- `suspicious_events`
- `alert_records`
- `risk_score`
- `analysis`
- `strategy`
- `strategy_meta`
- `deployment`
- `request_path`
- `interception_result`
- `errors`
- `notes`
- `cycle_report`

### Routing behavior

- In `monitor` mode, the graph runs the full telemetry-to-response pipeline.
- In `intercept` mode, the graph can jump directly into later stages depending on what state is already present.
- After alert aggregation, the graph only continues to `analysis` if an aggregated alert is raised.
- After `strategy`, the graph only continues if a valid strategy exists.
- After `deployment`, the graph only continues to `interception` if a `request_path` is present.

## Repository Structure

### Runtime and orchestration

- [main.py](/E:/agentic_ai/defense system/main.py): application entry point
- [langgraph_pipeline.py](/E:/agentic_ai/defense system/langgraph_pipeline.py): LangGraph orchestration layer
- [state_schema.py](/E:/agentic_ai/defense system/state_schema.py): graph state contract
- [agents/system_agent.py](/E:/agentic_ai/defense system/agents/system_agent.py): runtime loop and live reporting

### Event collection

- [collectors/process_collector.py](/E:/agentic_ai/defense system/collectors/process_collector.py): process telemetry
- [collectors/file_collector.py](/E:/agentic_ai/defense system/collectors/file_collector.py): filesystem event monitoring
- [collectors/network_collector.py](/E:/agentic_ai/defense system/collectors/network_collector.py): network connection telemetry
- [core/monitor.py](/E:/agentic_ai/defense system/core/monitor.py): combines all collectors

### Detection and ML

- [agents/event_enrichment.py](/E:/agentic_ai/defense system/agents/event_enrichment.py): feature enrichment
- [utils/filters.py](/E:/agentic_ai/defense system/utils/filters.py): noise reduction and trusted-process suppression
- [detectors/scoring.py](/E:/agentic_ai/defense system/detectors/scoring.py): heuristic scoring detector
- [logs/logger.py](/E:/agentic_ai/defense system/logs/logger.py): ML payload creation and aggregation boundary
- [ml/ml_models/aggregator_model/router.py](/E:/agentic_ai/defense system/ml/ml_models/aggregator_model/router.py): model routing
- [ml/ml_models/aggregator_model/aggregator.py](/E:/agentic_ai/defense system/ml/ml_models/aggregator_model/aggregator.py): streaming alert aggregation

### LLM agents

- [agents/analysis/analysis_agent.py](/E:/agentic_ai/defense system/agents/analysis/analysis_agent.py): attacker intent/stage analysis
- [agents/strategy/strategy_agent.py](/E:/agentic_ai/defense system/agents/strategy/strategy_agent.py): deception planning
- [utils/llm_client.py](/E:/agentic_ai/defense system/utils/llm_client.py): shared LLM client

### Deception and response

- [agents/deployment/deployment_agent.py](/E:/agentic_ai/defense system/agents/deployment/deployment_agent.py): decoy registry and rule creation
- [core/interception_layer.py](/E:/agentic_ai/defense system/core/interception_layer.py): real/partial/fake response decisions
- [agents/generation/generation_agent.py](/E:/agentic_ai/defense system/agents/generation/generation_agent.py): fake file content generation
- [core/path_resolver.py](/E:/agentic_ai/defense system/core/path_resolver.py): decoy path normalization and mapping

### Demos and validation

- [presentation_demo.py](/E:/agentic_ai/defense system/presentation_demo.py): step-by-step pipeline demo
- [presentation_demo_file_attack.py](/E:/agentic_ai/defense system/presentation_demo_file_attack.py): heavier file-focused attack walkthrough
- [run_all_checks.ps1](/E:/agentic_ai/defense system/run_all_checks.ps1): one-command project validation

## Requirements

### Python

- Python `>=3.13`

### Models

These model artifacts must exist:

- `ml/ml_models/file_model/file_hybrid_final.pkl`
- `ml/ml_models/process_model/process_hybrid_final.pkl`
- `ml/ml_models/network_model/network_hybrid_model.pkl`

### Environment variables

Create a `.env` file in the repo root with at least:

```env
OPENAI_API_KEY=your_key_here
```

## Installation

### Using the existing virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Fresh install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

Primary runtime configuration lives in [configs/system_config.yaml](/E:/agentic_ai/defense system/configs/system_config.yaml).

The `monitoring` section controls live file-watch behavior:

```yaml
monitoring:
  poll_interval: 1
  recursive: true
  console_reporting: true
  file_watch_paths:
    - ${USERPROFILE}\Documents
    - ${USERPROFILE}\Desktop
    - .\demo_shared
```

Use this to point the app at the folders you want to monitor on your machine.

## Running the system

### Start the live runtime

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

What you should see:

- startup banner
- version output
- monitored file paths
- periodic live incident reports when events are observed

### Run the one-command validation suite

```powershell
.\run_all_checks.ps1
```

This checks:

- environment prerequisites
- model artifact presence
- LLM configuration
- strategy tests
- deployment tests
- pipeline demo
- attacker simulation
- watcher demo
- LangGraph full cycle
- LangGraph interception mode
- `main.py` startup smoke test

## Presentation and demo commands

### Clean pipeline walkthrough

```powershell
python presentation_demo.py
```

### Realistic file-focused attack walkthrough

```powershell
python presentation_demo_file_attack.py
```

### Event-driven watcher demo

```powershell
python tests\run_event_pipeline.py
```

Then, in another terminal:

```powershell
New-Item -ItemType Directory -Force demo_shared\logs
Set-Content demo_shared\logs\sec_audit.log "trigger"
```

## Example end-to-end flow

Here is the dominant operational path:

1. Process/file/network collectors ingest telemetry.
2. Event enrichment adds features such as z-scores, rarity, trust, and frequency.
3. Filtering removes low-value noise.
4. Rule-based scoring classifies suspiciousness.
5. The logger transforms accepted detections into ML payloads.
6. File/process/network models score the events.
7. The streaming aggregator raises an alert when global risk crosses threshold.
8. The analysis agent infers intent and attack stage.
9. The strategy agent creates an executable decoy plan.
10. The deployment manager registers decoys and interception rules.
11. The interception layer returns real, partial, or fake content for a requested path.

## Strategy agent summary

The strategy agent is the planning layer between attacker understanding and deception deployment.

It:
- takes `intent`, `attack_stage`, and `confidence`
- builds a strict JSON-only LLM prompt
- forces artifact generation under a safe staging root
- constrains output by deterministic limits
- validates and repairs the plan
- falls back to a deterministic safe strategy if the model output is invalid

Important strategy files:

- [agents/strategy/strategy_agent.py](/E:/agentic_ai/defense system/agents/strategy/strategy_agent.py): main controller
- [agents/strategy/prompt_builder.py](/E:/agentic_ai/defense system/agents/strategy/prompt_builder.py): prompt and hint builder
- [agents/strategy/parser.py](/E:/agentic_ai/defense system/agents/strategy/parser.py): JSON extraction
- [agents/strategy/schema.py](/E:/agentic_ai/defense system/agents/strategy/schema.py): planning constants and limits
- [agents/strategy/validator.py](/E:/agentic_ai/defense system/agents/strategy/validator.py): safety, normalization, validation, fallback

## Notes and limitations

- The active deception response is strongest on the file side. File generation, deployment metadata, and interception are the most complete parts of the response stack.
- This project is not a kernel-level filesystem minifilter. It does not transparently replace arbitrary OS file reads for every process on the machine.
- The live runtime performs real telemetry collection, but “fake content delivery” happens through the project’s interception flow, not through OS-wide file hooking.
- The older `src/` tree is mostly legacy scaffolding and is not the main runtime path.

## Documentation

- [system_analysis.md](/E:/agentic_ai/defense system/system_analysis.md): deep codebase analysis
- [visual_flows.svg](/E:/agentic_ai/defense system/visual_flows.svg): workflow diagram

## License

This repository currently has no explicit open-source license file. If you plan to publish it publicly, add a license before release.
