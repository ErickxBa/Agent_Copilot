# Agent_Banca: Financial Reconciliation PoC

## Project purpose

This repository contains a hybrid reconciliation proof of concept for
payment-gateway reports, general-ledger records, and central-bank statements
to identify discrepancies and evidence-backed orphan transactions, then
produce verifiable analyst reports. The current proof of concept (PoC) uses
synthetic bank, payment-gateway, and general-ledger records. Pandas performs
deterministic matching first; the AI model receives only unresolved records in
bounded batches. The PoC does not yet ingest official central-bank formats and
is not a production banking or AML decision system.

## Current architecture

- `src/orchestrator.py` is the hybrid entry point. It loads the JSON source
  reports into Pandas DataFrames, applies deterministic AML screening, matches
  bank-to-ledger records on exact payout ID, currency, amount, and UTC date,
  and matches gateway net settlements using the documented per-transaction fee
  and 48-hour timing rules. Fully matched and AML-quarantined payouts are
  excluded from the exceptions queue. The OpenAI-compatible model receives
  only unresolved, non-quarantined records, in batches of at most 20, and is
  prohibited from returning deterministic matches or AML alerts. Its exception
  reports are schema- and consistency-validated before consolidation. Final
  reports are saved as JSON in `output/`.
- `data/poc_bank.json`, `data/poc_gateway.json`, and `data/poc_ledger.json` are
  the fixtures used by the orchestrator.
- `agent_config/system_prompt.md` defines the auditor role and JSON output
  contract. `agent_config/skills/` holds fee/timing and AML instructions.
- `agent_config/skills/reconciliation_analysis.md` documents the current
  runtime input schema, evidence-first workflow, and batch-completeness limits;
  `src/orchestrator.py` includes it in the runtime model context.
- `.github/copilot-instructions.md` defines repository-wide development
  standards for Copilot. `.github/agents/conciliacion-auditoria.agent.md`
  defines the VS Code Copilot agent for reconciliation engineering; it is
  separate from the runtime auditor prompt in `agent_config/`.
- `.github/skills/reconciliation-engineering/SKILL.md` is the workspace
  general Agent Skill for engineering tasks. The workspace also provides
  focused skills for source-format validation, evidence-based exception
  analysis, and audit reporting. VS Code discovers project skills from
  `.github/skills/` and loads relevant skills on demand. These are engineering
  guidance, not new reconciliation rules or source-format support; runtime
  model instructions in `agent_config/` are not Copilot Agent Skills.
- `src/copilot_app.py` is a local Streamlit interface branded **Agent
  Concilation** for testing the custom VS Code Copilot agent.
  `src/copilot_backend.py` uses the official Copilot SDK
  for CLI-based authentication checks and persistent chat sessions; it loads
  the agent and workspace skills from `.github/`. This test interface is
  separate from `src/orchestrator.py`, does not run reconciliation, and does
  not use `OPENAI_MODEL`, Ollama, or `ALLOW_REMOTE_ENDPOINT`. Chat replies are
  taken from the Copilot SDK's final response event; chunked replies are
  reconstructed only from events with that response's message ID rather than
  inferred from an unrelated transcript entry.
- `src/copilot_app.py` also separates two upload workflows: one `.txt` or
  `.json` file can be sent as context to the Copilot agent for an explanation,
  or three source files can be passed to the existing reconciliation
  orchestrator. Each upload is limited to 1 MiB. Reconciliation uploads must
  contain the existing `records` JSON structure; `.txt` is not CSV or free
  text. The three uploaded files are staged temporarily and the report is
  offered as an explanatory PDF with section definitions, summary counts, and
  source-record references; the detailed JSON remains available for download.
  PDF explanations use fixed application text, not model-generated analysis.
  Unresolved records may be sent to the configured OpenAI-compatible endpoint
  under the existing `ALLOW_REMOTE_ENDPOINT` guard.
- The Copilot chat accepts a single `.txt` or `.json` attachment directly in
  the chat composer. Users can toggle the general reconciliation-engineering
  skill and the focused source-format-validation,
  exception-evidence-analysis, and audit-reporting skills. The UI/UX skill
  remains available for development guidance but is disabled in application
  chat sessions. Toggle state controls skill availability, not evidence that
  a skill was actually activated for a response.
- The Streamlit workspace presents a `Fuentes` panel for Copilot connection,
  sessions, and skill controls, a central conversation with an attachment
  composer, and a `Studio` panel that explains the product goal and PoC limits.
  Reconciliation remains a separate `Conciliar reportes` view.
