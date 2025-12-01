Plan: Use `llms.txt` context to update and standardize the ADK healthcare project

Goal
- Use the information in `llms.txt` (ADK guidance, recommended models, A2A patterns) to update the project in small, auditable steps.

Context
- `llms.txt` documents ADK usage recommendations, example agent patterns, model suggestions (e.g., `gemini-2.5-flash`), and A2A guidance. This plan focuses on pragmatic repo changes that align with that context.

High-level Tasks
1. Standardize model settings
   - Set a single `MODEL_NAME` variable (recommended: `gemini-2.5-flash`) and ensure all agents import and use it.
   - Files impacted: `agent.py`, `subagents/*/agent.py`, `agents/gov_audit_agent.py`.

2. Move root agent instruction to `prompts/root_prompt.py`
   - Create `prompts/root_prompt.py` with a `ROOT_AGENT_INSTRUCTION` variable containing the root agent's instruction text (pulled from `llms.txt` + repository-specific rules like security/A2A).
   - Update `agent.py` to import and use `ROOT_AGENT_INSTRUCTION`.
   - Rationale: centralize prompt text for easier edits and reuse.

3. Ensure subagents forward record-requests to root (sentinel)
   - Confirm each subagent has the sentinel routing text appended to its `instruction` (or mutate at startup) so they return `__FORWARD_TO_ROOT__` when asked to "show records".
   - Files impacted: `subagents/ent/agent.py`, `subagents/gynec/agent.py`, `subagents/generalphysician/agent.py` (or central mutation in `agent.py`).

4. A2A communication using Runner.run_async only (no `google.adk.client` dependency)
   - Use `Runner.run_async` (content messages) for A2A flows between `agents/gov_audit_agent.py` and the root runner.
   - Ensure audit agent creates its own session and the root runner has the audit session created ahead of time to avoid "Session not found".
   - Files impacted: `agents/gov_audit_agent.py`, `test_audit_agent.py`.

5. Add or update `audit_server.py` (FastAPI)
   - Ensure a robust template that avoids `str.format()` pitfalls (use `.replace()` or f-strings safely) and that it reads from `healthcare.db`.
   - Add a friendly homepage and `/audit-report` and `/api/records` endpoints.

6. Requirements and developer notes
   - Add `google-adk` to `requirements.txt` only if you want to rely on it; otherwise document the project works without `google.adk.client` and uses only the runner/session APIs.
   - Add a short note to `README.md` referencing `llms.txt` for ADK guidance.

Acceptance Criteria
- `MODEL_NAME` is unified across agents.
- `prompts/root_prompt.py` exists and `agent.py` imports `ROOT_AGENT_INSTRUCTION` (no inline bulk instruction text remains in `agent.py`).
- Subagents return the sentinel when asked to show records (either in their instruction or mutated at runtime).
- `agents/gov_audit_agent.py` implements A2A via `Runner.run_async` only and succeeds when run via `test_audit_agent.py`.
- `audit_server.py` serves the homepage and audit report without template errors and displays records from `healthcare.db`.
- `README.md` references `llms.txt` and documents the chosen `MODEL_NAME` and A2A approach.

Next steps (if approved)
- Implement Step 1 (MODEL_NAME) and run unit smoke tests.
- Implement Step 2 (prompts file) and update `agent.py` accordingly.
- Implement Step 3 (sentinel) and test "show records" flows from subagents.
- Implement Step 4 (A2A runner-only) and test via `test_audit_agent.py`.
- Implement Step 5 (audit server) and validate web UI.
- Optionally add persistent session DB (SQLite) and logging for audit accesses.

Notes
- Keep changes small and test after each step.
- Prefer modifying `agent.py` to mutate sub-agent `.instruction` at startup if you want a single change rather than editing many sub-agent files.
- Avoid introducing `google.adk.client` if you prefer to keep fewer dependencies; the plan supports a runner-only A2A approach.

-- End of plan --
