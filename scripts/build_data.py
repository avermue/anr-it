#!/usr/bin/env python3
"""
Build the static ANR dataset used by the webapp.

The script reads the raw ANR CSV exports in data/raw/, keeps projects involving
INRAE-family organisations or INRAE Transfert, enriches partners with SIREN
identifiers when the complementary ESR export provides them, and writes
data/inrae_anr_projects.json.
"""

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
csv.field_size_limit(10**9)

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT = BASE_DIR / "data" / "inrae_anr_projects.json"
SOURCE_METADATA = RAW_DIR / "source_metadata.json"

ENCODING = "utf-8-sig"
SEP = ";"
DEFAULT_ANR_DATA_DATE = "2026-05-02"

INRAE_SIREN = "180070039"
IT_SIREN = "433960762"
EXPECTED_TOTAL = 1326

PROJECT_FILES = [
    ("DGDS", "anr01_dgds_2005_projets.csv"),
    ("DGDS", "anr01_dgds_2010_projets.csv"),
    ("DGPIE", "anr02_dgpie_projets.csv"),
]

PARTNER_FILES = [
    ("DGDS", "anr01_dgds_2005_partenaires.csv"),
    ("DGDS", "anr01_dgds_2010_partenaires.csv"),
    ("DGPIE", "anr02_dgpie_partenaires.csv"),
]

INRAE_FAMILY = {"INRAE", "IRSTEA", "CEMAGREF"}


def log(message):
    print(message, flush=True)


def ss(value, maxlen=None):
    text = "" if value is None else str(value).strip()
    return text[:maxlen] if maxlen else text


