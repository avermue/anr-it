"""Download all ANR data sources into data/raw/.

Idempotent: skips files that already exist with non-zero size.
Runs 4 concurrent downloads for speed.
"""
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

RAW_DIR = Path(__file__).resolve().parent.parent / 'data' / 'raw'
RAW_DIR.mkdir(parents=True, exist_ok=True)

SOURCES = {
    # ANR_01 — DGDS / Plan d'action (DOS pre-2010, DGDS since 2010)
    'anr01_dgds_2010_projets.csv':
        'https://static.data.gouv.fr/resources/anr-01-projets-anr-dos-et-dgds-detail-des-projets-et-des-partenaires/20260501-222157/anr-dgds-depuis-2010-projets-finances-20260502-projets.csv',
    'anr01_dgds_2010_partenaires.csv':
        'https://static.data.gouv.fr/resources/anr-01-projets-anr-dos-et-dgds-detail-des-projets-et-des-partenaires/20260501-222206/anr-dgds-depuis-2010-projets-finances-20260502-partenaires.csv',
    'anr01_dgds_2005_projets.csv':
        'https://static.data.gouv.fr/resources/anr-01-projets-anr-dos-et-dgds-detail-des-projets-et-des-partenaires/20251105-125442/anr-dgds-2005-2009-projets-finances-20251105-projets.csv',
    'anr01_dgds_2005_partenaires.csv':
        'https://static.data.gouv.fr/resources/anr-01-projets-anr-dos-et-dgds-detail-des-projets-et-des-partenaires/20251105-125445/anr-dgds-2005-2009-projets-finances-20251105-partenaires.csv',
    'anr01_notice.pdf':
        'https://static.data.gouv.fr/resources/anr-01-projets-anr-dos-detail-des-projets-et-des-partenaires/20251105-112810/2025-11-02-notice-anr-dgds-projets-finances.pdf',
    # ANR_02 — DGPIE / PIA / France 2030
    'anr02_dgpie_projets.csv':
        'https://static.data.gouv.fr/resources/anr-02-projets-anr-dgpie-detail-des-projets-et-des-partenaires/20260501-225043/anr-dgpie-depuis-2010-projets-finances-20260502-projets.csv',
    'anr02_dgpie_partenaires.csv':
        'https://static.data.gouv.fr/resources/anr-02-projets-anr-dgpie-detail-des-projets-et-des-partenaires/20260501-225045/anr-dgpie-depuis-2010-projets-finances-20260502-partenaires.csv',
    'anr02_notice.pdf':
        'https://static.data.gouv.fr/resources/projets-anr-dgpie-detail-des-projets-et-des-partenaires/20210616-181904/2021-04-22-anr-dgpie-projets-finances.pdf',
    # Participants identifiés (Opendatasoft / Ministère ESR)
    'participants_siren.csv':
        'http://data.enseignementsup-recherche.gouv.fr/explore/dataset/fr-esr-aap-anr-projets-retenus-participants-identifies/download/?format=csv&timezone=Europe/Berlin&use_labels_for_header=true',
}


def download_one(dst_name, url):
    dst = RAW_DIR / dst_name
    if dst.exists() and dst.stat().st_size > 0:
        return (dst_name, dst.stat().st_size, 'cached')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'anr-it-portal/0.1'})
        with urllib.request.urlopen(req, timeout=120) as r, open(dst, 'wb') as f:
            while True:
                chunk = r.read(1 << 16)
                if not chunk:
                    break
                f.write(chunk)
        return (dst_name, dst.stat().st_size, 'downloaded')
    except Exception as e:
        if dst.exists():
            dst.unlink()
        return (dst_name, 0, f'ERROR: {e}')


def main():
    print(f"Target dir: {RAW_DIR}")
    print(f"Files     : {len(SOURCES)}")
    print('-' * 80)
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(download_one, name, url): name for name, url in SOURCES.items()}
        for fut in as_completed(futures):
            name, size, status = fut.result()
            size_s = f"{size / 1e6:8.2f} MB" if size else "        -"
            print(f"  [{status:<10}] {size_s}  {name}")
    print('-' * 80)
    total = sum(f.stat().st_size for f in RAW_DIR.iterdir() if f.is_file())
    print(f"Total in data/raw/: {total / 1e6:.1f} MB")


if __name__ == '__main__':
    main()
