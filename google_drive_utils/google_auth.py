#!/usr/bin/env python3
import os
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes that allow both download and upload operations
DEFAULT_DRIVE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/drive.file",
]


def get_drive_credentials(
    *,
    port: int = 8100,
    scopes=None,
    credentials_path: str = "secrets/credentials.json",
    token_path: str = "secrets/token.json",
):
    if scopes is None:
        scopes = DEFAULT_DRIVE_SCOPES

    if not os.path.exists(credentials_path):
        raise FileNotFoundError(f"Credentials not found: {credentials_path}")

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)
        if not creds.has_scopes(scopes):
            os.remove(token_path)
            creds = None

    if creds and creds.expired and creds.refresh_token:
        if not _refresh_token(creds, token_path):
            creds = None

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
        creds = flow.run_local_server(
            open_browser=False, host="localhost", bind_addr="0.0.0.0", port=int(port)
        )
        Path(token_path).write_text(creds.to_json())

    return creds


def request_with_refresh(request_fn, creds, token_path: str):
    response = request_fn(creds.token)

    if response.status_code == 401 and creds.refresh_token:
        if _refresh_token(creds, token_path):
            response = request_fn(creds.token)

    return response


def _refresh_token(creds, token_path: str) -> bool:
    try:
        creds.refresh(Request())
        Path(token_path).write_text(creds.to_json())
        return True
    except Exception:
        if os.path.exists(token_path):
            os.remove(token_path)
        return False
