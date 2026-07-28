# ProofChain UI Gateway

FastAPI sidecar that projects persisted ProofChain artifacts and dispatches only
explicitly allowlisted CLI commands as asynchronous jobs.

## Quickstart

```bash
cd C:\SideQuest\ProofChain
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[api]"
cd ui_gateway
uvicorn app.main:app --port 8000 --reload
```

## Security Guarantees
1. **Artifact-backed reads:** Missing artifacts return `404`; the gateway never invents run data.
2. **Path boundaries:** Run identifiers cannot escape the configured run directory.
3. **Allowlisted dispatch:** Commands use argument arrays with `shell=False`; undeclared
   fields are rejected.
4. **Observable jobs:** Command jobs expose queued, running, completed, and failed states
   plus the actual CLI exit code and parsed result.
5. **Separated health:** Platform health and accreditation readiness are reported
   independently.