- The Streamlit UI follows the workspace `ui-ux-design-system` development
  skill and uses `src/assets/global.css` as its centralized visual-token and
  component-style source. The base colors in `.streamlit/config.toml` align
  with these tokens. This development skill is not exposed in application chat.
- Copilot chat requests include a project-scope instruction and uploaded file
  contents are identified as untrusted reference data. This guides the model
  to stay within Agent_Banca topics but is not a deterministic topic filter.
- `docs/agent-architecture.md` explains the separate VS Code Copilot and
  application-auditor flows, their context sources, and how each is executed,
  including the local SDK test interface.
- `docs/compliance_aml_rules.md` is the illustrative AML knowledge base used by
  the AML skill.
- `.github/workflows/ci.yml` runs offline validation and unit tests. CI must
  never require API keys or send fixture data to an external model.

## Scope and limitations

- The current fixtures contain 12 bank records, 11 gateway records, and 13
  ledger records. They do not establish production-scale throughput.
- Pandas loads each complete JSON report into memory; the model calls are
  limited to at most 20 records, but this is a record-count limit, not a token
  limit. Long descriptions or unusually large records may still exceed a
  provider's context or request limits. Ingestion is not streaming and has no
  database-backed checkpointing or retry workflow.
- Deterministic matching is limited to the explicit payout, currency, amount,
  UTC-date, fee, and settlement-time rules implemented in the orchestrator.
  Other exception interpretation remains probabilistic and requires analyst
  review.
- The output is persisted as JSON, but there is no reconciliation analyst
  interface, CSV export, or workflow for reviewing and approving findings.
  The local Copilot test interface is a developer smoke-test tool, not an
  analyst case-management UI.
- Before production use, benchmark representative data volumes, establish
  accounting-specific rules and controls, and add operational monitoring,
  access control, and analyst review tooling.

## Run locally

1. Use Python 3.11 or newer.
2. Install dependencies: `python -m pip install -r requirements.txt`.
3. Copy `.env.example` to `.env`.
4. Choose one endpoint in `.env`:
   - **Local:** start Ollama and make the configured model available. Defaults
     use `http://localhost:11434/v1` and `llama3.1`.
   - **Remote GroqCloud:** create an account/API key, then replace the local
     endpoint, key, and model with the commented Groq example in `.env.example`
     and set `ALLOW_REMOTE_ENDPOINT=true`. `openai/gpt-oss-20b` is listed by
     Groq as supporting structured output, but free access, rate limits, and
     model availability depend on the account and may change.
5. Run `python src/orchestrator.py` on the machine that has the source reports.

The client uses the OpenAI-compatible Chat Completions API. `OPENAI_BASE_URL`,
`OPENAI_API_KEY`, and `OPENAI_MODEL` configure the endpoint and model. Remote
endpoints are refused unless `ALLOW_REMOTE_ENDPOINT=true` is explicitly set.
For remote inference, only unresolved, non-quarantined exception records are
sent, but those records still leave the machine. Do not send real financial
data unless the provider's privacy, retention, security, and contractual
controls have been reviewed and approved. Free-tier usage is not guaranteed to
be sufficient for bulk processing.

## Probar el agente personalizado de Copilot

This is a separate developer-only chat path; it does not run
`src/orchestrator.py` or prove reconciliation behavior.

1. Install the project dependencies as above.
2. Authenticate with Copilot CLI in a terminal by running `copilot` and
   completing the sign-in flow. The web interface never accepts or stores
   credentials or tokens.
3. From the repository root, run:

   ```bash
   streamlit run src/copilot_app.py
   ```

4. In the page, check the Copilot authentication status, acknowledge the
   service-processing notice, and create a conversation. Existing conversations
   created by this interface can be listed and resumed.

The interface selects the custom agent in
`.github/agents/conciliacion-auditoria.agent.md`, loads workspace skills from
`.github/skills/`, and restricts available tools to `view`, `grep`, and `glob`.
It does not provide shell or editing tools and the Streamlit server binds to
loopback by default. The SDK uses the Copilot CLI identity and its configured
model, not `OPENAI_API_KEY`, `OPENAI_MODEL`, or the Ollama endpoint. The SDK
persists session transcripts locally according to its configuration. Messages
and any repository content the agent reads may be processed by Copilot under
the user's account policies; use synthetic data only. This separate Copilot
path is not governed by the application's `ALLOW_REMOTE_ENDPOINT` privacy
guard.

## Privacy and compliance boundaries

