function renderUnits() {
  const unitMap = {};
  FILTERED.forEach(project => {
    (project.partners || []).forEach(partner => {
      if (!isInraeFamily(partner) || !partner.rnsr) return;
      if (!unitMap[partner.rnsr]) {
        unitMap[partner.rnsr] = {
          rnsr: partner.rnsr,
          cities: new Set(),
          leads: new Set(),
          projects: new Set(),
          years: new Set(),
          aid: 0
        };
      }
      const unit = unitMap[partner.rnsr];
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
    if (sort === 'city-asc') return firstValue(a.cities).localeCompare(firstValue(b.cities), 'en');
    return b.projects.size - a.projects.size || b.aid - a.aid;
  });

  const total = rows.length;
  const pageRows = rows.slice(UNIT_PAGE * PER_PAGE, (UNIT_PAGE + 1) * PER_PAGE);
  window._unitRows = pageRows;

  document.getElementById('unit-tbody').innerHTML = pageRows.length ? pageRows.map((unit, index) => {
    const years = [...unit.years].filter(Boolean).sort();
    const leads = [...unit.leads].sort().slice(0, 3);
    const cities = [...unit.cities].sort();
    const isActive = UNIT_FILTER === unit.rnsr;
    return `<tr class="is-clickable ${isActive ? 'is-active' : ''}" onclick="setUnitFilter(window._unitRows[${index}].rnsr)">
      <td><div class="name-main">${esc(unit.rnsr)}</div></td>
      <td>${esc(cities.slice(0, 2).join(', ') || '-')}</td>
      <td>${leads.length ? leads.map(esc).join('<br>') : '-'}</td>
      <td class="mono">${unit.projects.size}</td>
      <td class="mono">${years.length ? `${years[0]}-${years[years.length - 1]}` : '-'}</td>
      <td class="mono">${fmtM(unit.aid)}</td>
    </tr>`;
  }).join('') : '<tr><td colspan="6" style="text-align:center;color:var(--ink-light);padding:14px">No RNSR units match.</td></tr>';

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

