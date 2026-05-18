"""One-time download script: streams Yelp, Amazon Books, Goodreads and creates small samples.

Usage:
    pip install pandas pyarrow    # dev-only, not needed at runtime
    python tools/download_datasets.py

Output: data/yelp/*.json, data/amazon/*.json, data/goodreads/*.json
All samples combined ≈ 50-70 MB. The large Yelp ZIP (4.35 GB) is deleted after sampling.
"""

import gzip
import io
import json
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

import httpx

BASE = Path(__file__).resolve().parent.parent / "data"

YELP_ZIP_URL = "https://business.yelp.com/external-assets/files/Yelp-JSON.zip"
YELP_FILES = {
    "business": ("yelp_academic_dataset_business.json", 10_000),
    "review": ("yelp_academic_dataset_review.json", 20_000),
    "user": ("yelp_academic_dataset_user.json", 2_000),
}

AMAZON_HF_REPO = "LoganKells/amazon_product_reviews_video_games"
AMAZON_HF_FILE = "data.csv"

GOODREADS_HF_REPO = "pszemraj/goodreads-bookgenres"
GOODREADS_HF_FILE = "data/train-00000-of-00001-1ddc9bde2cb8caf1.parquet"



TIMEOUT = 300.0


def _log(msg: str) -> None:
    print(f"[download_datasets] {msg}")


# ── Yelp ──────────────────────────────────────────────────────────────


def _stream_lines_from_zip_member(
    zip_path: str, member_name: str, max_lines: int,
) -> list[str]:
    """Read up to *max_lines* JSON lines from a file inside the nested ZIP→TAR."""
    import tarfile

    lines: list[str] = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        # The Yelp dataset is Yelp JSON/yelp_dataset.tar inside the ZIP
        tar_member = "Yelp JSON/yelp_dataset.tar"
        if tar_member not in zf.namelist():
            # Try alternate paths
            candidates = [n for n in zf.namelist() if n.endswith(".tar")]
            tar_member = candidates[0] if candidates else None

        if tar_member is None:
            raise FileNotFoundError(
                f"Could not find .tar inside ZIP. Contents: {zf.namelist()[:10]}"
            )

        with zf.open(tar_member, "r") as tar_bytes:
            with tarfile.open(fileobj=tar_bytes, mode="r") as tf:
                # Find the requested member_name inside the tar
                tinfo = None
                for m in tf.getmembers():
                    if m.name.endswith(member_name):
                        tinfo = m
                        break
                if tinfo is None:
                    raise KeyError(
                        f"'{member_name}' not found in TAR. Members: {[m.name for m in tf.getmembers()[:10]]}"
                    )
                f = tf.extractfile(tinfo)
                if f is None:
                    raise ValueError(f"Cannot extract {member_name} from TAR")
                for i, raw in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(raw.decode("utf-8").rstrip("\n"))
    return lines


def download_yelp() -> None:
    yelp_dir = BASE / "yelp"
    yelp_dir.mkdir(parents=True, exist_ok=True)

    zip_path = os.path.join(tempfile.gettempdir(), "yelp_dataset.zip")

    _headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.yelp.com/dataset",
    }

    if os.path.isfile(zip_path):
        actual = os.path.getsize(zip_path)
        # HEAD to check expected size
        try:
            with httpx.Client(headers=_headers, timeout=30, follow_redirects=True) as c:
                head = c.head(YELP_ZIP_URL)
                expected = int(head.headers.get("content-length", 0))
        except Exception:
            expected = 0
        if actual >= expected and expected > 0:
            _log(f"Yelp ZIP already downloaded ({actual // 1024 // 1024} MB).")
        else:
            _log(f"Partial ZIP found ({actual // 1024 // 1024} MB vs {expected // 1024 // 1024} MB). Re-downloading...")
            os.remove(zip_path)
            _download_yelp_zip(zip_path, _headers)
    else:
        _download_yelp_zip(zip_path, _headers)

    # Extract + sample
    _log("Extracting samples from Yelp ZIP...")
    for key, (member_name, max_lines) in YELP_FILES.items():
        lines = _stream_lines_from_zip_member(zip_path, member_name, max_lines)
        out_path = yelp_dir / f"{key}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")
        _log(f"  Saved {len(lines)} lines to {out_path.name}")

    # Delete ZIP
    os.remove(zip_path)
    _log("Deleted Yelp ZIP.")


