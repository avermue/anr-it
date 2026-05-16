"""Profile ANR data values: instruments, INRAE/IT detection, SIREN coverage, RNSR availability, countries."""
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
csv.field_size_limit(10**9)

RAW = Path(__file__).resolve().parent.parent / 'data' / 'raw'
ENC, SEP = 'utf-8-sig', ';'


def rows(name):
    with open(RAW / name, 'r', encoding=ENC, newline='') as f:
        yield from csv.DictReader(f, delimiter=SEP)


def detect(name):
    """Classify partner organisation name → tag (or None)."""
    n = (name or '').upper().strip()
    if 'INRAE TRANSFERT' in n or 'INRA TRANSFERT' in n:
        return 'IT'
    if n in ('INRAE', 'INRA'):
        return 'INRAE'
    if "INSTITUT NATIONAL DE RECHERCHE POUR L'AGRICULTURE" in n \
       or 'INSTITUT NATIONAL DE LA RECHERCHE AGRONOMIQUE' in n:
        return 'INRAE'
    if 'IRSTEA' in n:
        return 'IRSTEA'
    if 'CEMAGREF' in n:
        return 'CEMAGREF'
    return None


# ═══════════════════════════════════════════════════════════════
# A. Distribution des instruments
# ═══════════════════════════════════════════════════════════════
print('=' * 100)
print('A. INSTRUMENTS — Programme.Acronyme (DGDS) / Action.Titre.Francais (DGPIE)')
print('=' * 100)

dgds_instr = Counter()
for f in ('anr01_dgds_2005_projets.csv', 'anr01_dgds_2010_projets.csv'):
    for r in rows(f):
        dgds_instr[(r.get('Programme.Acronyme') or '').strip() or '(empty)'] += 1
print(f"\nDGDS: {len(dgds_instr)} instruments distincts, total {sum(dgds_instr.values()):,} projets")
print("Top 50:")
for k, v in dgds_instr.most_common(50):
    print(f"  {v:6,}  {k}")
if len(dgds_instr) > 50:
    print(f"  ... ({len(dgds_instr) - 50} autres, queue de distribution)")

dgpie_instr = Counter()
for r in rows('anr02_dgpie_projets.csv'):
    dgpie_instr[(r.get('Action.Titre.Francais') or '').strip() or '(empty)'] += 1
print(f"\nDGPIE: {len(dgpie_instr)} instruments distincts, total {sum(dgpie_instr.values()):,} projets")
print("All:")
for k, v in dgpie_instr.most_common():
    print(f"  {v:6,}  {k}")


# ═══════════════════════════════════════════════════════════════
# B. Détection INRAE/IT par nom dans les fichiers partenaires
# ═══════════════════════════════════════════════════════════════
print('\n' + '=' * 100)
print('B. DETECTION par nom dans les fichiers partenaires')
print('=' * 100)

global_tag_proj = defaultdict(set)
for f in ('anr01_dgds_2005_partenaires.csv',
          'anr01_dgds_2010_partenaires.csv',
          'anr02_dgpie_partenaires.csv'):
    tag_proj = defaultdict(set)
    tag_names = defaultdict(Counter)
    for r in rows(f):
        name = r.get('Projet.Partenaire.Nom_organisme', '')
        t = detect(name)
        if t:
            code = r.get('Projet.Code_Decision', '')
            tag_proj[t].add(code)
            tag_names[t][name.strip()] += 1
            global_tag_proj[t].add(code)
    print(f"\n  {f}:")
    for t in ('INRAE', 'IRSTEA', 'CEMAGREF', 'IT'):
        if t in tag_proj:
            print(f"    {t:<10} {len(tag_proj[t]):>5,} projets distincts "
                  f"({sum(tag_names[t].values()):>5,} lignes partenaires)")
            for nm, c in tag_names[t].most_common(4):
                print(f"        [{c:>4}] {nm[:90]}")

print(f"\n  TOTAL (toutes périodes, tous datasets, dédoublonné par Code_Decision):")
for t in ('INRAE', 'IRSTEA', 'CEMAGREF', 'IT'):
    if t in global_tag_proj:
        print(f"    {t:<10} {len(global_tag_proj[t]):>5,} projets")
union = set().union(*global_tag_proj.values())
print(f"    UNION (INRAE+IRSTEA+CEMAGREF+IT) {len(union):,} projets distincts")


# ═══════════════════════════════════════════════════════════════
# C. SIREN dataset — détection INRAE par SIREN 180070039 + IT
# ═══════════════════════════════════════════════════════════════
print('\n' + '=' * 100)
print('C. SIREN DATASET — Detection by SIREN 180070039 (INRAE) + INRAE TRANSFERT')
print('=' * 100)

INRAE_SIREN = '180070039'
inrae_projs = set()
inrae_libelles = Counter()
it_candidates = Counter()      # (siren, libellé) → count
all_codes_in_siren = set()
sample_partner_field_widths = Counter()

