const DATA_URL = 'data/inrae_anr_projects.json';
const PER_PAGE = 25;

const SCHEME_ORDER = [
  'AAPG',
  'Blanc',
  'JCJC',
  'ASTRID',
  'MRSEI',
  'LabCom',
  'T-ERC',
  'Thématique',
  'Idex/Isite',
  'Labex',
  'EquipEx',
  'EUR',
  'IHU/RHU',
  'SATT',
  'Infrastructures',
  'Démonstrateurs France 2030',
  'Other'
];

const CC_NAMES = {
  AD: 'Andorra', AE: 'United Arab Emirates', AF: 'Afghanistan', AL: 'Albania',
  AM: 'Armenia', AO: 'Angola', AR: 'Argentina', AT: 'Austria', AU: 'Australia',
  AZ: 'Azerbaijan', BA: 'Bosnia & Herzegovina', BB: 'Barbados', BD: 'Bangladesh',
  BE: 'Belgium', BF: 'Burkina Faso', BG: 'Bulgaria', BH: 'Bahrain', BJ: 'Benin',
  BM: 'Bermuda', BO: 'Bolivia', BR: 'Brazil', CA: 'Canada', CD: 'DR Congo',
  CF: 'Central African Republic', CG: 'Congo', CH: 'Switzerland', CI: "Côte d'Ivoire",
  CL: 'Chile', CM: 'Cameroon', CN: 'China', CO: 'Colombia', CR: 'Costa Rica',
  CU: 'Cuba', CV: 'Cabo Verde', CY: 'Cyprus', CZ: 'Czechia', DE: 'Germany',
  DK: 'Denmark', DZ: 'Algeria', EC: 'Ecuador', EE: 'Estonia', EG: 'Egypt',
  ES: 'Spain', ET: 'Ethiopia', FI: 'Finland', FJ: 'Fiji', FR: 'France',
  GA: 'Gabon', GB: 'United Kingdom', GE: 'Georgia', GH: 'Ghana', GL: 'Greenland',
  GM: 'Gambia', GN: 'Guinea', GR: 'Greece', GT: 'Guatemala', GU: 'Guam',
  GW: 'Guinea-Bissau', HK: 'Hong Kong', HR: 'Croatia', HT: 'Haiti', HU: 'Hungary',
  ID: 'Indonesia', IE: 'Ireland', IL: 'Israel', IN: 'India', IR: 'Iran',
  IS: 'Iceland', IT: 'Italy', JO: 'Jordan', JP: 'Japan', KE: 'Kenya',
  KG: 'Kyrgyzstan', KH: 'Cambodia', KM: 'Comoros', KN: 'Saint Kitts and Nevis',
  KR: 'South Korea', KW: 'Kuwait', KZ: 'Kazakhstan', LA: 'Laos', LB: 'Lebanon',
  LT: 'Lithuania', LU: 'Luxembourg', LV: 'Latvia', MA: 'Morocco', MC: 'Monaco',
  MD: 'Moldova', MG: 'Madagascar', MK: 'North Macedonia', ML: 'Mali', MN: 'Mongolia',
  MT: 'Malta', MU: 'Mauritius', MW: 'Malawi', MX: 'Mexico', MY: 'Malaysia',
  MZ: 'Mozambique', NA: 'Namibia', NE: 'Niger', NF: 'Norfolk Island', NG: 'Nigeria',
  NI: 'Nicaragua', NL: 'Netherlands', NO: 'Norway', NP: 'Nepal', NZ: 'New Zealand',
  PE: 'Peru', PG: 'Papua New Guinea', PH: 'Philippines', PK: 'Pakistan', PL: 'Poland',
  PS: 'Palestine', PT: 'Portugal', PY: 'Paraguay', QA: 'Qatar', RO: 'Romania',
  RS: 'Serbia', RU: 'Russia', SA: 'Saudi Arabia', SC: 'Seychelles', SD: 'Sudan',
  SE: 'Sweden', SG: 'Singapore', SI: 'Slovenia', SK: 'Slovakia', SN: 'Senegal',
  TG: 'Togo', TH: 'Thailand', TN: 'Tunisia', TR: 'Turkey', TT: 'Trinidad and Tobago',
  TW: 'Taiwan', TZ: 'Tanzania', UA: 'Ukraine', UG: 'Uganda', US: 'United States',
  UY: 'Uruguay', UZ: 'Uzbekistan', VN: 'Vietnam', VU: 'Vanuatu', YE: 'Yemen',
  ZA: 'South Africa', ZW: 'Zimbabwe'
};