def _download_yelp_zip(zip_path: str, headers: dict) -> None:
    _log("Downloading Yelp dataset (4.35 GB ZIP)...")
    with httpx.Client(timeout=TIMEOUT, follow_redirects=True, headers=headers) as client:
        with client.stream("GET", YELP_ZIP_URL) as resp:
            resp.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in resp.iter_bytes(chunk_size=8 * 1024 * 1024):
                    f.write(chunk)


# ── Amazon Reviews ────────────────────────────────────────────────────


def download_amazon() -> None:
    amazon_dir = BASE / "amazon"
    amazon_dir.mkdir(parents=True, exist_ok=True)
    out_path = amazon_dir / "reviews.json"
    max_rows = 15_000

    _log("Loading Amazon Reviews (video games) from HuggingFace...")
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        _log("huggingface_hub not installed. Run: pip install huggingface_hub")
        return

    csv_path = hf_hub_download(
        repo_id=AMAZON_HF_REPO,
        filename=AMAZON_HF_FILE,
        repo_type="dataset",
    )

    import csv
    count = 0
    with open(csv_path, "r", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        with open(out_path, "w", encoding="utf-8") as f_out:
            for row in reader:
                clean = {
                    "source": "amazon",
                    "customer_id": row.get("reviewerID", ""),
                    "product_id": row.get("asin", ""),
                    "product_title": row.get("summary", ""),
                    "product_category": "video_games",
                    "star_rating": row.get("overall"),
                    "review_body": row.get("reviewText", ""),
                    "review_headline": row.get("summary", ""),
                    "helpful_votes": row.get("helpful", "0"),
                    "verified_purchase": row.get("verified", "0"),
                }
                f_out.write(json.dumps(clean, ensure_ascii=False) + "\n")
                count += 1
                if count >= max_rows:
                    break

    _log(f"Saved {count} Amazon reviews.")


# ── Goodreads ─────────────────────────────────────────────────────────


def download_goodreads() -> None:
    goodreads_dir = BASE / "goodreads"
    goodreads_dir.mkdir(parents=True, exist_ok=True)
    out_path = goodreads_dir / "books.json"
    max_rows = 15_000

    _log("Downloading Goodreads parquet...")
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        _log("huggingface_hub not installed.")
        return

    parquet_path = hf_hub_download(
        repo_id=GOODREADS_HF_REPO,
        filename=GOODREADS_HF_FILE,
        repo_type="dataset",
    )

    try:
        import pandas as pd
    except ImportError:
        _log("pandas not installed.")
        return

    df = pd.read_parquet(parquet_path, engine="pyarrow")
    df = df.head(max_rows)

    records = df.to_dict(orient="records")
    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            clean: dict = {}
            for k, v in r.items():
                if isinstance(v, (list, dict)):
                    clean[k] = v
                elif v is None:
                    clean[k] = None
                elif isinstance(v, float):
                    clean[k] = round(v, 4)
                else:
                    try:
                        if pd.isna(v):
                            clean[k] = None
                        else:
                            clean[k] = str(v)
                    except (ValueError, TypeError):
                        clean[k] = str(v)
            f.write(json.dumps(clean, ensure_ascii=False) + "\n")

    _log(f"Saved {len(records)} Goodreads books.")


# ── Main ──────────────────────────────────────────────────────────────


def check_disk_space_needed() -> None:
    """Rough check: Yelp ZIP is ~4.4 GB, plus ~50 MB for outputs."""
    import shutil
    free = shutil.disk_usage(BASE).free
    needed = 5_000_000_000  # 5 GB
    if free < needed:
        _log(
            f"WARNING: Only {free // 1_000_000_000} GB free, need ~{needed // 1_000_000_000} GB. "
            "You can skip Yelp with --skip-yelp or free up space."
        )


def main(skip_yelp: bool = False) -> None:
    check_disk_space_needed()

    if not skip_yelp:
        download_yelp()
    else:
        _log("Skipping Yelp download.")

    download_amazon()
    download_goodreads()

    # Show final sizes
    _log("\nFinal dataset sizes:")
    for path in sorted(BASE.rglob("*")):
        if path.is_file() and not path.name.startswith("."):
            size_mb = path.stat().st_size / 1_024 / 1_024
            _log(f"  {path.relative_to(BASE.parent)}: {size_mb:.1f} MB")
    total = sum(
        p.stat().st_size for p in BASE.rglob("*") if p.is_file()
    )
    _log(f"Total: {total / 1_024 / 1_024:.1f} MB")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-yelp", action="store_true", help="Skip Yelp download (4.35 GB)")
    args = parser.parse_args()
    main(skip_yelp=args.skip_yelp)