def sf(value, default=0.0):
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    text = text.replace("\u00a0", "").replace(" ", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return default


def si(value):
    text = ss(value)
    if not text:
        return None
    try:
        return int(float(text.replace(",", ".")))
    except ValueError:
        return None


def normalize_text(value):
    text = ss(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def split_multi(value):
    return [part.strip() for part in ss(value).split(";")]


def norm_date(value):
    text = ss(value)
    if re.fullmatch(r"\d{4}", text):
        return f"{text}-01-01"
    return text


def is_true(value):
    return normalize_text(value) in {"TRUE", "VRAI", "1", "YES", "OUI"}


def read_rows(filename):
    path = RAW_DIR / filename
    with path.open("r", encoding=ENCODING, newline="") as handle:
        yield from csv.DictReader(handle, delimiter=SEP)


def load_anr_data_date():
    if not SOURCE_METADATA.exists():
        return DEFAULT_ANR_DATA_DATE

    try:
        with SOURCE_METADATA.open("r", encoding="utf-8") as handle:
            metadata = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_ANR_DATA_DATE

    dates = []
    for dataset_key in ("dgds", "dgpie"):
        value = (metadata.get("datasets") or {}).get(dataset_key, {}).get("last_update")
        if isinstance(value, str) and len(value) >= 10:
            dates.append(value[:10])
    return max(dates) if dates else DEFAULT_ANR_DATA_DATE


COUNTRY_CODES = {
    "Afrique du Sud": "ZA",
    "Albanie": "AL",
    "Algérie": "DZ",
    "Allemagne": "DE",
    "Arabie saoudite": "SA",
    "Argentine": "AR",
    "Arménie": "AM",
    "Australie": "AU",
    "Autriche": "AT",
    "Azerbaïdjan": "AZ",
    "Bangladesh": "BD",
    "Barbade": "BB",
    "Belgique": "BE",
    "Bénin": "BJ",
    "Bermudes": "BM",
    "Bolivie": "BO",
    "Brésil": "BR",
    "Bulgarie": "BG",
    "Burkina Faso": "BF",
    "Cabo Verde": "CV",
    "Cambodge": "KH",
    "Cameroun": "CM",
    "Canada": "CA",
    "Chili": "CL",
    "Chine": "CN",
    "Chypre": "CY",
    "Colombie": "CO",
    "Comores": "KM",
    "Congo": "CG",
    "Congo (République démocratique du)": "CD",
    "Cook (Îles)": "CK",
    "Corée (République de)": "KR",
    "Costa Rica": "CR",
    "Côte d'Ivoire": "CI",
    "Croatie": "HR",
    "Cuba": "CU",
    "Danemark": "DK",
    "Égypte": "EG",
    "Émirats arabes unis": "AE",
    "Équateur": "EC",
    "Espagne": "ES",
    "Estonie": "EE",
    "États-Unis d'Amérique": "US",
    "Éthiopie": "ET",
    "Fidji": "FJ",
    "Finlande": "FI",
    "France": "FR",
    "Gabon": "GA",
    "Gambie": "GM",
    "Géorgie": "GE",
    "Ghana": "GH",
    "Grèce": "GR",
    "Groenland": "GL",
    "Guam": "GU",
    "Guatemala": "GT",
    "Guinée": "GN",
    "Guinée-Bissau": "GW",
    "Haïti": "HT",
    "Hong Kong": "HK",
    "Hongrie": "HU",
    "Inde": "IN",
    "Indonésie": "ID",
    "Iran": "IR",
    "Irlande": "IE",
    "Islande": "IS",
    "Israël": "IL",
    "Italie": "IT",
    "Japon": "JP",
    "Jordanie": "JO",
    "Kazakhstan": "KZ",
    "Kenya": "KE",
    "Kirghizistan": "KG",
    "Koweït": "KW",
    "Laos": "LA",
    "Lettonie": "LV",
    "Liban": "LB",
    "Lituanie": "LT",
    "Luxembourg": "LU",
    "Macédoine du Nord": "MK",
    "Madagascar": "MG",
    "Malaisie": "MY",
    "Mali": "ML",
    "Malte": "MT",
    "Maroc": "MA",
    "Mexique": "MX",
    "Moldavie": "MD",
    "Monaco": "MC",
    "Mongolie": "MN",
    "Mozambique": "MZ",
    "Namibie": "NA",
    "Népal": "NP",
    "Nicaragua": "NI",
    "Niger": "NE",
    "Nigéria": "NG",
    "Norfolk (Île)": "NF",
    "Norvège": "NO",
    "Nouvelle-Zélande": "NZ",
    "Ouganda": "UG",
    "Ouzbékistan": "UZ",
    "Pakistan": "PK",
    "Palestine": "PS",
    "Papouasie-Nouvelle-Guinée": "PG",
    "Paraguay": "PY",
    "Pays-Bas": "NL",
    "Pérou": "PE",
    "Philippines": "PH",
    "Pologne": "PL",
    "Portugal": "PT",
    "Qatar": "QA",
    "République centrafricaine": "CF",
    "Roumanie": "RO",
    "Royaume-Uni de Grande-Bretagne et d'Irlande du Nord": "GB",
    "Russie": "RU",
    "Saint-Kitts-et-Nevis": "KN",
    "Sénégal": "SN",
    "Serbie": "RS",
    "Seychelles": "SC",
    "Sierra Leone": "SL",
    "Singapour": "SG",
    "Slovaquie": "SK",
    "Slovénie": "SI",
    "Soudan": "SD",
    "Suède": "SE",
    "Suisse": "CH",
    "Taïwan": "TW",
    "Tanzanie": "TZ",
    "Tchad": "TD",
    "Tchéquie": "CZ",
    "Thaïlande": "TH",
    "Togo": "TG",
    "Trinité-et-Tobago": "TT",
    "Tunisie": "TN",
    "Turquie": "TR",
    "Ukraine": "UA",
    "Uruguay": "UY",
    "Vanuatu": "VU",
    "Viet Nam": "VN",
    "Yémen": "YE",
    "Zimbabwe": "ZW",
}

FRENCH_TERRITORIES = {
    "Guadeloupe",
    "Guyane française",
    "Martinique",
    "Mayotte",
    "Nouvelle-Calédonie",
    "Polynésie française",
    "Réunion",
}

COUNTRY_MAP = {
    normalize_text(country): code for country, code in COUNTRY_CODES.items()
}
for territory in FRENCH_TERRITORIES:
    COUNTRY_MAP[normalize_text(territory)] = "FR"


def country_to_iso(country):
    if not ss(country):
        return ""
    return COUNTRY_MAP.get(normalize_text(country), "")


def detect_entity(name, siren=None, country=None):
    # Scope detection intentionally mirrors the validated profiling baseline:
    # SIREN enriches partners, but does not broaden the INRAE-family perimeter.
    text = ss(name).upper()
    if not text.strip():
        return None
    norm = normalize_text(name)
    country = country or ""
    is_foreign = bool(country and country != "FR")

    if "INRAE TRANSFERT" in text or "INRA TRANSFERT" in text:
        return None if is_foreign else "IT"

    if text.strip() in {"INRAE", "INRA"}:
        return None if is_foreign else "INRAE"

    if "INSTITUT NATIONAL DE RECHERCHE POUR L'AGRICULTURE" in text:
        return None if is_foreign else "INRAE"

    if "INSTITUT NATIONAL DE LA RECHERCHE AGRONOMIQUE" in text:
        foreign_inra = any(token in norm for token in ("MAROC", "TUNISIE", "TUNIS", "ALGERIE", "ALGER"))
        if is_foreign or foreign_inra:
            return None
        return "INRAE"

    if "IRSTEA" in text:
        return None if is_foreign else "IRSTEA"

    if "CEMAGREF" in text:
        return None if is_foreign else "CEMAGREF"

    return None


def role_from_row(row):
    return "coordinator" if is_true(row.get("Projet.Partenaire.Est_coordinateur")) else "participant"


def best_role(roles):
    return "coordinator" if "coordinator" in roles else ("participant" if roles else "")


def scheme_group_dgds(scheme):
    code = normalize_text(scheme)
    compact = code.replace(" ", "")
    if not code:
        return "Other"
    if compact.startswith("AAPG") or code == "APPEL A PROJETS GENERIQUE":
        return "AAPG"
    if "BLANC" in code:
        return "Blanc"
    if code in {"JC", "JCJC"} or "JEUNES CHERCHE" in code:
        return "JCJC"
    if compact.startswith("ASTRID"):
        return "ASTRID"
    if compact.startswith("MRSEI") or compact == "MRSE":
        return "MRSEI"
    if compact.startswith("LABCOM"):
        return "LabCom"
    if compact in {"TERC", "T-ERC", "TER"} or "T ERC" in code:
        return "T-ERC"
    return "Thématique"


DGPIE_GROUPS = {
    "Idex/Isite": {
        "CAMP", "CMAS", "CONV", "GURE", "IACL", "IDEX", "IDES", "IDFI",
        "IDFN", "NCUN", "SACL",
    },
    "Labex": {"LABX"},
    "EquipEx": {"EQPX"},
    "EUR": {"EURE", "SFRI"},
    "IHU/RHU": {"IAHU", "IBHU", "IHU", "RHU", "RHUS"},
    "SATT": {"SATE", "SATM", "SATT"},
    "Infrastructures": {
        "BINF", "CRYO", "ESRE", "FR6G", "FRAN", "FRAT", "FRBN", "FRMI",
        "FRVC", "IEEC", "IEED", "INBS", "INDF", "IRMC", "NANB", "NUWA",
        "RESH", "ZEUS",
    },
}


def scheme_group_dgpie(scheme):
    code = normalize_text(scheme).replace(" ", "")
    if not code:
        return "Other"
    for group, codes in DGPIE_GROUPS.items():
        if code in codes:
            return group
    if code.startswith("EX"):
        return "EquipEx"
    if code.startswith("DM") or code.startswith("PE"):
        return "Démonstrateurs France 2030"
    return "Other"


def scheme_group(programme, scheme):
    if programme == "DGDS":
        return scheme_group_dgds(scheme)
    return scheme_group_dgpie(scheme)


def load_siren_entries():
    by_project = defaultdict(list)
    label_map = defaultdict(lambda: defaultdict(set))
    short_map = defaultdict(lambda: defaultdict(set))
    projects_by_siren = defaultdict(set)

    for row in read_rows("participants_siren.csv"):
        project_id = ss(row.get("Code du projet"))
        if not project_id:
            continue

        identifiers = split_multi(row.get("Identifiant de partenaire"))
        id_types = split_multi(row.get("Type d'identifiant"))
        labels = split_multi(row.get("Libellé de partenaire"))
        shorts = split_multi(row.get("Sigle de partenaire"))
        type_codes = split_multi(row.get("Code du type de partenaire"))
        type_labels = split_multi(row.get("Type de partenaire"))
        width = max(
            len(identifiers),
            len(id_types),
            len(labels),
            len(shorts),
            len(type_codes),
            len(type_labels),
        )

        for index in range(width):
            identifier = identifiers[index] if index < len(identifiers) else ""
            id_type = id_types[index] if index < len(id_types) else ""
            label = labels[index] if index < len(labels) else ""
            short = shorts[index] if index < len(shorts) else ""
            type_code = type_codes[index] if index < len(type_codes) else ""
            type_label = type_labels[index] if index < len(type_labels) else ""

            siren = re.sub(r"\D", "", identifier)
            if normalize_text(id_type) != "SIREN" or len(siren) != 9:
                continue

            entry = {
                "siren": siren,
                "label": ss(label),
                "short": ss(short),
                "typeCode": ss(type_code),
                "typeLabel": ss(type_label),
            }
            by_project[project_id].append(entry)
            projects_by_siren[siren].add(project_id)

            norm_label = normalize_text(label)
            if len(norm_label) >= 4:
                label_map[project_id][norm_label].add(siren)

            norm_short = normalize_text(short)
            if len(norm_short) >= 2:
                short_map[project_id][norm_short].add(siren)

    return {
        "entries": by_project,
        "labels": label_map,
        "shorts": short_map,
        "projects_by_siren": projects_by_siren,
    }


def only_value(values):
    values = {value for value in values if value}
    if len(values) == 1:
        return next(iter(values))
    return None


def lookup_siren(project_id, partner_name, partner_short, siren_data):
    name_norm = normalize_text(partner_name)
    short_norm = normalize_text(partner_short)

    if name_norm:
        siren = only_value(siren_data["labels"][project_id].get(name_norm, set()))
        if siren:
            return siren
    if short_norm:
        siren = only_value(siren_data["shorts"][project_id].get(short_norm, set()))
        if siren:
            return siren

    candidates = sorted(
        siren_data["entries"].get(project_id, []),
        key=lambda entry: len(normalize_text(entry["label"])),
        reverse=True,
    )
    for entry in candidates:
        label_norm = normalize_text(entry["label"])
        if len(label_norm) < 8:
            continue
        if label_norm in name_norm or name_norm in label_norm:
            return entry["siren"]

    return None


def project_has_siren(project_id, siren, siren_data):
    return project_id in siren_data["projects_by_siren"].get(siren, set())


def load_projects():
    projects = {}
    duplicates = []

    for programme, filename in PROJECT_FILES:
        for row in read_rows(filename):
            project_id = ss(row.get("Projet.Code_Decision"))
            if not project_id:
                continue

            if programme == "DGDS":
                funding_scheme = ss(row.get("Programme.Acronyme"))
                title_fr = ss(row.get("Projet.Titre.Francais"))
                title_en = ss(row.get("Projet.Titre.Anglais"))
                objective_fr = ss(row.get("Projet.Resume.Francais"))
                objective_en = ss(row.get("Projet.Resume.Anglais"))
                start_date = norm_date(row.get("Projet.T0 scientifique"))
                edition = si(row.get("AAP.Edition"))
                amount = sf(row.get("Projet.Montant.AF.Aide_allouee.ANR"))
                framework = "Plan d'action ANR"
            else:
                funding_scheme = ss(row.get("Action.Titre.Francais"))
                title_fr = ss(row.get("Projet.Titre.Francais"))
                title_en = ""
                objective_fr = ss(row.get("Projet.Resume.Francais"))
                objective_en = ""
                start_date = norm_date(row.get("Projet.Date_debut"))
                edition = si(row.get("Action.Edition"))
                amount = sf(row.get("Projet.Aide_allouee"))
                framework = "PIA / France 2030"

            if project_id in projects:
                duplicates.append(project_id)
                continue

            projects[project_id] = {
                "id": project_id,
                "acronym": ss(row.get("Projet.Acronyme")),
                "title": title_fr or title_en,
                "titleEn": title_en,
                "objective": objective_fr,
                "objectiveEn": objective_en,
                "startDate": start_date,
                "edition": edition,
                "programme": programme,
                "frameworkProgramme": framework,
                "fundingScheme": funding_scheme,
                "fundingSchemeShort": funding_scheme,
                "schemeGroup": scheme_group(programme, funding_scheme),
                "ecMaxContribution": amount,
                "anrUrl": f"http://www.agence-nationale-recherche.fr/?Projet={project_id}",
            }

    return projects, duplicates


def build_partner(row, programme, siren_data, unknown_countries):
    project_id = ss(row.get("Projet.Code_Decision"))
    name = ss(row.get("Projet.Partenaire.Nom_organisme"))
    short = ""
    siren = lookup_siren(project_id, name, short, siren_data)
    country_name = ss(row.get("Projet.Partenaire.Adresse.Pays"))
    country = country_to_iso(country_name)
    if country_name and not country:
        unknown_countries[country_name] += 1

    name_entity = detect_entity(name, country=country)
    if not siren and name_entity == "IT" and project_has_siren(project_id, IT_SIREN, siren_data):
        siren = IT_SIREN
    if not siren and name_entity == "INRAE" and project_has_siren(project_id, INRAE_SIREN, siren_data):
        siren = INRAE_SIREN

    entity = detect_entity(name, siren, country)

    ec_contribution = None
    if programme == "DGDS":
        ec_contribution = sf(row.get("Projet.Partenaire.Aide_allouee.ANR"))

    return {
        "name": name,
        "shortName": short,
        "country": country,
        "countryName": country_name,
        "city": ss(row.get("Projet.Partenaire.Adresse.Ville")),
        "region": ss(row.get("Projet.Partenaire.Adresse.Region")),
        "activityType": ss(row.get("Projet.Partenaire.Categorie_organisme")),
        "role": role_from_row(row),
        "ecContribution": ec_contribution,
        "siren": siren,
        "rnsr": ss(row.get("Projet.Partenaire.Code_RNSR")) or None,
        "leadName": ss(row.get("Projet.Partenaire.Responsable_scientifique.Nom")),
        "leadFirstName": ss(row.get("Projet.Partenaire.Responsable_scientifique.Prenom")),
        "leadORCID": ss(row.get("Projet.Partenaire.Responsable_scientifique.ORCID")),
        "entity": entity or "",
        "_programme": programme,
        "_projectAcronym": ss(row.get("Projet.Acronyme")),
        "_edition": si(row.get("Action.Edition")),
    }


def load_partners(siren_data):
    partners_by_project = defaultdict(list)
    unknown_countries = Counter()

    for programme, filename in PARTNER_FILES:
        for row in read_rows(filename):
            project_id = ss(row.get("Projet.Code_Decision"))
            if not project_id:
                continue
            partners_by_project[project_id].append(
                build_partner(row, programme, siren_data, unknown_countries)
            )

    return partners_by_project, unknown_countries


def sum_contributions(partners):
    return round(sum(p.get("ecContribution") or 0.0 for p in partners), 2)


def year_from_project_id(project_id):
    match = re.match(r"ANR-(\d{2})-", project_id)
    if not match:
        return None
    year = int(match.group(1))
    return 2000 + year if year < 80 else 1900 + year


def skeleton_project(project_id, partners):
    programme = next((p.get("_programme") for p in partners if p.get("_programme")), "DGDS")
    acronym = next((p.get("_projectAcronym") for p in partners if p.get("_projectAcronym")), "")
    edition = next((p.get("_edition") for p in partners if p.get("_edition")), None)
    if edition is None:
        edition = year_from_project_id(project_id)
    framework = "Plan d'action ANR" if programme == "DGDS" else "PIA / France 2030"
    funding_scheme = ""
    return {
        "id": project_id,
        "acronym": acronym,
        "title": acronym or project_id,
        "titleEn": "",
        "objective": "",
        "objectiveEn": "",
        "startDate": f"{edition}-01-01" if edition else "",
        "edition": edition,
        "programme": programme,
        "frameworkProgramme": framework,
        "fundingScheme": funding_scheme,
        "fundingSchemeShort": funding_scheme,
        "schemeGroup": scheme_group(programme, funding_scheme),
        "ecMaxContribution": sum_contributions(partners),
        "anrUrl": f"http://www.agence-nationale-recherche.fr/?Projet={project_id}",
        "_isSkeleton": True,
    }


def public_partner(partner):
    return {
        key: value
        for key, value in partner.items()
        if not key.startswith("_")
    }


def assemble_projects(projects_base, partners_by_project):
    selected = []
    skeleton_projects = []

    for project_id, partners in partners_by_project.items():
        inrae_partners = [p for p in partners if p.get("entity") in INRAE_FAMILY]
        it_partners = [p for p in partners if p.get("entity") == "IT"]
        if not inrae_partners and not it_partners:
            continue

        base = projects_base.get(project_id)
        if not base:
            base = skeleton_project(project_id, partners)
            skeleton_projects.append(project_id)

        project = dict(base)
        partner_countries = sorted({
            p["country"] for p in partners if p.get("country")
        })
        project.update({
            "partnerCount": len(partners),
            "partnerCountries": partner_countries,
            "hasIT": bool(it_partners),
            "hasINRAE": bool(inrae_partners),
            "itRole": best_role([p["role"] for p in it_partners]),
            "inraeRole": best_role([p["role"] for p in inrae_partners]),
            "itEcContribution": sum_contributions(it_partners),
            "inraeEcContribution": sum_contributions(inrae_partners),
            "partners": [public_partner(p) for p in partners],
        })
        project.pop("_isSkeleton", None)
        selected.append(project)

    selected.sort(key=lambda item: (item.get("startDate") or "", item.get("id") or ""), reverse=True)
    return selected, skeleton_projects


def summarize(projects, duplicates, skeleton_projects, unknown_countries):
    total = len(projects)
    rnsr_values = {
        partner["rnsr"]
        for project in projects
        for partner in project["partners"]
        if partner.get("entity") in INRAE_FAMILY and partner.get("rnsr")
    }
    group_counts = Counter(project["schemeGroup"] for project in projects)

    log("")
    log("=" * 52)
    log("SUMMARY")
    log("=" * 52)
    log(f"Total              : {total:,}")
    log(f"  DGDS             : {sum(1 for p in projects if p['programme'] == 'DGDS'):,}")
    log(f"  DGPIE            : {sum(1 for p in projects if p['programme'] == 'DGPIE'):,}")
    log("  ----------------------")
    log(f"  IT only          : {sum(1 for p in projects if p['hasIT'] and not p['hasINRAE']):,}")
    log(f"  INRAE only       : {sum(1 for p in projects if p['hasINRAE'] and not p['hasIT']):,}")
    log(f"  IT + INRAE       : {sum(1 for p in projects if p['hasIT'] and p['hasINRAE']):,}")
    log("  ----------------------")
    log(f"  With IT          : {sum(1 for p in projects if p['hasIT']):,}")
    log(f"  With INRAE       : {sum(1 for p in projects if p['hasINRAE']):,}")
    log(f"  INRAE coord.     : {sum(1 for p in projects if p['inraeRole'] == 'coordinator'):,}")
    log(f"  RNSR units       : {len(rnsr_values):,}")
    log(f"  Partner countries: {len({c for p in projects for c in p['partnerCountries']}):,}")
    log(f"  Total ANR aid    : {sum(p['ecMaxContribution'] for p in projects) / 1e6:.1f} M€")
    log(f"  INRAE aid        : {sum(p['inraeEcContribution'] for p in projects) / 1e6:.1f} M€")
    log(f"  IT aid           : {sum(p['itEcContribution'] for p in projects) / 1e6:.1f} M€")

    log("")
    log("Scheme groups:")
    for group, count in group_counts.most_common():
        log(f"  {group:<28} {count:>5,}")

    if duplicates:
        log("")
        log(f"WARNING: {len(duplicates):,} duplicate project id(s) skipped.")
    if skeleton_projects:
        log("")
        log(f"WARNING: {len(skeleton_projects):,} project(s) built from partner metadata only.")
    if unknown_countries:
        log("")
        log("WARNING: unmapped countries:")
        for country, count in unknown_countries.most_common():
            log(f"  {count:>5,}  {country}")
    if total != EXPECTED_TOTAL:
        log("")
        log(f"WARNING: expected {EXPECTED_TOTAL:,} projects, generated {total:,}.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default=str(OUTPUT),
        help="Output JSON path, defaults to data/inrae_anr_projects.json",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    log("Loading SIREN enrichment...")
    siren_data = load_siren_entries()
    log(f"  Projects with SIREN data: {len(siren_data['entries']):,}")

    log("Loading ANR projects...")
    projects_base, duplicates = load_projects()
    log(f"  Project metadata rows: {len(projects_base):,}")

    log("Loading ANR partners...")
    partners_by_project, unknown_countries = load_partners(siren_data)
    log(f"  Projects with partner rows: {len(partners_by_project):,}")

    log("Assembling retained projects...")
    projects, skeleton_projects = assemble_projects(projects_base, partners_by_project)
    anr_data_date = load_anr_data_date()

    output = {
        "generatedAt": date.today().isoformat(),
        "anrDataDate": anr_data_date,
        "projects": projects,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, ensure_ascii=False, indent=2)

    summarize(projects, duplicates, skeleton_projects, unknown_countries)
    size_mb = output_path.stat().st_size / 1024 / 1024
    log("")
    log(f"OK: {output_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