const ROLE_LABELS = {
  coordinator: 'Coordinator',
  participant: 'Participant'
};

function esc(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function normRole(role) {
  return role === 'coordinator' ? 'coordinator' : role ? 'participant' : '';
}

function roleL(role) {
  return ROLE_LABELS[role] || role || '-';
}

function fmtM(value) {
  const n = Number(value || 0);
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M€';
  if (n >= 1000) return Math.round(n / 1000) + 'k€';
  if (n > 0) return Math.round(n) + '€';
  return '-';
}

function fmtD(value) {
  return value ? String(value).slice(0, 7) : '-';
}

function fmtY(value) {
  return value ? String(value).slice(0, 4) : '';
}

function flag(cc) {
  if (!cc || cc.length !== 2) return esc(cc || '');
  const code = cc.toLowerCase();
  const name = esc(CC_NAMES[cc] || cc);
  return `<img src="https://flagcdn.com/16x12/${code}.png" alt="${esc(cc)}" title="${name}" style="width:16px;height:12px;vertical-align:middle;border-radius:1px;margin:0 1px" onerror="this.replaceWith(document.createTextNode('${esc(cc)}'))">`;
}

function programmeLabel(programme) {
  if (programme === 'DGPIE') return 'PIA / France 2030';
  return 'Plan d’action ANR';
}

function progTag(project) {
  if ((project.programme || '').toUpperCase() === 'DGPIE') {
    return '<span class="tag tg-dgpie">DGPIE</span>';
  }
  return '<span class="tag tg-dgds">DGDS</span>';
}

function activeColors() {
  if (VIEW_MODE === 'IT') {
    return { label: 'IT', budgetLabel: 'IT aid' };
  }
  if (VIEW_MODE === 'BOTH') {
    return { label: 'IT & INRAE', budgetLabel: 'Scoped aid' };
  }
  if (VIEW_MODE === 'ALL') {
    return { label: 'All entities', budgetLabel: 'Scoped aid' };
  }
  return { label: 'INRAE', budgetLabel: 'INRAE aid' };
}

function activeBudget(project) {
  if (VIEW_MODE === 'IT') return project.itEcContribution || 0;
  if (VIEW_MODE === 'INRAE') return project.inraeEcContribution || 0;
  return (project.itEcContribution || 0) + (project.inraeEcContribution || 0);
}

function entityBadges(project) {
  const tags = [];
  if (project.hasIT) tags.push(`<span class="tag tag-entity tag-it">IT · ${roleL(project.itRole)}</span>`);
  if (project.hasINRAE) tags.push(`<span class="tag tag-entity tag-inrae">INRAE · ${roleL(project.inraeRole)}</span>`);
  return tags.join('');
}

function budgetChips(project) {
  const chips = [];
  if (project.ecMaxContribution > 0) chips.push(`<span class="cb cb-total">Project: ${fmtM(project.ecMaxContribution)}</span>`);
  if (project.hasIT) chips.push(`<span class="cb cb-it">IT: ${fmtM(project.itEcContribution)}</span>`);
  if (project.hasINRAE) chips.push(`<span class="cb cb-inrae">INRAE: ${fmtM(project.inraeEcContribution)}</span>`);
  return chips.length ? `<div class="card-budgets">${chips.join('')}</div>` : '<span class="card-budget">-</span>';
}

function isInraeFamily(partner) {
  return ['INRAE', 'IRSTEA', 'CEMAGREF'].includes(partner.entity);
}

function partnerDisplayName(partner) {
  if (partner.entity === 'IT') return `${partner.name} · IT`;
  if (isInraeFamily(partner)) return `${partner.name} · ${partner.entity}`;
  return partner.name || '-';
}

function projectUnitCodes(project) {
  return [...new Set((project.partners || [])
    .filter(partner => isInraeFamily(partner) && partner.rnsr)
    .map(partner => partner.rnsr))];
}

