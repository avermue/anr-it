function renderUnits() {
  const unitMap = {};
  FILTERED.forEach(project => {
    (project.partners || []).forEach(partner => {
      if (!isInraeFamily(partner) || !partner.rnsr) return;
      if (!unitMap[partner.rnsr]) {
        unitMap[partner.rnsr] = {
          rnsr: partner.rnsr,
          names: new Map(),
          acronyms: new Set(),
          types: new Set(),
          departments: new Set(),
          cities: new Set(),
          leads: new Set(),
          projects: new Set(),
          years: new Set(),
          aid: 0,
          url: ''
        };
      }
      const unit = unitMap[partner.rnsr];
      const unitName = partner.unitName || partner.name;
      if (unitName) unit.names.set(unitName, (unit.names.get(unitName) || 0) + 1);
      if (partner.unitAcronym) unit.acronyms.add(partner.unitAcronym);
      if (partner.unitType) unit.types.add(partner.unitType);
      if (partner.unitDepartment) unit.departments.add(partner.unitDepartment);
      if (!unit.url && partner.unitUrl) unit.url = partner.unitUrl;
      if (partner.city) unit.cities.add(partner.city);
      const lead = [partner.leadFirstName, partner.leadName].filter(Boolean).join(' ');
      if (lead) unit.leads.add(lead);
      unit.projects.add(project.id);
      if (project.startDate) unit.years.add(fmtY(project.startDate));
      unit.aid += partner.ecContribution || 0;
    });
  });

  const sort = document.getElementById('unit-sort').value;
  let rows = Object.values(unitMap);
  rows.sort((a, b) => {
    if (sort === 'budget-desc') return b.aid - a.aid || b.projects.size - a.projects.size;
    if (sort === 'rnsr-asc') return a.rnsr.localeCompare(b.rnsr, 'en');
    if (sort === 'department-asc') return firstValue(a.departments).localeCompare(firstValue(b.departments), 'en');
    if (sort === 'city-asc') return firstValue(a.cities).localeCompare(firstValue(b.cities), 'en');
    return b.projects.size - a.projects.size || b.aid - a.aid;
  });

  const total = rows.length;
  const pageRows = rows.slice(UNIT_PAGE * PER_PAGE, (UNIT_PAGE + 1) * PER_PAGE);
  window._unitRows = pageRows;

  document.getElementById('unit-tbody').innerHTML = pageRows.length ? pageRows.map((unit, index) => {
    const years = [...unit.years].filter(Boolean).sort();
    const name = dominantName(unit.names);
    const nameLink = unit.url
      ? `<a href="${esc(unit.url)}" target="_blank" rel="noopener noreferrer" onclick="event.stopPropagation()">${esc(name)}</a>`
      : esc(name);
    const meta = [[...unit.types].sort()[0], [...unit.acronyms].sort()[0]].filter(Boolean).join(' ');
    const departments = [...unit.departments].sort();
    const leads = [...unit.leads].sort().slice(0, 3);
    const cities = [...unit.cities].sort();
    const isActive = UNIT_FILTER === unit.rnsr;
    return `<tr class="is-clickable ${isActive ? 'is-active' : ''}" onclick="setUnitFilter(window._unitRows[${index}].rnsr)">
      <td><div class="name-main">${esc(unit.rnsr)}</div></td>
      <td><div class="name-main">${nameLink}</div>${meta ? `<div class="name-sub">${esc(meta)}</div>` : ''}</td>
      <td>${departments.length ? departments.slice(0, 2).map(esc).join('<br>') : '-'}</td>
      <td>${esc(cities.slice(0, 2).join(', ') || '-')}</td>
      <td>${leads.length ? leads.map(esc).join('<br>') : '-'}</td>
      <td class="mono">${unit.projects.size}</td>
      <td class="mono">${years.length ? `${years[0]}-${years[years.length - 1]}` : '-'}</td>
      <td class="mono">${fmtM(unit.aid)}</td>
    </tr>`;
  }).join('') : '<tr><td colspan="8" style="text-align:center;color:var(--ink-light);padding:14px">No RNSR units match.</td></tr>';

  document.getElementById('units-subtitle').textContent = `${total} RNSR units in ${FILTERED.length} filtered projects`;
  renderUnitFilterIndicator();
  renderPager('unit-pager', total, UNIT_PAGE, setUnitPage);
}

function firstValue(set) {
  return [...set].sort()[0] || '';
}

function renderUnitFilterIndicator() {
  const el = document.getElementById('unit-filter-active');
  const label = document.getElementById('unit-filter-label');
  if (!UNIT_FILTER) {
    el.classList.remove('on');
    return;
  }
  label.textContent = `Filtering projects by RNSR unit: ${UNIT_FILTER}`;
  el.classList.add('on');
}

function setUnitFilter(rnsr) {
  UNIT_FILTER = UNIT_FILTER === rnsr ? null : rnsr;
  apply();
}

function clearUnitFilter() {
  UNIT_FILTER = null;
  apply();
}

function setUnitPage(page) {
  UNIT_PAGE = page;
  renderUnits();
}
