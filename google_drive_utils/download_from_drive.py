#!/usr/bin/env python3
import argparse
import os
import sys
import time
from pathlib import Path

import requests
from tqdm import tqdm

from google_auth import get_drive_credentials, request_with_refresh


def main():
    CREDENTIALS = "secrets/credentials.json"
    TOKEN = "secrets/token.json"

    DRIVE_API = "https://www.googleapis.com/drive/v3/files"
    CHUNK = 128 * 1024 * 1024          # 128MB
    STREAM_CHUNK = 8 * 1024 * 1024     # 8MB
    TIMEOUT = (10, 60)                 # (connect, read)
    RETRY_SLEEP = 5

    p = argparse.ArgumentParser()
    p.add_argument("--file-id", required=True)
    p.add_argument("--port", default=8100, type=int)
    p.add_argument("--out-dir", default=".")
    args = p.parse_args()

    # token.json があれば非対話で利用（refresh も自動）
    try:
        creds = get_drive_credentials(
            port=args.port, credentials_path=CREDENTIALS, token_path=TOKEN
        )
    except FileNotFoundError:
        print(f"[ERROR] {CREDENTIALS} が見つかりません。")
        sys.exit(1)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # メタデータ（name, size）
    meta = request_with_refresh(
        lambda token: requests.get(
            f"{DRIVE_API}/{args.file_id}",
            params={"fields": "name,size"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=TIMEOUT,
        ),
        creds,
        TOKEN,
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

            try:
                r = request_with_refresh(
                    lambda token: requests.get(
                        url,
                        params=params,
                        headers={
                            "Authorization": f"Bearer {token}",
                            "Range": f"bytes={pos}-{end}",
                        },
                        stream=True,
                        timeout=TIMEOUT,
                    ),
                    creds,
                    TOKEN,
                )

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
