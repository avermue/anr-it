function buildSidebar() {
  buildScopeList();
  buildList('f-programme', 'programme', [...new Set(VISIBLE_PROJECTS.map(p => p.programme))].sort(), p => p.programme, programmeLabel);
  buildSchemeGroups();
  renderRoleSection();
  if (VIEW_MODE !== 'INRAE') populateRoleList('f-it-role', 'itRole', p => p.itRole);
  if (VIEW_MODE !== 'IT') populateRoleList('f-inrae-role', 'inraeRole', p => p.inraeRole);
  syncSidebarCheckboxes();
}

function buildScopeList() {
  const el = document.getElementById('f-scope');
  const cIT = ALL.filter(p => p.hasIT).length;
  const cINRAE = ALL.filter(p => p.hasINRAE).length;
  el.innerHTML = `
    <label class="ci"><input type="checkbox" data-key="scope" value="IT">IT<span class="cc">${cIT}</span></label>
    <label class="ci"><input type="checkbox" data-key="scope" value="INRAE">INRAE<span class="cc">${cINRAE}</span></label>`;
}

function buildSchemeGroups() {
  const counts = {};
  VISIBLE_PROJECTS.forEach(project => {
    counts[project.schemeGroup] = (counts[project.schemeGroup] || 0) + 1;
  });
  const values = Object.keys(counts).sort((a, b) => {
    const ai = SCHEME_ORDER.indexOf(a);
    const bi = SCHEME_ORDER.indexOf(b);
    if (ai !== -1 || bi !== -1) return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
    return a.localeCompare(b, 'en');
  });
  const el = document.getElementById('f-scheme-group');
  el.innerHTML = values.map(value => `
    <label class="ci"><input type="checkbox" data-key="schemeGroup" value="${esc(value)}">
    ${esc(value)}<span class="cc">${counts[value]}</span></label>`).join('');
}

function buildList(elId, key, values, getter, labelFn) {
  const counts = {};
  VISIBLE_PROJECTS.forEach(project => {
    const value = getter(project);
    if (Array.isArray(value)) value.forEach(v => { if (v) counts[v] = (counts[v] || 0) + 1; });
    else if (value) counts[value] = (counts[value] || 0) + 1;
  });
  const el = document.getElementById(elId);
  el.innerHTML = values.map(value => `
    <label class="ci"><input type="checkbox" data-key="${key}" value="${esc(value)}">
    ${labelFn ? labelFn(value) : esc(value)}<span class="cc">${counts[value] || 0}</span></label>`).join('');
}

function renderRoleSection() {
  const sec = document.getElementById('role-section');
  if (VIEW_MODE === 'IT') {
    sec.innerHTML = '<div class="fb"><span class="ft">IT Role</span><div class="cl" id="f-it-role"></div></div>';
  } else if (VIEW_MODE === 'INRAE') {
    sec.innerHTML = '<div class="fb"><span class="ft">INRAE Role</span><div class="cl" id="f-inrae-role"></div></div>';
  } else {
    sec.innerHTML = `
      <div class="fb"><span class="ft">IT Role</span><div class="cl" id="f-it-role"></div></div>
      <hr class="fr">
      <div class="fb"><span class="ft">INRAE Role</span><div class="cl" id="f-inrae-role"></div></div>`;
  }
}

function populateRoleList(elId, key, getter) {
  const counts = {};
  VISIBLE_PROJECTS.forEach(project => {
    const role = getter(project);
    if (role) counts[role] = (counts[role] || 0) + 1;
  });
  const values = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
  buildList(elId, key, values, getter, roleL);
}

function syncSidebarCheckboxes() {
  document.querySelectorAll('.sidebar input[type="checkbox"][data-key]').forEach(cb => {
    const key = cb.dataset.key;
    cb.checked = Boolean(FILTERS[key] && FILTERS[key].has(cb.value));
  });
}
