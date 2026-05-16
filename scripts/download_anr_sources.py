#!/usr/bin/env python3
"""Download ANR data sources into data/raw/.

The ANR CSV resources are resolved from the data.gouv.fr dataset API so the
scheduled GitHub Action can pick up future source updates without editing this
script. Pinned URLs are kept as a fallback and for reproducible local runs.
"""

import argparse
import json
import re
import sys
import unicodedata
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
METADATA_FILE = RAW_DIR / "source_metadata.json"

DATASETS = {
    "dgds": {
        "slug": "anr-01-projets-anr-dos-et-dgds-detail-des-projets-et-des-partenaires",
        "label": "ANR_01 DGDS",
    },
    "dgpie": {
        "slug": "anr-02-projets-anr-dgpie-detail-des-projets-et-des-partenaires",
        "label": "ANR_02 DGPIE",
    },
}

DYNAMIC_SPECS = {
    "anr01_dgds_2010_projets.csv": {
        "dataset": "dgds",
        "include": ["dgds", "depuis", "2010", "projets"],
        "exclude": ["partenaires"],
    },
    "anr01_dgds_2010_partenaires.csv": {
        "dataset": "dgds",
        "include": ["dgds", "depuis", "2010", "partenaires"],
        "exclude": [],
    },
    "anr01_dgds_2005_projets.csv": {
        "dataset": "dgds",
        "include": ["dgds", "2005", "2009", "projets"],
        "exclude": ["partenaires"],
    },
    "anr01_dgds_2005_partenaires.csv": {
        "dataset": "dgds",
        "include": ["dgds", "2005", "2009", "partenaires"],
        "exclude": [],
    },
    "anr02_dgpie_projets.csv": {
        "dataset": "dgpie",
        "include": ["dgpie", "projets"],
        "exclude": ["partenaires"],
    },
    "anr02_dgpie_partenaires.csv": {
        "dataset": "dgpie",
        "include": ["dgpie", "partenaires"],
        "exclude": [],
    },
}

PINNED_SOURCES = {
    "anr01_dgds_2010_projets.csv": {
        "dataset": "dgds",
        "url": "https://static.data.gouv.fr/resources/anr-01-projets-anr-dos-et-dgds-detail-des-projets-et-des-partenaires/20260501-222157/anr-dgds-depuis-2010-projets-finances-20260502-projets.csv",
    },
    "anr01_dgds_2010_partenaires.csv": {
        "dataset": "dgds",
        "url": "https://static.data.gouv.fr/resources/anr-01-projets-anr-dos-et-dgds-detail-des-projets-et-des-partenaires/20260501-222206/anr-dgds-depuis-2010-projets-finances-20260502-partenaires.csv",
    },
    "anr01_dgds_2005_projets.csv": {
        "dataset": "dgds",
        "url": "https://static.data.gouv.fr/resources/anr-01-projets-anr-dos-et-dgds-detail-des-projets-et-des-partenaires/20251105-125442/anr-dgds-2005-2009-projets-finances-20251105-projets.csv",
    },
    "anr01_dgds_2005_partenaires.csv": {
        "dataset": "dgds",
        "url": "https://static.data.gouv.fr/resources/anr-01-projets-anr-dos-et-dgds-detail-des-projets-et-des-partenaires/20251105-125445/anr-dgds-2005-2009-projets-finances-20251105-partenaires.csv",
    },
    "anr01_notice.pdf": {
        "dataset": "dgds",
        "url": "https://static.data.gouv.fr/resources/anr-01-projets-anr-dos-detail-des-projets-et-des-partenaires/20251105-112810/2025-11-02-notice-anr-dgds-projets-finances.pdf",
    },
    "anr02_dgpie_projets.csv": {
        "dataset": "dgpie",
        "url": "https://static.data.gouv.fr/resources/anr-02-projets-anr-dgpie-detail-des-projets-et-des-partenaires/20260501-225043/anr-dgpie-depuis-2010-projets-finances-20260502-projets.csv",
    },
    "anr02_dgpie_partenaires.csv": {
        "dataset": "dgpie",
        "url": "https://static.data.gouv.fr/resources/anr-02-projets-anr-dgpie-detail-des-projets-et-des-partenaires/20260501-225045/anr-dgpie-depuis-2010-projets-finances-20260502-partenaires.csv",
    },
    "anr02_notice.pdf": {
        "dataset": "dgpie",
        "url": "https://static.data.gouv.fr/resources/projets-anr-dgpie-detail-des-projets-et-des-partenaires/20210616-181904/2021-04-22-anr-dgpie-projets-finances.pdf",
    },
    "participants_siren.csv": {
        "dataset": "participants",
        "url": "http://data.enseignementsup-recherche.gouv.fr/explore/dataset/fr-esr-aap-anr-projets-retenus-participants-identifies/download/?format=csv&timezone=Europe/Berlin&use_labels_for_header=true",
    },
}


def normalize(value):
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-zA-Z0-9]+", " ", text).lower()
    return re.sub(r"\s+", " ", text).strip()


def fetch_dataset(dataset_key):
    slug = DATASETS[dataset_key]["slug"]
    api_url = f"https://www.data.gouv.fr/api/1/datasets/{slug}/"
    req = urllib.request.Request(api_url, headers={"User-Agent": "anr-it-portal/0.1"})
    with urllib.request.urlopen(req, timeout=60) as response:
        return json.load(response)


