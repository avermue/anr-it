"""Inspect every CSV in data/raw/: encoding, separator, columns, sample, row count."""
import csv
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
csv.field_size_limit(10**9)  # accept long objective fields

RAW_DIR = Path(__file__).resolve().parent.parent / 'data' / 'raw'

FILES = [
    'anr01_dgds_2005_projets.csv',
    'anr01_dgds_2005_partenaires.csv',
    'anr01_dgds_2010_projets.csv',
    'anr01_dgds_2010_partenaires.csv',
    'anr02_dgpie_projets.csv',
    'anr02_dgpie_partenaires.csv',
    'participants_siren.csv',
]


def sniff(path: Path):
    """Return (encoding, sep, header_line)."""
    with open(path, 'rb') as f:
        head_bytes = f.read(16384)
    enc = None
    head_text = ''
    for candidate in ('utf-8-sig', 'utf-8', 'cp1252', 'latin1'):
        try:
            head_text = head_bytes.decode(candidate)
            enc = candidate
            break
        except UnicodeDecodeError:
            continue
    first_line = head_text.splitlines()[0] if head_text else ''
    counts = {sep: first_line.count(sep) for sep in [';', ',', '\t', '|']}
    sep = max(counts, key=counts.get) if any(counts.values()) else ','
    return enc, sep


def count_rows(path: Path, enc: str):
    n = 0
    with open(path, 'r', encoding=enc, errors='replace', newline='') as f:
        for _ in f:
            n += 1
    return max(n - 1, 0)


def inspect(path: Path):
    enc, sep = sniff(path)
    print('=' * 100)
    print(f"FILE   : {path.name}  ({path.stat().st_size / 1e6:.1f} MB)")
    print(f"  enc  : {enc}")
    print(f"  sep  : {repr(sep)}")
    with open(path, 'r', encoding=enc, errors='replace', newline='') as f:
        reader = csv.reader(f, delimiter=sep)
        try:
            header = next(reader)
        except StopIteration:
            print('  (empty)')
            return
        print(f"  cols : {len(header)}")
        for i, col in enumerate(header):
            print(f"     {i:3d}  {col}")
        print("  sample (first 2 rows):")
        for i, row in enumerate(reader):
            if i >= 2:
                break
            print(f"    --- row {i} ---")
            for k, v in zip(header, row):
                if v == '':
                    continue
                v_s = (v[:90] + '…') if len(v) > 90 else v
                print(f"      {k}: {v_s}")
    rows = count_rows(path, enc)
    print(f"  rows : {rows:,}")
    print()


for name in FILES:
    p = RAW_DIR / name
    if p.exists():
        inspect(p)
    else:
        print(f"!! Missing: {name}")
