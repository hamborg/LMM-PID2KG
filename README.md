# LMM HVAC Diagram Data Extractor

Experimental digitisation framework for extracting semantic knowledge graphs (TTL) from HVAC engineering diagrams (P&ID / BMS images) with multimodal LMMs (Gemini / GPT), and for evaluating and refining the result.

The semantic knowledge graphs are based on the following ontologies:
- Building Topology Ontology, [BOT](https://w3c-lbd-cg.github.io/bot)
- Brick Schema v1.3, [Brick](https://ontology.brickschema.org/)
- Flow Systems Ontology, [FSO](https://alikucukavci.github.io/FSO/)
- Flow Properties Ontology, [FPO](https://www.researchgate.net/publication/382838849_Efficient_management_and_compliance_check_of_HVAC_information_in_the_building_design_phase_using_Semantic_Web_technologies) (journal paper)
- Semantic Sensor Network Ontology, [SOSA](https://www.w3.org/TR/vocab-ssn/)
- Quantities, Units, Dimensions, and Types Ontology, [QUDT](https://qudt.org/), specifically SI-units from the [units](https://qudt.org/vocab/unit/) vocab.

The candidate semantic knowledge graph outputs are then evaluated agains purpose-related competency questions (CQs), grouped into purpose-conditioned levels of abstraction (PCLA).

Finally, an LMM-based human-in-the-loop (HITL) refinement process can then be used to resolve imperfections according to the CQs in question.

---

The framework thus has three stages, each with its own entry point in the project root:

| Stage | Script | Purpose |
|-------|--------|---------|
| 1. Graph Extraction | `run.py` | Zero-shot LMM call on a prompt + images; saves the output as a semantic knowledge graph (`TTL`). |
| 2. CQ Evaluation | `sparql.py` | Runs SPARQL evaluation queries against a TTL graph. |
| 3. Graph Refinement | `hitl.py` | Human-in-the-loop (HITL): the user gives instructions, the LMM revises the TTL, the result is re-evaluated. |

## 1. Project structure (high level)

```text
├── auth/
│   ├── config.example.yaml     Template for config.yaml
│   └── config.yaml             Model settings (gitignored)
├── .env                        API keys (gitignored)
├── install/
│   ├── ps.ps1                  Activate the virtual environment (PowerShell)
│   └── cmd.bat                 Activate the virtual environment (cmd)
├── src/lmm_fw/                 LMM framework package (providers, multimodal parts, strategies, settings)
├── experiments/
│   ├── lvl_0 ... lvl_4/        Experiment data, one folder per experiment (see section 5)
│   ├── run_experiment.py       Experiment runner used by run.py
│   ├── run_logger.py           runs.jsonl logging and timer
│   └── ttl_extract.py          Extracts the TTL block from model output
├── sparql_queries/
│   ├── queries/                *.rq evaluation queries (A_, V_, H_, Z_ prefixes)
│   ├── PCLA/                   Query groups (pcla_groups.yaml) and lookup code
│   ├── run_query.py            Query runner used by sparql.py
│   └── query_logger.py         sparql_runs.jsonl logging
├── hitl_refinement/            HITL session logic (loop, prompting, workspace, evaluation)
│   └── templates/              initial_prompt.md and the evaluation scheme workbook template
├── hitl/                       HITL session output (contents gitignored)
├── utils/default_settings.py   All CLI defaults in one place (class `Default`)
├── run.py  sparql.py  hitl.py  Entry points
└── pyproject.toml
```

## 2. Environment setup

Run everything from the project root. All scripts use paths relative to it.

### 2.1 Create the virtual environment (once)

```cmd
python -m venv .venv
```

### 2.2 Activate it (every new shell)

The `install/` folder has small activation helpers. They check that `.venv` exists and then activate it.

**PowerShell**
```powershell
. .\install\ps.ps1
```
Note the leading `. ` (dot-sourcing). Without it, the script runs in a child scope and the activation is lost when it ends. If PowerShell blocks the script, allow it for the current session with
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

**cmd**
```cmd
install\cmd.bat
```

**macOS / Linux** (no helper provided)
```bash
source .venv/bin/activate
```

If `.venv` is missing, both helpers stop with a "Virtual environment not found" message. Go back to 2.1.

### 2.3 Install dependencies (once)

```cmd
pip install -e .
```

This installs the `lmm_fw` package (in `src/`) in editable mode, plus `google-genai`, `openai`, `PyYAML`, `rdflib`, `questionary` and `openpyxl`.

## 3. Configuration

Two files, with different roles:

- **`.env`**: API keys only.
- **`auth/config.yaml`**: provider, model and sampling settings. It refers to the keys in `.env`.

Both are gitignored. `auth/config.example.yaml` is the tracked template.

```bash
cp auth/config.example.yaml auth/config.yaml     # PowerShell: Copy-Item
```

Create `.env` in the project root:

```text
GEMINI_API_KEY=...
OPENAI_API_KEY=...
```

The format is plain `NAME=value` lines (optional quotes, `#` comments). Instead of `.env` you can export the same variables in your shell (`$env:GEMINI_API_KEY = "..."` in PowerShell, `export GEMINI_API_KEY=...` in bash).

In `config.yaml`, a key is referenced as `api_key: ${GEMINI_API_KEY}`. When `run.py` or `hitl.py` selects an LMM client, `load_config()` reads `.env` from the current working directory (so run from the project root) and expands these references. `sparql.py` makes no LMM calls and does not load either file. Variables already set in the real environment take precedence over `.env`, and a real key written directly in the YAML wins over both. Placeholder values (anything starting with `YOUR_`, `<`, `CHANGEME` or `REPLACE_ME`) count as not set and fall back to the environment variable.

> **Note:** `.env` and `config.yaml` are replicated too. Never commit real keys. If a key has been exposed, rotate it.

> **Known limitation:** `load_config()` requires *both* keys, even when you only run one provider.

Model, temperature and thinking level are set per provider in `config.yaml`. The default provider is set by `default_provider` there. The CLI default (`--provider`) is set in `utils/default_settings.py`.

## 4. Typical workflow

1. Activate the environment (section 2.2).
2. Add or pick an experiment folder under `experiments/lvl_X/` (section 5).
3. `python run.py ...` to extract a TTL (section 6).
4. `python sparql.py ...` to evaluate it (section 7).
5. `python hitl.py ...` to refine it interactively (section 8).

## 5. Experiment folders

Experiments are organised by level (`lvl_0` to `lvl_4`). An experiment is a folder named with a two-digit number prefix, e.g. `experiments/lvl_1/02 5704 køkken VEN-9.03/`. It is selected on the command line by its number only (`-l 1 -e 2`). Folder names contain spaces and non-ASCII characters, so quote paths in the shell.

```text
experiments/lvl_1/02 5704 køkken VEN-9.03/
├── prompt_main.md              Prompt files: prompt.md, or prompt_<name>.md
├── prompt_mod.md
├── images/                     Input images, sorted by filename (01_diagram, 02_legend, 03_titleblock, ...)
├── Outputs/                    Full model outputs (.txt), written by run.py
├── Query_results/              SPARQL results, written by sparql.py
├── Edits/                      Manually edited source files (PDF/PNG)
├── L1E2 main - 03.16_15.41.ttl Extracted TTL files, written by run.py
├── runs.jsonl                  One record per LMM run
└── sparql_runs.jsonl           One record per SPARQL run
```

Supported image formats are `.png`, `.jpg`, `.jpeg` and `.webp`.

**Version control:** `.gitignore` tracks only `images/` (excluding its subfolders) and the `prompt*.md` files in `lvl_1` and `lvl_2`. `lvl_3`, `lvl_4` and `experiments/Ideer.txt` are ignored entirely, and `hitl/` is ignored except for `.gitkeep`.

## 6. Running experiments: `run.py`

```bash
python run.py -l 1 -e 2 -p main
```

This looks in `experiments/lvl_1/`, finds the folder starting with `02`, reads `prompt_main.md` and all images in `images/`, makes one zero-shot LMM call and saves the results.

| Flag | Meaning |
|------|---------|
| `-l`, `--lvl` | Level 0-4 (default 1) |
| `-e`, `--exp` | Experiment number(s). Required. Several allowed: `-e 1 2 3` |
| `-m`, `--provider` | `gemini` (default) or `gpt` |
| `-p`, `--prompt` | Prompt suffix(es). `-p main` uses `prompt_main.md`. Without `-p` the file must be named `prompt.md` |
| `-r`, `--runs` | Repeated runs per experiment (default 1, max 25) |
| `-n`, `--comment` | Note appended to the output filename |
| `-t`, `--no-timestamp` | Leave the timestamp out of the output filename |

If a run combination totals more than one run, you are asked to confirm (and optionally reduce to 1 run each). More than four runs requires explicit confirmation because of API rate limits.

Output files in the experiment folder:

- `Outputs/L<lvl>E<exp> [<prompt>] [- <timestamp>] [<note>].txt`: full model output.
- `L<lvl>E<exp> [...].ttl`: extracted Brick TTL (same base name), written to the experiment folder. If no TTL block is found, no `.ttl` is written.
- `runs.jsonl`: provider, model, prompt file and length, number of images, execution time (s), output filename, UTC timestamp. Suitable for later analysis with pandas.

## 7. Evaluating a TTL with SPARQL: `sparql.py`

```bash
python sparql.py -l 1 -e 4 -q A_01 V_01
python sparql.py -l 1 -e 4 -g 1 2          # all queries in PCLA groups 1 and 2
python sparql.py -l 1 -e 4 --hitl          # the default HITL query set
```

The script asks you to pick one of the `.ttl` files in the experiment folder, then runs the queries on it.

| Flag | Meaning |
|------|---------|
| `-l`, `-e` | Level and experiment (one experiment only) |
| `-q`, `--query` | Query IDs matching files in `sparql_queries/queries/` (default `A_00`, all components) |
| `-g`, `--pcla` | Run all queries in PCLA groups 0-7 (overrides `-q`) |
| `--hitl` | Run the default HITL queries (overrides `-q`) |
| `-n` | Note appended to the output filename |
| `-f`, `--format` | `csv` (default) or `json` |

Results are written to the experiment's `Query_results/` and logged in `sparql_runs.jsonl`.

Queries are named `<prefix>_<nn>_<description>.rq`: `A` = generic, `V` = ventilation, `H` = heating, `Z` = building / zones. PCLA groups (`sparql_queries/PCLA/pcla_groups.yaml`) bundle related checks, e.g. location, system membership, flow.

## 8. Human-in-the-loop refinement: `hitl.py`

Starts from an existing TTL, then repeats: you type an instruction → the LMM returns a revised TTL → the SPARQL evaluation queries are re-run → results are written to the evaluation scheme workbook.

```bash
python hitl.py -l 1 -e 4                    # new session (asks which TTL to start from)
python hitl.py -l 1 -e 4 -s A -q A_01 V_01  # mode A, custom evaluation queries
python hitl.py -c                           # continue/branch an existing session (interactive)
python hitl.py -c latest                    # branch from the latest turn
```

| Flag | Meaning |
|------|---------|
| `-l`, `-e` | Level and experiment (one experiment only; default experiment `04`) |
| `-m`, `--provider` | `gemini` (default) or `gpt` |
| `-q`, `--query` | Evaluation queries (default `A_01 V_01 Z_02 V_12 Z_01`) |
| `-s`, `--mode` | `A` = conversational memory (earlier instructions are replayed); `B` = stateless iterative refinement (default) |
| `-n` | Note appended to the session name |
| `-c`, `--continue` | Continue from an earlier session. Optionally `latest` |

An empty instruction ends the loop.

Each session is stored in `hitl/L<lvl>_E<exp>/ses_<timestamp>_<mode>[_note]/`:

```text
source/                 Copy of the images and starting TTL (+ baseline evaluation, T0)
turns/turn_NN/          instruction.txt, input_ttl.ttl, output_raw.txt, output_ttl.ttl
evaluations/            Per-turn query results (CSV) and "Evaluation scheme.xlsx"
session_config.json     Session settings
session_log.jsonl       Per-turn log
```

Continuing a session never modifies the old one. It creates a new branched session named `<session>__from_tNN`.

## 9. Defaults

All CLI defaults (provider, level, runs, timestamp format, default queries, HITL experiment and mode, file names) are defined in the `Default` class in `utils/default_settings.py`. Change them there.