def resource_text(resource):
    url_filename = (resource.get("url") or "").rstrip("/").split("/")[-1]
    return normalize(" ".join([
        resource.get("title") or "",
        url_filename,
        resource.get("latest") or "",
    ]))


def is_csv_resource(resource):
    fmt = normalize(resource.get("format") or "")
    url = (resource.get("url") or "").lower()
    title = normalize(resource.get("title") or "")
    return fmt == "csv" or url.endswith(".csv") or " csv " in f" {title} "


def resource_sort_key(resource):
    text = " ".join([
        resource.get("title") or "",
        resource.get("url") or "",
        resource.get("last_modified") or "",
        resource.get("published") or "",
    ])
    dates = re.findall(r"20\d{6}", text)
    return (
        max(dates) if dates else "",
        resource.get("last_modified") or "",
        resource.get("published") or "",
        resource.get("title") or "",
    )


def matches(resource, spec):
    if not is_csv_resource(resource):
        return False
    text = resource_text(resource)
    includes = [normalize(part) for part in spec["include"]]
    excludes = [normalize(part) for part in spec["exclude"]]
    return all(part in text for part in includes) and not any(part in text for part in excludes)


def resolve_sources(use_pinned=False):
    sources = {name: dict(source) for name, source in PINNED_SOURCES.items()}
    metadata = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "pinned" if use_pinned else "api",
        "datasets": {},
        "sources": {},
    }

    if use_pinned:
        metadata["sources"] = sources
        return sources, metadata

    datasets = {}
    for dataset_key in DATASETS:
        try:
            dataset = fetch_dataset(dataset_key)
        except Exception as exc:
            print(f"WARNING: API lookup failed for {dataset_key}, using pinned URLs: {exc}")
            continue
        datasets[dataset_key] = dataset
        metadata["datasets"][dataset_key] = {
            "slug": dataset.get("slug") or DATASETS[dataset_key]["slug"],
            "title": dataset.get("title"),
            "last_update": dataset.get("last_update") or dataset.get("last_modified"),
            "page": dataset.get("page"),
        }

    for dst_name, spec in DYNAMIC_SPECS.items():
        dataset = datasets.get(spec["dataset"])
        if not dataset:
            continue

        candidates = [r for r in dataset.get("resources", []) if matches(r, spec)]
        if not candidates:
            print(f"WARNING: no API resource match for {dst_name}, using pinned URL")
            continue

        resource = sorted(candidates, key=resource_sort_key)[-1]
        sources[dst_name] = {
            "dataset": spec["dataset"],
            "url": resource["url"],
            "resource_id": resource.get("id"),
            "resource_title": resource.get("title"),
            "resource_last_modified": resource.get("last_modified"),
            "resource_published": resource.get("published"),
            "resource_filesize": resource.get("filesize"),
        }

    metadata["sources"] = sources
    return sources, metadata


def download_one(dst_name, source, force=False):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    dst = RAW_DIR / dst_name
    if dst.exists() and dst.stat().st_size > 0 and not force:
        return dst_name, dst.stat().st_size, "cached"

    tmp = dst.with_name(f"{dst.name}.tmp")
    try:
        req = urllib.request.Request(source["url"], headers={"User-Agent": "anr-it-portal/0.1"})
        with urllib.request.urlopen(req, timeout=180) as response, tmp.open("wb") as handle:
            while True:
                chunk = response.read(1 << 16)
                if not chunk:
                    break
                handle.write(chunk)
        tmp.replace(dst)
        return dst_name, dst.stat().st_size, "downloaded"
    except Exception as exc:
        if tmp.exists():
            tmp.unlink()
        return dst_name, 0, f"ERROR: {exc}"


def write_metadata(metadata):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with METADATA_FILE.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Redownload files even when cached.")
    parser.add_argument("--pinned", action="store_true", help="Use pinned source URLs instead of the data.gouv.fr API.")
    parser.add_argument("--dry-run", action="store_true", help="Resolve and print sources without downloading.")
    parser.add_argument("--workers", type=int, default=4, help="Concurrent downloads.")
    args = parser.parse_args()

    sources, metadata = resolve_sources(use_pinned=args.pinned)

    print(f"Target dir: {RAW_DIR}")
    print(f"Files     : {len(sources)}")
    print("-" * 100)
    for name, source in sorted(sources.items()):
        origin = source.get("resource_title") or source["url"]
        print(f"  {name:<36} {origin}")

    if args.dry_run:
        return

    print("-" * 100)
    errors = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(download_one, name, source, args.force): name
            for name, source in sources.items()
        }
        for future in as_completed(futures):
            name, size, status = future.result()
            if status.startswith("ERROR"):
                errors.append((name, status))
            size_s = f"{size / 1e6:8.2f} MB" if size else "        -"
            print(f"  [{status:<10}] {size_s}  {name}")

    if errors:
        print("-" * 100)
        for name, status in errors:
            print(f"{name}: {status}", file=sys.stderr)
        raise SystemExit(1)

    write_metadata(metadata)
    total = sum(path.stat().st_size for path in RAW_DIR.iterdir() if path.is_file())
    print("-" * 100)
    print(f"Metadata: {METADATA_FILE}")
    print(f"Total in data/raw/: {total / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
