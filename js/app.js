let ALL = [];
let VISIBLE_PROJECTS = [];
let FILTERED = [];
let VIEW_MODE = 'INRAE';
let FILTERS = {
  scope: new Set(['INRAE']),
  programme: new Set(),
  schemeGroup: new Set(),
  itRole: new Set(),
  inraeRole: new Set()
};
let SEARCH = '';
let SORT = 'startDate-desc';
let PARTNER_FILTER = null;
let UNIT_FILTER = null;
let PARTNER_PAGE = 0;
let UNIT_PAGE = 0;

function deriveViewMode() {
  const hasIT = FILTERS.scope.has('IT');
  const hasINRAE = FILTERS.scope.has('INRAE');
  if (hasIT && hasINRAE) return 'BOTH';
  if (hasIT) return 'IT';
  if (hasINRAE) return 'INRAE';
  return 'ALL';
}

function applyViewMode({ rebuild = true } = {}) {
  VIEW_MODE = deriveViewMode();
  if (VIEW_MODE === 'IT') VISIBLE_PROJECTS = ALL.filter(project => project.hasIT);
  else if (VIEW_MODE === 'INRAE') VISIBLE_PROJECTS = ALL.filter(project => project.hasINRAE);
  else if (VIEW_MODE === 'BOTH') VISIBLE_PROJECTS = ALL.filter(project => project.hasIT && project.hasINRAE);
  else VISIBLE_PROJECTS = ALL.filter(project => project.hasIT || project.hasINRAE);

  document.documentElement.classList.remove('mode-IT', 'mode-INRAE', 'mode-BOTH', 'mode-ALL');
  document.documentElement.classList.add('mode-' + VIEW_MODE);

  if (rebuild) {
    PARTNER_PAGE = 0;
    UNIT_PAGE = 0;
    buildKPIs();
    buildSidebar();
    apply();
  }
}

function persistScope() {
  try {
    localStorage.setItem('anr-it.scope', JSON.stringify([...FILTERS.scope]));
  } catch (e) {}
}

function onScopeChange() {
  if (!FILTERS.scope.has('IT')) FILTERS.itRole.clear();
  if (!FILTERS.scope.has('INRAE')) FILTERS.inraeRole.clear();
  persistScope();
  applyViewMode();
}

