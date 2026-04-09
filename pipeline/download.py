#!/usr/bin/env python3
"""Download PPTX files from the manifest.

Reads manifest.yaml, downloads each PPTX to pipeline/raw/<id>.pptx.
Skips files that already exist (unless --force is passed).

Usage:
    python3 download.py
    python3 download.py --force          # re-download all
    python3 download.py --ids sc-aurora sc-laertes   # download specific IDs
"""

import argparse
import os
import sys
import time

import requests
import yaml


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(SCRIPT_DIR, "manifest.yaml")
RAW_DIR = os.path.join(SCRIPT_DIR, "raw")

# SlidesCarnival direct download pattern
# Page URL: https://www.slidescarnival.com/template/<name>/<id>
# Download: https://www.slidescarnival.com/download/<id>
SC_DOWNLOAD_PREFIX = "https://www.slidescarnival.com/download/"


def load_manifest():
    with open(MANIFEST_PATH, "r") as f:
        data = yaml.safe_load(f)
    return data.get("sources", [])


def resolve_download_url(source):
    """Resolve the actual PPTX download URL from the page URL."""
    url = source.get("direct_download") or source.get("url", "")
    attribution = source.get("attribution", "")

    # SlidesCarnival: extract numeric ID from URL path
    if attribution == "SlidesCarnival" and "slidescarnival.com" in url:
        # URL pattern: https://www.slidescarnival.com/template/<name>/<numeric_id>
        # or: https://www.slidescarnival.com/<name>/<numeric_id>
        parts = url.rstrip("/").split("/")
        # Find the numeric ID (last path segment that's a number)
        for part in reversed(parts):
            if part.isdigit():
                return f"{SC_DOWNLOAD_PREFIX}{part}"
        # Fallback: try the last segment
        return f"{SC_DOWNLOAD_PREFIX}{parts[-1]}"

    # For other sources, the URL is the page URL (manual download may be needed)
    return url


def download_file(url, dest_path, timeout=60):
    """Download a file with requests, following redirects."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
    }
    resp = requests.get(url, headers=headers, timeout=timeout, stream=True, allow_redirects=True)
    resp.raise_for_status()

    # Check content type -- we want a PPTX file
    content_type = resp.headers.get("Content-Type", "")
    is_pptx = (
        "presentation" in content_type
        or "pptx" in content_type
        or "octet-stream" in content_type
        or "zip" in content_type
        or dest_path.endswith(".pptx")
    )

    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    # Verify the file is actually a PPTX (ZIP-based, starts with PK)
    with open(dest_path, "rb") as f:
        magic = f.read(2)
    if magic != b"PK":
        os.remove(dest_path)
        raise ValueError(f"Downloaded file is not a valid PPTX (got content-type: {content_type})")

    return os.path.getsize(dest_path)


def main():
    parser = argparse.ArgumentParser(description="Download PPTX files from manifest")
    parser.add_argument("--force", action="store_true", help="Re-download existing files")
    parser.add_argument("--ids", nargs="*", help="Only download specific source IDs")
    args = parser.parse_args()

    os.makedirs(RAW_DIR, exist_ok=True)
    sources = load_manifest()

    if args.ids:
        sources = [s for s in sources if s["id"] in args.ids]

    total = len(sources)
    downloaded = 0
    skipped = 0
    failed = 0

    for i, source in enumerate(sources):
        src_id = source["id"]
        dest = os.path.join(RAW_DIR, f"{src_id}.pptx")

        if os.path.exists(dest) and not args.force:
            print(f"[{i+1}/{total}] SKIP {src_id} (already exists)")
            skipped += 1
            continue

        url = resolve_download_url(source)
        print(f"[{i+1}/{total}] Downloading {src_id}...")
        print(f"  URL: {url}")

        try:
            size = download_file(url, dest)
            size_kb = size / 1024
            print(f"  OK: {size_kb:.0f} KB")
            downloaded += 1
        except Exception as e:
            print(f"  FAILED: {e}")
            failed += 1

        # Be polite: small delay between downloads
        if i < total - 1:
            time.sleep(1.0)

    print(f"\nDone: {downloaded} downloaded, {skipped} skipped, {failed} failed (out of {total})")


if __name__ == "__main__":
    main()
