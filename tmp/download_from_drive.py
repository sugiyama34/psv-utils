#!/usr/bin/env python3
import argparse
import os
import sys
import time
from pathlib import Path

import requests
from tqdm import tqdm


def main():
    DRIVE_API = "https://www.googleapis.com/drive/v3/files"
    CHUNK = 128 * 1024 * 1024          # 128MB
    STREAM_CHUNK = 8 * 1024 * 1024     # 8MB
    TIMEOUT = 60
    RETRY_SLEEP = 5

    p = argparse.ArgumentParser()
    p.add_argument("--file-id", required=True)
    p.add_argument("--api-key", default=os.environ.get("GOOGLE_API_KEY"))
    p.add_argument("--out-dir", default=".", help="出力先フォルダ（既存 or 自動作成）")
    args = p.parse_args()

    if not args.api_key:
        print("[ERROR] --api-key か環境変数 GOOGLE_API_KEY を指定してください。")
        sys.exit(1)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # メタデータ（name, size）
    meta = requests.get(
        f"{DRIVE_API}/{args.file_id}",
        params={"fields": "name,size", "key": args.api_key},
        timeout=TIMEOUT,
    )
    meta.raise_for_status()
    meta = meta.json()
    name = meta["name"]
    size = int(meta["size"])

    part = out_dir / (name + ".part")
    pos = part.stat().st_size if part.exists() else 0

    # ダウンロード（alt=media + Range）
    url = f"{DRIVE_API}/{args.file_id}"
    params = {"alt": "media", "key": args.api_key}

    pbar = tqdm(total=size, initial=pos, unit="B", unit_scale=True, desc=name)

    with open(part, "ab") as f:
        while pos < size:
            end = min(pos + CHUNK - 1, size - 1)
            headers = {"Range": f"bytes={pos}-{end}"}

            try:
                r = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    stream=True,
                    timeout=TIMEOUT,
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
