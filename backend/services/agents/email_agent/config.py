import os
import logging
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

# Load local .env only for local development (harmless in Cloud Run)
load_dotenv(find_dotenv())

# Resolve a path: expand ~ and, if relative, resolve relative to the repository root.
# Repo root is assumed to be 4 parents up from this file (backend/services/agents/email_agent -> repo root).
def _abs_path(p: str | None) -> str | None:
    if not p:
        return None
    p = os.path.expanduser(p)
    path = Path(p)
    if not path.is_absolute():
        repo_root = Path(__file__).resolve().parents[4]
        path = repo_root / path
    return str(path.resolve())

# Read environment variables (Cloud Run recommended: set these as environment variables or use Secret Manager)
GMAIL_CREDENTIALS_FILE = _abs_path(os.environ.get("GMAIL_CREDENTIALS_FILE", "backend/gmail_oauth_credentials.json"))
GMAIL_TOKEN_FILE = _abs_path(os.environ.get("GMAIL_TOKEN_FILE", "backend/gmail_token.json"))

# If files are missing, emit a clear warning so deploy-time logs help debugging.
for name, path in (("GMAIL_CREDENTIALS_FILE", GMAIL_CREDENTIALS_FILE), ("GMAIL_TOKEN_FILE", GMAIL_TOKEN_FILE)):
    if path and not Path(path).exists():
        logging.warning(
            "%s resolved to %s but the file does not exist. On Cloud Run consider using Secret Manager or mounting the credentials into the container.",
            name,
            path,
        )