for r in rows('participants_siren.csv'):
    code = (r.get('Code du projet') or '').strip()
    if code:
        all_codes_in_siren.add(code)
    sirens = (r.get('Identifiant de partenaire') or '').split(';')
    types = (r.get("Type d'identifiant") or '').split(';')
    libs = (r.get('Libellé de partenaire') or '').split(';')
    sample_partner_field_widths[len(libs)] += 1
    n = max(len(sirens), len(types), len(libs))
    for i in range(n):
        s = sirens[i] if i < len(sirens) else ''
        t = types[i] if i < len(types) else ''
        l = libs[i] if i < len(libs) else ''
        if t == 'siren' and s == INRAE_SIREN:
            inrae_projs.add(code)
            inrae_libelles[l.strip()] += 1
        L = (l or '').upper()
        if 'INRAE TRANSFERT' in L or 'INRA TRANSFERT' in L:
            it_candidates[(s, l.strip())] += 1

print(f"\nProjets contenant le SIREN INRAE ({INRAE_SIREN}): {len(inrae_projs):,}")
print(f"Libellés associés à ce SIREN (top 8):")
for lab, c in inrae_libelles.most_common(8):
    print(f"  [{c:5}] {lab}")

print(f"\nCandidats INRAE TRANSFERT (libellé contient 'INRAE/INRA TRANSFERT'):")
for (s, lab), c in it_candidates.most_common(20):
    print(f"  [{c:>4}]  siren={s!r:<15}  libellé={lab}")

print(f"\nDistribution du nb de partenaires par projet (échantillon):")
for w, c in sorted(sample_partner_field_widths.most_common(10)):
    print(f"  {w:>3} partenaires: {c:,} projets")


# ═══════════════════════════════════════════════════════════════
# D. Couverture SIREN dataset sur ANR_01+ANR_02
# ═══════════════════════════════════════════════════════════════
print('\n' + '=' * 100)
print('D. COVERAGE — SIREN dataset vs ANR_01+ANR_02')
print('=' * 100)

anr_codes = set()
for f in ('anr01_dgds_2005_projets.csv', 'anr01_dgds_2010_projets.csv', 'anr02_dgpie_projets.csv'):
    for r in rows(f):
        c = (r.get('Projet.Code_Decision') or '').strip()
        if c:
            anr_codes.add(c)

inter = anr_codes & all_codes_in_siren
only_anr = anr_codes - all_codes_in_siren
only_siren = all_codes_in_siren - anr_codes
print(f"  ANR_01+02 projects total: {len(anr_codes):,}")
print(f"  SIREN dataset projects:   {len(all_codes_in_siren):,}")
print(f"  Intersection:             {len(inter):,}  ({100 * len(inter) / max(len(anr_codes), 1):.1f}% des ANR)")
print(f"  ANR sans entrée SIREN:    {len(only_anr):,}")
print(f"  SIREN sans entrée ANR:    {len(only_siren):,}")
if only_anr:
    print(f"  Echantillon ANR-only (10 premiers):")
    for code in sorted(only_anr)[:10]:
        print(f"    {code}")


# ═══════════════════════════════════════════════════════════════
# E. Pays distincts dans les partenaires
# ═══════════════════════════════════════════════════════════════
print('\n' + '=' * 100)
print('E. PAYS (Projet.Partenaire.Adresse.Pays)')
print('=' * 100)

countries = Counter()
for f in ('anr01_dgds_2005_partenaires.csv', 'anr01_dgds_2010_partenaires.csv', 'anr02_dgpie_partenaires.csv'):
    for r in rows(f):
        c = (r.get('Projet.Partenaire.Adresse.Pays') or '').strip()
        if c:
            countries[c] += 1

print(f"\nTotal pays distincts: {len(countries)}")
print("Distribution complète:")
for c, n in countries.most_common():
    print(f"  {n:>7,}  {c}")


# ═══════════════════════════════════════════════════════════════
# F. Code_RNSR — taux de remplissage pour partenaires INRAE
# ═══════════════════════════════════════════════════════════════
print('\n' + '=' * 100)
print('F. CODE_RNSR coverage for INRAE/INRA/IRSTEA/CEMAGREF (ANR_01 since 2010)')
print('=' * 100)

rnsr_filled = 0
rnsr_empty = 0
rnsr_examples = []
rnsr_unique = set()
rnsr_counter = Counter()
for r in rows('anr01_dgds_2010_partenaires.csv'):
    name = r.get('Projet.Partenaire.Nom_organisme', '')
    if not detect(name):
        continue
    rnsr = (r.get('Projet.Partenaire.Code_RNSR') or '').strip()
    if rnsr:
        rnsr_filled += 1
        rnsr_unique.add(rnsr)
        rnsr_counter[rnsr] += 1
        if len(rnsr_examples) < 20:
            ville = r.get('Projet.Partenaire.Adresse.Ville', '')
            rnsr_examples.append((rnsr, name[:55], ville))
    else:
        rnsr_empty += 1

tot = rnsr_filled + rnsr_empty
print(f"\nLignes INRAE/IRSTEA/CEMAGREF dans anr01_dgds_2010_partenaires.csv:")
print(f"  Avec Code_RNSR    : {rnsr_filled:>5,}  ({100 * rnsr_filled / max(tot, 1):.1f}%)")
print(f"  Sans Code_RNSR    : {rnsr_empty:>5,}")
print(f"  RNSR uniques      : {len(rnsr_unique):>5,}")

print(f"\nEchantillon (RNSR / organisme / ville):")
for rnsr, name, ville in rnsr_examples:
    print(f"  {rnsr:<14} {name:<55} {ville}")

print(f"\nTop 10 RNSR les plus fréquents pour INRAE:")
for rnsr, c in rnsr_counter.most_common(10):
    print(f"  [{c:>4}]  {rnsr}")
