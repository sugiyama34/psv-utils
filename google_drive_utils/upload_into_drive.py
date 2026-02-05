#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

import requests
from tqdm import tqdm

from google_auth import get_drive_credentials, request_with_refresh


def main():
    CREDENTIALS = "secrets/credentials.json"
    TOKEN = "secrets/token.json"

    UPLOAD_API = "https://www.googleapis.com/upload/drive/v3/files"
    CHUNK = 32 * 1024 * 1024  # 32MB chunks for resumable upload
    TIMEOUT = (10, 60)  # (connect, read)

    p = argparse.ArgumentParser(description="Upload file to Google Drive folder")
    p.add_argument("--file", required=True, help="Path to file to upload")
    p.add_argument("--folder-id", required=True, help="Google Drive folder ID")
    p.add_argument("--port", default=8100, type=int, help="Port for OAuth callback")
    args = p.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"[ERROR] File not found: {file_path}")
        sys.exit(1)

    # Authentication (shared token with download)
    try:
        creds = get_drive_credentials(
            port=args.port, credentials_path=CREDENTIALS, token_path=TOKEN
        )
    except FileNotFoundError:
        print(f"[ERROR] File not found: {CREDENTIALS}")
        sys.exit(1)

    file_size = file_path.stat().st_size
    file_name = file_path.name

    # Step 1: Initiate resumable upload
    metadata = {"name": file_name, "parents": [args.folder_id]}

    init_response = request_with_refresh(
        lambda token: requests.post(
            f"{UPLOAD_API}?uploadType=resumable&supportsAllDrives=true",
            json=metadata,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=UTF-8",
                "X-Upload-Content-Length": str(file_size),
            },
            timeout=TIMEOUT,
        ),
        creds,
        TOKEN,
    )

    if not init_response.ok:
        print(f"[ERROR] Init upload failed with status {init_response.status_code}")
        print(f"        Response: {init_response.text}")
    init_response.raise_for_status()
    upload_url = init_response.headers["Location"]

    # Step 2: Upload file in chunks with progress bar
    pbar = tqdm(total=file_size, unit="B", unit_scale=True, desc=f"Uploading {file_name}")
    uploaded = 0

    with open(file_path, "rb") as f:
        while uploaded < file_size:
            chunk_size = min(CHUNK, file_size - uploaded)
            chunk_data = f.read(chunk_size)

            headers = {
                "Content-Length": str(len(chunk_data)),
                "Content-Range": f"bytes {uploaded}-{uploaded + len(chunk_data) - 1}/{file_size}",
            }

            upload_response = requests.put(
                upload_url, data=chunk_data, headers=headers, timeout=TIMEOUT
            )

            if upload_response.status_code in [200, 201]:
                # Upload complete
                uploaded += len(chunk_data)
                pbar.update(len(chunk_data))
                result = upload_response.json()
                pbar.close()
                print(f"\n[SUCCESS] File uploaded: {result['name']}")
                print(f"          File ID: {result['id']}")
                print(f"          Link: https://drive.google.com/file/d/{result['id']}/view")
                return

            elif upload_response.status_code == 308:
                # Resume incomplete - continue uploading
                uploaded += len(chunk_data)
                pbar.update(len(chunk_data))

            else:
                pbar.close()
                print(f"\n[ERROR] Upload failed with status {upload_response.status_code}")
                print(f"        Response: {upload_response.text}")
                sys.exit(1)

    pbar.close()


if __name__ == "__main__":
    main()
