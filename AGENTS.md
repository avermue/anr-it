# AGENTS.md — Portail ANR / Prospection INRAE

## 🌐 Mission

Static webapp (HTML/JS/CSS pur, sans bundler, déployable sur GitHub Pages) qui
visualise les projets ANR (DGDS depuis 2005 + DGPIE/PIA depuis 2010) impliquant
**INRAE / INRA / IRSTEA / CEMAGREF / INRAE Transfert (IT)**.

Pendant français du portail CORDIS (~/10_Code/cordis-it) qui couvre les projets
européens. Même architecture, mêmes conventions visuelles.

Objectif utilisateur : **prospection commerciale** — identifier les projets
ANR, leurs partenaires, et les unités de recherche INRAE engagées (Code_RNSR).

## 📁 Architecture cible

```
~/10_Code/anr-it/
├── AGENTS.md                        ← ce fichier
├── index.html                       ← shell (à créer, dérivé de cordis-it)
├── css/style.css                    ← (à créer, palette identique à cordis-it)
├── js/
│   ├── data.js                      ← constantes + SCHEME_GROUPS ANR
│   ├── app.js                       ← state, load, apply, events
│   ├── sidebar.js                   ← filtres
│   ├── cards.js                     ← onglet Projects
│   ├── partners.js                  ← onglet Partners
│   ├── units.js                     ← onglet Units (NOUVEAU vs cordis-it)
│   ├── modal.js                     ← modale détail projet
│   └── about.js                     ← onglet About
├── data/
│   ├── inrae_anr_projects.json      ← (généré par build_data.py)
│   └── raw/                         ← 239 MB de CSV bruts (à .gitignore)
└── scripts/
    ├── inspect_anr_sources.py       ← ✅ liste les ressources data.gouv.fr
    ├── download_anr_sources.py      ← ✅ télécharge les 9 fichiers (idempotent)
    ├── inspect_anr_schemas.py       ← ✅ profile encoding/colonnes/échantillons
    ├── profile_anr_values.py        ← ✅ profile instruments/INRAE/SIREN/RNSR
    └── build_data.py                ← ⏭️ À écrire (étape suivante)
```

## 📊 Sources de données

Téléchargées dans `data/raw/` (239 MB, **idempotent** via `download_anr_sources.py`).
Tous en **`utf-8-sig` + séparateur `;`**.