- The default endpoint is loopback-only; data is not intentionally sent to a
  hosted provider by default. Local execution alone is not a guarantee of
  zero retention: review local model, server, and application logs.
- Use synthetic fixtures in development and CI. Never put secrets in source
  control; `.env` is ignored by Git.
- AML thresholds are illustrative test rules, not legal advice or a finding of
  wrongdoing. Alerts require a qualified human compliance review.
- The model must not initiate payments, post ledger entries, block accounts,
  or file regulatory reports.
- Keep financial arithmetic and required controls deterministic and validate
  the model output before downstream use. The model's JSON response is not a
  substitute for independent production-grade reconciliation controls.

## Development and validation

Run the offline test suite with:

```bash
python -m unittest discover -s tests -v
```

CI checks Python syntax, fixture JSON, and unit tests without calling Ollama,
Groq, or any other model endpoint.

To use alternate reports with the same expected JSON filenames, set
`RECONCILIATION_DATA_DIR`. Set `AUDIT_OUTPUT_DIR` to change the report
destination. Inputs may use the expected `.json` filenames or `.txt` filenames
whose contents are valid JSON with the same schema; `.txt` does not mean CSV or
arbitrary plain text. If both extensions exist for a source, `.json` takes
precedence. See `data/txt_samples/` for a small synthetic example that runs
without unresolved records or a model call.

The larger fixtures in `data/poc_bank.json`, `data/poc_gateway.json`, and
`data/poc_ledger.json` cover amount/date/currency discrepancies, multi-record
gateway settlements, fee-window cases, an unmatched ledger record, and
illustrative AML scenarios. The interactive reconciliation page may call the
configured model for unresolved exceptions; use the offline orchestrator tests
to exercise these cases without a model endpoint:

```bash
python -m unittest discover -s tests -p test_orchestrator.py -v
```

The product objective is to reconcile payment-gateway reports, ledger records,
and central-bank statements; identify discrepancies and evidence-backed
orphans; and give analysts verifiable reports. Current implementation remains
at synthetic PoC scale: deterministic matching and AML screening run locally,
unresolved exceptions may be sent to a configured model, and a JSON report is
persisted for later review. It is not a mass-processing or analyst
case-management solution. The requirements status below describes current
implementation, not business or compliance approval:

- The only available inputs are three small synthetic JSON fixtures:
  `data/poc_bank.json` (12 records), `data/poc_gateway.json` (11), and
  `data/poc_ledger.json` (13). They include exact and fee matches, aggregated
  gateway payouts, a one-cent fee discrepancy, UTC-date and currency
  discrepancies, a late settlement, an existing unmatched ledger record, and
  an AML threshold-boundary example. No specific bank, payment gateway, ledger
  vendor, central bank institution/jurisdiction, or official external file
  format has been selected. In particular, no central-bank statement adapter
  is implemented.
- The fixture fields are documented by their contents and
  `SOURCE_FIELDS` in `src/orchestrator.py`. A `payout_id` is the current
  cross-source key. Commission, status, and a separate settlement reference
  are not input fields in the current schema.
- The runtime auditor's knowledge is a set of Markdown documents loaded and
  concatenated by `load_markdown_context()`; it is not a vector database, RAG
  index, trained model, or institution-specific knowledge system. The model
  receives unresolved records separately in batches, not the complete source
  reports.
- Current code matches bank-to-ledger on payout ID, currency, amount, and UTC
  calendar date; bank-to-gateway uses the hard-coded fee and settlement-window
  rules described above. These are PoC implementation rules, not user-approved
  accounting policy. Cross-currency conversion is not supported.
- Reports are timestamped JSON files written locally to `output/`. The
  analyst workflow beyond later/manual report review, retention, and
  production storage/access controls have not been approved or implemented.
- Remote model use is opt-in and guarded by `ALLOW_REMOTE_ENDPOINT`; no
  approval to send real financial data to an external model has been given.
- AML thresholds are illustrative only and require human review. They are not
  approved jurisdiction-specific rules.
- Production volumes, run frequency, performance/memory/concurrency targets,
  representative benchmark data, and formal acceptance criteria remain
  unspecified. Automated retries, checkpoint recovery, and idempotent
  execution behavior are also not established as requirements.

When answering or implementing against this product objective, use these known
facts to avoid asking already-answered questions. Ask for missing decisions
only when they affect the requested change. The user has stated the desired
source categories and outcome; the institution, official formats, accounting
rules, scale targets, operational controls, and acceptance criteria remain
unconfirmed. Do not interpret suggestions made during requirements discovery
as approved policy unless the user explicitly confirms them.
