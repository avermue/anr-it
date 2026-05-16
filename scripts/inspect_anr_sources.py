"""List resources exposed by the 3 ANR datasets on data.gouv.fr.

Run before any download — gives us titles, formats, sizes, stable URLs.
No file is downloaded here, only the dataset metadata is fetched via the API.
"""
import json
import sys
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

SLUGS = [
    'anr-01-projets-anr-dos-et-dgds-detail-des-projets-et-des-partenaires',
    'anr-02-projets-anr-dgpie-detail-des-projets-et-des-partenaires',
    'appels-a-projets-anr-projets-retenus-et-participants-identifies',
]


def fmt_size(n):
    if not n:
        return "       ? MB"
    return f"{n / 1e6:7.2f} MB"


for slug in SLUGS:
    api_url = f'https://www.data.gouv.fr/api/1/datasets/{slug}/'
    try:
        with urllib.request.urlopen(api_url, timeout=30) as r:
            d = json.load(r)
    except Exception as e:
        print(f'!! {slug}: {e}')
        continue
    print('=' * 100)
    print(f"DATASET   : {d.get('title')}")
    print(f"  slug    : {d.get('slug')}")
    org = (d.get('organization') or {}).get('name', '?')
    print(f"  org     : {org}")
    upd = d.get('last_update') or d.get('last_modified') or '?'
    print(f"  updated : {upd[:19] if isinstance(upd, str) else upd}")
    print(f"  page    : {d.get('page')}")
    resources = d.get('resources', [])
    print(f"  resources ({len(resources)}):")
    for r in resources:
        fmt = (r.get('format') or '?').lower()
        title = (r.get('title') or '-')[:80]
        print(f"    [{fmt:<6}] {fmt_size(r.get('filesize'))}  {title}")
        print(f"             url: {r.get('url')}")
    print()
