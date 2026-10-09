# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Research framework for extracting Brick-schema TTL (RDF) from HVAC P&ID / BMS diagram images using multimodal LMMs (Gemini / GPT), then refining the result with a human-in-the-loop (HITL) process. Three entry-point scripts at the repo root form a pipeline:

1. `run.py` – zero-shot LMM call on an experiment's `prompt.md` + `images/`, extracts TTL from the model output.
2. `sparql.py` – runs SPARQL evaluation queries against an experiment's `.ttl`.
3. `hitl.py` – iterative human-driven refinement of a TTL with the LMM, evaluating with SPARQL after each turn.

## Setup and commands

Windows; the project lives in a OneDrive-synced folder. Activate the venv with `.venv\Scripts\activate` (or `install/ps.ps1` / `install/cmd.bat`), then `pip install -e .` from the root.

- API keys: prefer env vars `GEMINI_API_KEY` / `OPENAI_API_KEY`; `auth/config.yaml` (gitignored, copy from `auth/config.example.yaml`) overrides if it holds a real key. `load_config()` currently requires *both* keys even for a single provider.
- Run an experiment: `python run.py -l 2 -e 3 [-m gemini|gpt] [-r N] [-p <prompt-suffix>] [-n note] [-t]` (`-e` accepts multiple; `-p v2` → `prompt_v2.md`).
- Run SPARQL: `python sparql.py -l 1 -e 4 -q A_01 V_01` or `-g <PCLA group 0-7>`, `--hitl` for the default HITL query set, `-f csv|json`. Prompts interactively (questionary) to pick which `.ttl` in the experiment folder.
- HITL: `python hitl.py -l 1 -e 4 -s B [-q queries...] [-n note]`; `-c` / `-c latest` continues or branches an existing session.
- There is no test suite or linter configured.
- `pyproject.toml` only declares `google-genai`, `openai`, `PyYAML`, but the code also imports `rdflib` and `questionary` — install them if missing.

## Architecture

- `src/lmm_fw/` – installable package (`pip install -e .`, `src` layout; VS Code `extraPaths` points at it). `choose_lmm.choose_LMM()` returns a `BaseLMMClient` (`providers/gemini_client.py`, `openai_client.py`); `multimodal/` builds image/text parts; `strategies/` has zero_shot / few_shot prompting; `settings.py` loads `auth/config.yaml`.
- `experiments/` – both the runner code (`run_experiment.py`, `run_logger.py`, `ttl_extract.py`) and the data. Data is organised as `experiments/lvl_N/NN <name>/` (level 0–4 = increasing difficulty; experiments are located by their numeric prefix, so `-e 3` matches the folder starting `03`). Each holds `prompt.md`, `images/` (ordered by filename: `01_diagram`, `02_legend`, `03_titleblock`), source PDFs/PNGs, and generated `output_<provider>_<run>.txt/.ttl` plus `runs.jsonl` timing logs. Folder names are Danish and contain spaces/non-ASCII characters — quote paths.
- `sparql_queries/` – `queries/*.rq` evaluation queries named by prefix (A = all/generic, V = ventilation, H = heating, Z = building/zone) + number; `run_query.py` executes them with rdflib; `PCLA/pcla_groups.yaml` + `pcla_queries.py` group queries into PCLA check groups (yaml uses `A01`, files use `A_01`; code maps between them).
- `hitl_refinement/` – HITL loop. `run_hitl.py` creates a session (`workspace.py`, `hitl_session.py`), `hitl_loop.py` loops: prompt the user for an instruction → `hitl_prompting.py` builds LMM parts from `templates/initial_prompt.md` + TTL + images → `ttl_manager.py` saves/extracts the new TTL → `graph_evaluation.py` runs the SPARQL evaluation queries → `evaluation_scheme_manipulator/update_scheme.py` writes results into the session's `Evaluation scheme.xlsx`. `continue_hitl.py` resumes or branches (`__from_tNN`) a prior session.
  - Mode **A** = conversational memory (prior instructions replayed in the prompt); mode **B** = stateless iterative refinement (only latest TTL + instruction). Default is B.
  - Session output lives in `hitl/L<level>_E<exp>/ses_<timestamp>_<mode>[_note]/` with `source/`, `turns/turn_NN/` (`instruction.txt`, `input_ttl.ttl`, `output_raw.txt`, `output_ttl.ttl`), `evaluations/turn_NN/*.csv`, `session_config.json`, `session_log.jsonl`.
- `utils/default_settings.py` – single `Default` class holding all CLI defaults (provider, level, default HITL experiment `"04"`, HITL queries, mode, filenames). Change defaults there rather than in the argparse code.

## Notes

- Root scripts import top-level packages (`utils`, `experiments`, `hitl_refinement`, `sparql_queries`) by relative-to-root name, so run them from the project root.
- HITL session folders and experiment outputs are research data; don't delete or rewrite them.