| Fichier | Lignes | Source |
|---|---:|---|
| `anr01_dgds_2005_projets.csv` | 6 463 | ANR_01 DOS/DGDS 2005-2009 |
| `anr01_dgds_2005_partenaires.csv` | 21 359 | (14 cols, pas de RNSR) |
| `anr01_dgds_2010_projets.csv` | 25 682 | ANR_01 DGDS depuis 2010 |
| `anr01_dgds_2010_partenaires.csv` | 81 300 | (15 cols, **avec Code_RNSR**) |
| `anr02_dgpie_projets.csv` | 2 685 | ANR_02 DGPIE / PIA |
| `anr02_dgpie_partenaires.csv` | 16 152 | (12 cols, pas d'aide partenaire) |
| `participants_siren.csv` | 101 615 | Apporte les SIREN (couvre 30 % des projets ANR) |

URLs stables sur `static.data.gouv.fr` (sauf participants_siren qui est servi
par Opendatasoft du Ministère ESR, export live).

## 🎯 Périmètre — onglets retenus

1. **📋 Projects**
2. **🤝 Partners**
3. **🏫 Units** — *nouveau onglet inédit vs CORDIS, pour les unités RNSR INRAE*
4. **ⓘ About**

(Pas de Geography / Disciplines / Budget / Timeline / Stats à la V1 — l'ANR ne
fournit pas la donnée correspondante, ou trop partielle.)

## ✅ Décisions data validées le 2026-05-13

Voir `memory/project_anr_decisions.md` pour le détail complet.

1. **Matching INRAE** : nom prioritaire (100 % de couverture), SIREN
   enrichissement (30 %).
2. **SIREN INRAE Transfert** = **`433960762`** (confirmé via le SIREN dataset,
   pas 433730492 comme supposé initialement).
3. **VIEW_MODE par défaut** = **`INRAE`** (IT seul = 15 projets, trop faible).
   On gardera la possibilité de retirer le scope `IT` si trop vide à l'usage.
4. **Regroupements DGDS** (9 buckets, *provisoire*) :
   AAPG, Blanc, JCJC, ASTRID, MRSEI, LabCom, T-ERC, Thématique, Other.
5. **Regroupements DGPIE** (9 buckets, *provisoire*) :
   Idex/Isite, Labex, EquipEx, EUR, IHU/RHU, SATT, Infrastructures,
   Démonstrateurs France 2030, Other.
6. **Option A — pas de status, pas de endDate**. On affiche juste
   `startDate` + `AAP.Edition`. Pas de filtre Status dans la sidebar.
7. **Onglet Units dédié** pour les unités RNSR (~143 unités INRAE distinctes,
   54 % des partenaires INRAE depuis 2010).
8. **RNSR V1 minimaliste** : on stocke `Code_RNSR` + `Responsable_scientifique`
   + `Ville` dans le JSON, **sans** enrichir avec la base RNSR officielle.
   Enrichissement V2 si souhaité après usage.

⚠️ **Les décisions 4 et 5 sont provisoires** : l'utilisateur attend retour
d'une spécialiste avant de figer les regroupements d'instruments.

## 🔑 Volumes cibles

**1 343 projets uniques** (UNION INRAE+INRA+IRSTEA+CEMAGREF+IT), même ordre de
grandeur que CORDIS (828). Détail :
- INRAE / INRA (matching nom) : 1 205 projets
- CEMAGREF (avant fusion 2020) : 83
- IRSTEA (2012–2019) : 76
- IT (INRAE Transfert) : 15 seulement

Voir `memory/project_anr_data_landscape.md` pour les chiffres complets.

## 🎨 Palette CSS — reprise intégrale du portail CORDIS

```css
--it: #1a4f8a       --it-mid: #2563ab     --it-light: #4a90d9     --it-pale: #e8f0fb
--inrae: #00847f    --inrae-mid: #009a94  --inrae-light: #4dbdb8  --inrae-pale: #e0f2f1
--both: #275562     --both-mid: #3a6e7e   --both-pale: #e8eef0
--ink: #1a1d24      --ink-mid: #3a4050    --ink-light: #6b7280    --ink-xlight: #9ca3af
```

Classes `mode-IT` / `mode-INRAE` / `mode-BOTH` / `mode-ALL` repointent `--it`
sur la couleur active. **Mécanisme à conserver tel quel** depuis cordis-it.

## 🧪 État d'avancement (2026-05-13)

- ✅ Étape 1 : Cartographie du portail CORDIS existant
- ✅ Étape 2 : Inventaire des datasets ANR (data.gouv.fr API)
- ✅ Étape 3 : Téléchargement des CSV bruts (239 MB)
- ✅ Étape 4 : Inspection des schémas
- ✅ Étape 5 : Profilage des valeurs (instruments, matching, SIREN, RNSR)
- ✅ Étape 6 : Validation des 8 décisions data ← **DERNIÈRE ÉTAPE FAITE**
- ⏭️ **Étape 7 (prochaine) : Écrire `scripts/build_data.py`**
  - Charger ANR_01 (2005 + 2010) + ANR_02 + SIREN dataset
  - Identifier les partenaires INRAE/INRA/IRSTEA/CEMAGREF par matching nom +
    enrichir avec SIREN quand dispo
  - Identifier IT par nom + SIREN 433960762
  - Reconstituer les projets : pour chaque project où INRAE/IT participe,
    récupérer tous les autres partenaires
  - Calculer `hasIT`, `hasINRAE`, `itRole`, `inraeRole`,
    `itEcContribution`, `inraeEcContribution` (DGDS uniquement),
    `partnerCountries[]` (mapping pays FR→ISO-2), `schemeGroup`
  - Conserver `Code_RNSR` + `Responsable_scientifique` par partenaire INRAE
  - Construire `anrUrl = http://www.agence-nationale-recherche.fr/?Projet={id}`
  - Produire `data/inrae_anr_projects.json` avec mêmes clés que le JSON CORDIS
    (drop : status, endDate, domains, euroSciVoc, topics, keywords, pic)
- ⏭️ Étape 8 : Adapter HTML/CSS/JS depuis cordis-it
- ⏭️ Étape 9 : Tester en local

## 🔀 Conventions

- **Langue** : français en conversation, anglais pour tous les labels UI.
- **Modifications chirurgicales** : préférer `Edit` ciblé à `Write` complet.
- **Git** : branche unique `main`. Toujours montrer le diff avant modifier.
  Ne jamais commiter ni pusher sans confirmation explicite de l'utilisateur.
- **Pas de fichier de documentation spontané** : la documentation vit ici
  (AGENTS.md) et dans la mémoire (`~/.Codex/projects/.../memory/`).
- **Test local** : après toute modification, proposer
  `python -m http.server 8080` puis indiquer **http://localhost:8080 en
  navigation privée** (cache navigateur).

## 📐 Schéma JSON cible — `data/inrae_anr_projects.json`

```js
{
  "generatedAt": "2026-05-13",
  "anrDataDate": "2026-05-02",          // last_update de l'API data.gouv.fr
  "projects": [
    {
      "id": "ANR-XX-XXXX-XXXX",         // = Code_Decision
      "acronym": "...",
      "title": "...",                   // FR si dispo, sinon EN
      "titleEn": "...",                 // (optionnel, seulement DGDS)
      "objective": "...",               // Résumé FR
      "objectiveEn": "...",             // (optionnel)
      "startDate": "YYYY-MM-DD",
      "edition": 2023,                  // AAP.Edition ou Action.Edition
      "programme": "DGDS" | "DGPIE",    // ← équivalent FP7/H2020/HE
      "frameworkProgramme": "Plan d'action ANR" | "PIA / France 2030",
      "fundingScheme": "...",           // Programme.Acronyme ou Action.Titre
      "schemeGroup": "AAPG" | "Blanc" | ... | "Other",
      "ecMaxContribution": 1234567.89,  // Aide totale projet
      "partnerCount": 5,
      "partnerCountries": ["FR", "DE", "ES"],  // ISO-2
      "anrUrl": "http://www.agence-nationale-recherche.fr/?Projet=ANR-XX-...",
      "hasIT": false,
      "hasINRAE": true,
      "itRole": "" | "coordinator" | "participant",
      "inraeRole": "coordinator" | "participant",
      "itEcContribution": 0,
      "inraeEcContribution": 234567.89,  // 0 si DGPIE (pas dispo)
      "partners": [
        {
          "name": "...",
          "shortName": "",              // peu rempli côté ANR
          "country": "FR",
          "city": "Versailles",
          "region": "Île-de-France",
          "activityType": "Etablissement public",  // = Categorie_organisme
          "role": "coordinator" | "participant",
          "ecContribution": 234567.89,  // null si DGPIE
          "siren": "180070039",         // depuis SIREN dataset, null si absent
          "rnsr": "201119649P",         // Code_RNSR, null si absent
          "leadName": "DUPONT",         // Responsable scientifique
          "leadFirstName": "Marie",
          "leadORCID": "0000-0002-..."  // si dispo
        }
      ]
    }
  ]
}
```

## 🐛 Pièges connus

- **Pays en libellé français** : il faut un mapping `"France"→FR`,
  `"Allemagne"→DE`, etc. (146 pays distincts à mapper). Les DOM-TOM
  (`Réunion`, `Guadeloupe`, etc.) → rattacher à `FR` pour la map, garder le
  libellé exact dans la card.
- **SIREN multi-valué** dans le 3e dataset : colonnes
  `Identifiant de partenaire` / `Type d'identifiant` / `Libellé de partenaire`
  sont des **listes parallèles séparées par `;` intra-cellule** (CSV quoté).
  Quand `type=lib_generique` → pas de SIREN, juste un libellé.
- **Couverture SIREN parcellaire** (30 % des projets ANR), surtout 2005 mal
  couvert (les `ANR-05-BDIV-*` n'y sont pas) → matching nom prioritaire.
- **DGPIE n'a pas d'aide par partenaire** : `inraeEcContribution` sera 0 pour
  les projets DGPIE.
- **`Projet.Resume.Anglais` n'existe pas en DGPIE** : on garde le FR.
- **`Programme.Acronyme` (DGDS)** vs **`Action.Titre.Francais` (DGPIE)** :
  schémas projets différents — gérer les deux chemins dans build_data.py.
