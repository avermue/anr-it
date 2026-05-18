#!/usr/bin/env python3
"""
Build a local INRAE structure lookup from https://annuaire.inrae.fr.

The script crawls public department pages, follows their laboratory links, and
writes data/inrae_structures.json. build_data.py then uses that cache offline to
enrich ANR partners by RNSR code.
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from html import unescape
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT = BASE_DIR / "data" / "inrae_structures.json"
PROJECTS_JSON = BASE_DIR / "data" / "inrae_anr_projects.json"
BASE_URL = "https://annuaire.inrae.fr"

UA = "anr-it-data-build/1.0 (+https://github.com/)"
INRAE_FAMILY = {"INRAE", "INRA", "IRSTEA", "CEMAGREF"}


def log(message):
    print(message, flush=True)


def fetch(path, retries=3, method="GET", body=None, session=None):
    url = path if path.startswith("http") else f"{BASE_URL}{path}"
    headers = {"User-Agent": UA}
    if body is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(session)) if session is not None else None
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            open_url = opener.open if opener else urllib.request.urlopen
            with open_url(request, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(0.8 * attempt)
    raise RuntimeError(f"Could not fetch {url}: {last_error}")


def clean_html(value):
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def parse_links(html):
    links = []
    pattern = re.compile(r'<a\b[^>]*href="/structure/([^"]+)"[^>]*>(.*?)</a>', re.I | re.S)
    for match in pattern.finditer(html):
        links.append({
            "id": match.group(1),
            "label": clean_html(match.group(2)),
        })
    return links


def parse_department_ids(html):
    ids = []
    seen = set()
    pattern = re.compile(
        r'<a\b[^>]*class="card__title-link"[^>]*href="/structure/([^"]+)"',
        re.I | re.S,
    )
    for match in pattern.finditer(html):
        structure_id = match.group(1)
        if structure_id in seen:
            continue
        seen.add(structure_id)
        ids.append(structure_id)
    return ids


def parse_laboratory_ids(html):
    start = html.find('id="structures"')
    if start < 0:
        return []
    end = html.find('id="infrastructures"', start)
    scope = html[start:end] if end > start else html[start:]
    ids = []
    seen = set()
    for link in parse_links(scope):
        if link["id"] in seen:
            continue
        seen.add(link["id"])
        ids.append(link["id"])
    return ids


def first_section(html, needle):
    sections = re.findall(
        r'<section class="details__subsection">(.*?)</section>',
        html,
        flags=re.I | re.S,
    )
    for section in sections:
        h2 = re.search(r"<h2\b[^>]*>(.*?)</h2>", section, flags=re.I | re.S)
        title = clean_html(h2.group(1)) if h2 else ""
        if needle.lower() in title.lower():
            return section
    return ""


def section_text(html, needle):
    section = first_section(html, needle)
    if not section:
        return ""
    section = re.sub(r"<h2\b.*?</h2>", " ", section, flags=re.I | re.S)
    return clean_html(section)


def section_links(html, needle):
    return parse_links(first_section(html, needle))


def parse_title_parts(title):
    title = clean_html(title)
    match = re.match(r"^([A-Z]{1,5})\s+([0-9A-Z]{2,5})(?:\s+([^|]+?))?\s*(?:\|\s*(.+))?$", title)
    if not match:
        return {
            "unitType": "",
            "unitCode": "",
            "unitAcronym": "",
            "unitName": title,
        }

    unit_type, unit_code, acronym, unit_name = match.groups()
    acronym = clean_html(acronym or "")
    unit_name = clean_html(unit_name or "")
    return {
        "unitType": unit_type,
        "unitCode": unit_code,
        "unitAcronym": acronym,
        "unitName": unit_name or title,
    }


def parse_structure_page(structure_id, html):
    title_match = re.search(r'<h1 class="hero__title">\s*(.*?)</h1>', html, re.I | re.S)
    label = clean_html(title_match.group(1)) if title_match else ""
    title_parts = parse_title_parts(label)

    rnsr = section_text(html, "RNSR")
    if not rnsr:
        return None

    centre_links = section_links(html, "Centre")
    pilot_links = section_links(html, "Département ou direction pilote")
    copilot_links = section_links(html, "Départements co-pilotes")

    return {
        "id": structure_id,
        "url": f"{BASE_URL}/structure/{structure_id}",
        "label": label,
        **title_parts,
        "rnsr": rnsr,
        "centre": centre_links[0]["label"] if centre_links else "",
        "centreCode": centre_links[0]["id"] if centre_links else "",
        "departmentPilot": pilot_links[0]["label"] if pilot_links else "",
        "departmentPilotCode": pilot_links[0]["id"] if pilot_links else "",
        "departmentCopilots": [
            {"code": link["id"], "name": link["label"]}
            for link in copilot_links
        ],
    }


def load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_existing_structures(path):
    if not path.exists():
        return [], {}, set(), set()

    payload = load_json(path)
    structures = payload.get("structures", [])
    by_id = {
        str(structure.get("id")): structure
        for structure in structures
        if structure.get("id")
    }
    rnsr_seen = {
        structure.get("rnsr")
        for structure in structures
        if structure.get("rnsr")
    }
    unresolved_rnsr = {
        rnsr
        for rnsr in payload.get("unresolvedRnsr", [])
        if rnsr
    }
    return structures, by_id, rnsr_seen, unresolved_rnsr


def collect_wanted_rnsr(path):
    if not path or not path.exists():
        return set()

    payload = load_json(path)
    wanted = set()
    for project in payload.get("projects", []):
        for partner in project.get("partners", []):
            if partner.get("entity") not in INRAE_FAMILY:
                continue
            rnsr = partner.get("rnsr")
            if rnsr:
                wanted.add(rnsr)
    return wanted


def discover_laboratory_ids(sleep):
    log("Fetching INRAE departments...")
    departments_html = fetch("/departements")
    department_ids = parse_department_ids(departments_html)
    log(f"  Departments/directions: {len(department_ids)}")

    lab_ids = []
    seen_labs = set()
    for index, department_id in enumerate(department_ids, start=1):
        html = fetch(f"/structure/{department_id}")
        for lab_id in parse_laboratory_ids(html):
            if lab_id not in seen_labs:
                seen_labs.add(lab_id)
                lab_ids.append(lab_id)
        log(f"  [{index:02d}/{len(department_ids):02d}] {department_id}: {len(seen_labs)} laboratories")
        time.sleep(sleep)
    return lab_ids


def merge_structures(existing, new):
    merged = {}
    for structure in existing:
        key = structure.get("rnsr") or structure.get("id")
        if key:
            merged[key] = structure
    for structure in new:
        key = structure.get("rnsr") or structure.get("id")
        if key:
            merged[key] = structure
    return sorted(merged.values(), key=lambda item: (item.get("rnsr") or "", item.get("id") or ""))


def write_output(path, structures, unresolved_rnsr=None):
    output = {
        "generatedAt": date.today().isoformat(),
        "source": f"{BASE_URL}/structures",
        "unresolvedRnsr": sorted(unresolved_rnsr or []),
        "structures": structures,
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(OUTPUT))
    parser.add_argument("--sleep", type=float, default=0.08, help="Delay between HTTP requests")
    parser.add_argument("--limit", type=int, default=0, help="Limit laboratory pages for parser tests")
    parser.add_argument("--incremental", action="store_true", help="Keep the existing cache and fetch only uncached lab pages")
    parser.add_argument(
        "--wanted-rnsr-from",
        default=str(PROJECTS_JSON),
        help="Project JSON used to identify relevant RNSR codes in incremental mode",
    )
    args = parser.parse_args()
    output_path = Path(args.output)

    existing_structures, existing_by_id, existing_rnsr, existing_unresolved = load_existing_structures(output_path)
    wanted_rnsr = collect_wanted_rnsr(Path(args.wanted_rnsr_from)) if args.wanted_rnsr_from else set()

    if args.incremental and existing_structures:
        missing_wanted = sorted(wanted_rnsr - existing_rnsr - existing_unresolved) if wanted_rnsr else []
        log(f"Existing structures  : {len(existing_structures)}")
        log(f"Wanted RNSR          : {len(wanted_rnsr)}")
        log(f"Known unresolved RNSR: {len(existing_unresolved)}")
        log(f"Missing wanted RNSR  : {len(missing_wanted)}")
        if wanted_rnsr and not missing_wanted:
            log("All wanted RNSR are already cached; keeping the existing structure cache.")
            return
    elif args.incremental:
        log("No existing structure cache; running a full crawl.")

    lab_ids = discover_laboratory_ids(args.sleep)

    if args.limit:
        lab_ids = lab_ids[:args.limit]

    structures = []
    rnsr_seen = set()
    target_rnsr = set(wanted_rnsr - existing_rnsr - existing_unresolved) if args.incremental and existing_structures and wanted_rnsr else set()
    detail_ids = [lab_id for lab_id in lab_ids if not args.incremental or lab_id not in existing_by_id]

    log("Fetching laboratory details...")
    for index, lab_id in enumerate(detail_ids, start=1):
        html = fetch(f"/structure/{lab_id}")
        structure = parse_structure_page(lab_id, html)
        if structure:
            structures.append(structure)
            if structure["rnsr"] in rnsr_seen:
                log(f"  WARNING duplicate RNSR {structure['rnsr']} at /structure/{lab_id}")
            rnsr_seen.add(structure["rnsr"])
            target_rnsr.discard(structure["rnsr"])
        if index % 50 == 0 or index == len(detail_ids):
            log(f"  [{index:03d}/{len(detail_ids):03d}] parsed, {len(structures)} with RNSR")
        if args.incremental and wanted_rnsr and not target_rnsr:
            log("  All missing wanted RNSR found; stopping incremental detail crawl.")
            break
        time.sleep(args.sleep)

    if args.incremental and existing_structures:
        next_unresolved = existing_unresolved | target_rnsr
        if not structures and next_unresolved == existing_unresolved:
            log("No new structure with RNSR found; keeping the existing structure cache.")
            return
        structures = merge_structures(existing_structures, structures)
        cached_rnsr = {
            structure.get("rnsr")
            for structure in structures
            if structure.get("rnsr")
        }
        unresolved_rnsr = next_unresolved - cached_rnsr
    else:
        structures = sorted(structures, key=lambda item: (item.get("rnsr") or "", item.get("id") or ""))
        unresolved_rnsr = set()

    write_output(output_path, structures, unresolved_rnsr)

    log("")
    log(f"OK: {output_path} ({len(structures)} structures with RNSR)")


if __name__ == "__main__":
    main()
