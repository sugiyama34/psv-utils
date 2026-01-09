#!/usr/bin/env python3
import argparse
import os
import sys
import time
from pathlib import Path

import requests
from tqdm import tqdm

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


def main():
    SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
    CREDENTIALS = "secrets/credentials.json"
    TOKEN = "secrets/token.json"

    DRIVE_API = "https://www.googleapis.com/drive/v3/files"
    CHUNK = 128 * 1024 * 1024          # 128MB
    STREAM_CHUNK = 8 * 1024 * 1024     # 8MB
    TIMEOUT = (10, 60)                 # (connect, read)
    RETRY_SLEEP = 5

    p = argparse.ArgumentParser()
    p.add_argument("--file-id", required=True)
    p.add_argument("--port", required=True)
    p.add_argument("--out-dir", default=".")
    args = p.parse_args()

    if not os.path.exists(CREDENTIALS):
        print(f"[ERROR] {CREDENTIALS} が見つかりません。")
        sys.exit(1)

    # token.json があれば非対話で利用（refresh も自動）
    creds = None
    if os.path.exists(TOKEN):
        creds = Credentials.from_authorized_user_file(TOKEN, SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        Path(TOKEN).write_text(creds.to_json())
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
        creds = flow.run_local_server(open_browser=False, host="localhost", bind_addr="0.0.0.0", port=int(args.port))
        Path(TOKEN).write_text(creds.to_json())

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # メタデータ（name, size）
    meta = requests.get(
        f"{DRIVE_API}/{args.file_id}",
        params={"fields": "name,size"},
        headers={"Authorization": f"Bearer {creds.token}"},
        timeout=TIMEOUT,
    )
    meta.raise_for_status()
    meta = meta.json()
    name = meta["name"]
    size = int(meta["size"])

    part = out_dir / (name + ".part")
    pos = part.stat().st_size if part.exists() else 0

    # 本体（alt=media + Range）
    url = f"{DRIVE_API}/{args.file_id}"
    params = {"alt": "media"}
    pbar = tqdm(total=size, initial=pos, unit="B", unit_scale=True, desc=name)

    with open(part, "ab") as f:
        while pos < size:
            end = min(pos + CHUNK - 1, size - 1)
            headers = {
                "Authorization": f"Bearer {creds.token}",
                "Range": f"bytes={pos}-{end}",
            }

            try:
                r = requests.get(url, params=params, headers=headers, stream=True, timeout=TIMEOUT)

                # 401 になったら token 更新して1回だけやり直す（最小限）
                if r.status_code == 401 and creds.refresh_token:
                    creds.refresh(Request())
                    Path(TOKEN).write_text(creds.to_json())
                    headers["Authorization"] = f"Bearer {creds.token}"
                    r = requests.get(url, params=params, headers=headers, stream=True, timeout=TIMEOUT)

                r.raise_for_status()

                for chunk in r.iter_content(STREAM_CHUNK):
                    if chunk:
                        f.write(chunk)
                        pos += len(chunk)
                        pbar.update(len(chunk))

                f.flush()
                os.fsync(f.fileno())

            except Exception:
                time.sleep(RETRY_SLEEP)

    pbar.close()
    part.rename(out_dir / name)


if __name__ == "__main__":
    main()