async function load() {
  try {
    const response = await fetch(DATA_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const raw = await response.json();

    ALL = raw.projects || [];
    window._generatedAt = raw.generatedAt || null;
    window._anrDataDate = raw.anrDataDate || null;

    ALL.forEach(project => {
      project.itRole = normRole(project.itRole || '');
      project.inraeRole = normRole(project.inraeRole || '');
      project.partners = project.partners || [];
      project.partners.forEach(partner => { partner.role = normRole(partner.role || ''); });
      project.partnerCountries = project.partnerCountries || [];
      if (!project.schemeGroup) project.schemeGroup = 'Other';
    });

    try {
      const rawScope = localStorage.getItem('anr-it.scope');
      if (rawScope) {
        const scope = JSON.parse(rawScope);
        if (Array.isArray(scope)) FILTERS.scope = new Set(scope.filter(v => v === 'IT' || v === 'INRAE'));
      }
    } catch (e) {}

    applyViewMode({ rebuild: false });
    init();
  } catch (error) {
    document.getElementById('grid').innerHTML =
      `<div class="empty"><span class="big">!</span>Cannot load <code>${DATA_URL}</code><br><small>${esc(error.message)}</small></div>`;
  }
}

function init() {
  buildKPIs();
  buildSidebar();
  bindEvents();
  apply();
  renderAbout();
  const update = document.getElementById('update-date');
  if (update) update.textContent = window._anrDataDate ? `ANR data · ${window._anrDataDate}` : 'ANR data';
}

function buildKPIs() {
  const scopedAid = VISIBLE_PROJECTS.reduce((sum, project) => sum + activeBudget(project), 0) / 1000000;
  const countries = new Set(VISIBLE_PROJECTS.flatMap(project => project.partnerCountries || [])).size;
  const units = new Set(VISIBLE_PROJECTS.flatMap(projectUnitCodes)).size;
  const label = activeColors().label;
  document.getElementById('hdr-kpis').innerHTML = `
    <div class="kpi"><span class="kpi-val">${VISIBLE_PROJECTS.length}</span><span class="kpi-lbl">${esc(label)} projects</span></div>
    <div class="kpi"><span class="kpi-val">${scopedAid.toFixed(0)}</span><span class="kpi-lbl">${esc(activeColors().budgetLabel)} M€</span></div>
    <div class="kpi"><span class="kpi-val">${units}</span><span class="kpi-lbl">RNSR units</span></div>
    <div class="kpi"><span class="kpi-val">${countries}</span><span class="kpi-lbl">Countries</span></div>`;
}

function apply() {
  const query = SEARCH.toLowerCase().trim();
  FILTERED = VISIBLE_PROJECTS.filter(project => {
    if (query) {
      const partnerText = (project.partners || []).map(partner =>
        `${partner.name || ''} ${partner.city || ''} ${partner.rnsr || ''} ${partner.leadName || ''} ${partner.leadFirstName || ''}`
      ).join(' ');
      const searchable = `${project.id} ${project.acronym} ${project.title} ${project.objective} ${project.fundingScheme} ${project.schemeGroup} ${partnerText}`.toLowerCase();
      if (!searchable.includes(query)) return false;
    }
    if (FILTERS.programme.size && !FILTERS.programme.has(project.programme)) return false;
    if (FILTERS.schemeGroup.size && !FILTERS.schemeGroup.has(project.schemeGroup)) return false;
    if (FILTERS.itRole.size && !FILTERS.itRole.has(project.itRole)) return false;
    if (FILTERS.inraeRole.size && !FILTERS.inraeRole.has(project.inraeRole)) return false;
    if (PARTNER_FILTER && !(project.partners || []).some(partner => partnerCanonicalKey(partner) === PARTNER_FILTER.key)) return false;
    if (UNIT_FILTER && !projectUnitCodes(project).includes(UNIT_FILTER)) return false;
    return true;
  });

  const [field, direction] = SORT.split('-');
  FILTERED.sort((a, b) => {
    let av;
    let bv;
    if (field === 'budget') {
      av = activeBudget(a);
      bv = activeBudget(b);
    } else if (field === 'acronym') {
      av = a.acronym || '';
      bv = b.acronym || '';
    } else if (field === 'partners') {
      av = a.partnerCount || 0;
      bv = b.partnerCount || 0;
    } else {
      av = a.startDate || '';
      bv = b.startDate || '';
    }
    const result = typeof av === 'string' ? av.localeCompare(bv, 'en') : av - bv;
    return direction === 'desc' ? -result : result;
  });

  renderAll();
}

function renderAll() {
  const count = FILTERED.length;
  document.getElementById('rcount').innerHTML =
    `<strong>${count}</strong> project${count !== 1 ? 's' : ''} of ${VISIBLE_PROJECTS.length}`;
  renderActiveFilters();
  renderCards();
  renderPartners();
  renderUnits();
}

const PILL_ACTIONS = [];

function renderActiveFilters() {
  PILL_ACTIONS.length = 0;
  const pills = [];
  const addPill = (label, clearFn) => {
    const index = PILL_ACTIONS.length;
    PILL_ACTIONS.push(clearFn);
    pills.push(`<span class="filter-pill">${label}<span class="pill-x" onclick="clearPill(${index})">×</span></span>`);
  };

  if (SEARCH.trim()) {
    addPill(`Search: ${esc(SEARCH.trim())}`, () => {
      SEARCH = '';
      document.getElementById('search').value = '';
      apply();
    });
  }
  [...FILTERS.programme].forEach(value => addPill(`Programme: ${esc(value)}`, () => {
    FILTERS.programme.delete(value);
    syncCheckbox('programme', value, false);
    apply();
  }));
  [...FILTERS.schemeGroup].forEach(value => addPill(`Action: ${esc(value)}`, () => {
    FILTERS.schemeGroup.delete(value);
    syncCheckbox('schemeGroup', value, false);
    apply();
  }));
  [...FILTERS.itRole].forEach(value => addPill(`IT role: ${esc(roleL(value))}`, () => {
    FILTERS.itRole.delete(value);
    syncCheckbox('itRole', value, false);
    apply();
  }));
  [...FILTERS.inraeRole].forEach(value => addPill(`INRAE role: ${esc(roleL(value))}`, () => {
    FILTERS.inraeRole.delete(value);
    syncCheckbox('inraeRole', value, false);
    apply();
  }));
  if (PARTNER_FILTER) {
    addPill(`Partner: ${esc(PARTNER_FILTER.label)}`, () => clearPartnerFilter());
  }
  if (UNIT_FILTER) {
    addPill(`Unit: ${esc(UNIT_FILTER)}`, () => clearUnitFilter());
  }
  document.getElementById('active-filters').innerHTML = pills.join('');
}

function clearPill(index) {
  if (PILL_ACTIONS[index]) PILL_ACTIONS[index]();
}

function syncCheckbox(key, value, checked) {
  const cb = document.querySelector(`.sidebar input[data-key="${key}"][value="${CSS.escape(value)}"]`);
  if (cb) cb.checked = checked;
}

function setView(view) {
  document.getElementById('grid').classList.toggle('cols2', view === 'grid');
  document.getElementById('v-list').classList.toggle('on', view === 'list');
  document.getElementById('v-grid').classList.toggle('on', view === 'grid');
}

function renderPager(elId, total, currentPage, setter) {
  const pages = Math.ceil(total / PER_PAGE);
  const el = document.getElementById(elId);
  el.innerHTML = `<span style="color:var(--ink-light);margin-right:4px">${total} rows</span>`;
  if (pages <= 1) return;
  const maxPages = Math.min(pages, 10);
  for (let i = 0; i < maxPages; i++) {
    el.innerHTML += `<button class="${i === currentPage ? 'on' : ''}" onclick="${setter.name}(${i})">${i + 1}</button>`;
  }
}

function bindEvents() {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(item => item.classList.remove('on'));
    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('on'));
    btn.classList.add('on');
    document.getElementById('tab-' + btn.dataset.tab).classList.add('on');
    const sortBlock = document.getElementById('sort-block');
    if (sortBlock) sortBlock.style.display = btn.dataset.tab === 'projects' ? '' : 'none';
  }));

  document.getElementById('search').addEventListener('input', event => {
    SEARCH = event.target.value;
    PARTNER_PAGE = 0;
    UNIT_PAGE = 0;
    apply();
  });

  document.getElementById('sort').addEventListener('change', event => {
    SORT = event.target.value;
    apply();
  });

  document.querySelector('.sidebar').addEventListener('change', event => {
    if (event.target.type !== 'checkbox') return;
    const key = event.target.dataset.key;
    if (!FILTERS[key]) return;
    event.target.checked ? FILTERS[key].add(event.target.value) : FILTERS[key].delete(event.target.value);
    if (key === 'scope') onScopeChange();
    else apply();
  });

  document.getElementById('btn-reset').addEventListener('click', () => {
    SEARCH = '';
    SORT = 'startDate-desc';
    PARTNER_FILTER = null;
    UNIT_FILTER = null;
    PARTNER_PAGE = 0;
    UNIT_PAGE = 0;
    Object.values(FILTERS).forEach(set => set.clear());
    FILTERS.scope = new Set(['INRAE']);
    persistScope();
    document.getElementById('search').value = '';
    document.getElementById('sort').value = 'startDate-desc';
    document.getElementById('partner-type').value = '';
    document.getElementById('unit-sort').value = 'projects-desc';
    applyViewMode();
  });

  document.getElementById('partner-type').addEventListener('change', () => {
    PARTNER_PAGE = 0;
    renderPartners();
  });

  document.getElementById('unit-sort').addEventListener('change', () => {
    UNIT_PAGE = 0;
    renderUnits();
  });
}

load();
