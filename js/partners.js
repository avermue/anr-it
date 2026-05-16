function renderPartners() {
  const typeSelect = document.getElementById('partner-type');
  populatePartnerTypes(typeSelect);

  const type = typeSelect.value;
  const orgMap = {};
  FILTERED.forEach(project => {
    (project.partners || []).forEach(partner => {
      if (!partner.name) return;
      const key = partnerCanonicalKey(partner);
      if (!orgMap[key]) {
        orgMap[key] = {
          key,
          label: partnerCanonicalLabel(partner),
          names: new Map(),
          countries: new Set(),
          countryNames: new Set(),
          activityTypes: new Set(),
          sirens: new Set(),
          entity: partner.entity || '',
          projects: new Set(),
          aid: 0
        };
      }
      orgMap[key].names.set(partner.name, (orgMap[key].names.get(partner.name) || 0) + 1);
      if (partner.country) orgMap[key].countries.add(partner.country);
      if (partner.countryName) orgMap[key].countryNames.add(partner.countryName);
      if (partner.activityType) orgMap[key].activityTypes.add(partner.activityType);
      if (partner.siren) orgMap[key].sirens.add(partner.siren);
      orgMap[key].projects.add(project.id);
      orgMap[key].aid += partner.ecContribution || 0;
      if (!orgMap[key].entity && partner.entity) orgMap[key].entity = partner.entity;
    });
  });

  let rows = Object.values(orgMap)
    .map(row => {
      row.name = row.label || dominantName(row.names);
      row.country = [...row.countries].sort();
      row.countryName = [...row.countryNames].sort();
      row.activityType = [...row.activityTypes].sort();
      row.siren = [...row.sirens].sort();
      return row;
    })
    .filter(row => !type || row.activityType.includes(type))
    .sort((a, b) => b.projects.size - a.projects.size || b.aid - a.aid || a.name.localeCompare(b.name, 'en'));

  const total = rows.length;
  const pageRows = rows.slice(PARTNER_PAGE * PER_PAGE, (PARTNER_PAGE + 1) * PER_PAGE);
  window._partnerRows = pageRows;

  const tbody = document.getElementById('partner-tbody');
  tbody.innerHTML = pageRows.length ? pageRows.map((row, index) => {
    const isActive = PARTNER_FILTER && PARTNER_FILTER.key === row.key;
    const badges = row.key === 'entity:IT'
      ? '<span class="tag tag-it">IT</span>'
      : row.key === 'entity:INRAE'
        ? '<span class="tag tag-inrae">INRAE</span>'
        : row.key === 'entity:IRSTEA_CEMAGREF'
          ? '<span class="tag tag-inrae">IRSTEA/CEMAGREF</span>'
        : '';
    const countryHtml = row.country.length
      ? row.country.slice(0, 4).map(cc => `${flag(cc)} ${esc(cc)}`).join('<br>') + (row.country.length > 4 ? `<br><span class="name-sub">+${row.country.length - 4}</span>` : '')
      : esc(row.countryName[0] || '-');
    const typeHtml = row.activityType.length > 1 ? `${esc(row.activityType[0])}<div class="name-sub">+${row.activityType.length - 1} types</div>` : esc(row.activityType[0] || '-');
    const sirenHtml = row.siren.length > 1 ? `${esc(row.siren[0])}<div class="name-sub">+${row.siren.length - 1}</div>` : esc(row.siren[0] || '-');
    const variants = row.names.size > 1 ? `<div class="name-sub">${row.names.size} name variants</div>` : '';
    return `<tr class="is-clickable ${isActive ? 'is-active' : ''}" onclick="setPartnerFilter(window._partnerRows[${index}])">
      <td><div class="name-main">${esc(row.name)} ${badges}</div>${variants}</td>
      <td>${countryHtml}</td>
      <td>${typeHtml}</td>
      <td class="mono">${sirenHtml}</td>
      <td class="mono">${row.projects.size}</td>
      <td class="mono">${fmtM(row.aid)}</td>
    </tr>`;
  }).join('') : '<tr><td colspan="6" style="text-align:center;color:var(--ink-light);padding:14px">No partners match.</td></tr>';

  document.getElementById('partners-subtitle').textContent = `${total} organisations in ${FILTERED.length} filtered projects`;
  renderPartnerFilterIndicator();
  renderPager('partner-pager', total, PARTNER_PAGE, setPartnerPage);
}

function populatePartnerTypes(select) {
  const current = select.value;
  const counts = {};
  FILTERED.forEach(project => {
    (project.partners || []).forEach(partner => {
      if (partner.activityType) counts[partner.activityType] = (counts[partner.activityType] || 0) + 1;
    });
  });
  const values = Object.keys(counts).sort((a, b) => counts[b] - counts[a] || a.localeCompare(b, 'en'));
  select.innerHTML = '<option value="">All types</option>' + values.map(value =>
    `<option value="${esc(value)}">${esc(value)} (${counts[value]})</option>`
  ).join('');
  if (values.includes(current)) select.value = current;
}

function partnerCanonicalKey(partner) {
  if (partner.entity === 'IT') return 'entity:IT';
  if (partner.entity === 'INRAE') return 'entity:INRAE';
  if (['IRSTEA', 'CEMAGREF'].includes(partner.entity)) return 'entity:IRSTEA_CEMAGREF';
  const known = knownInstitution(partner);
  if (known) return `known:${known.key}`;
  if (partner.siren) return `siren:${partner.siren}`;
  return `name:${normalisePartnerName(partner.name)}|country:${partner.country || partner.countryName || ''}`;
}

function partnerCanonicalLabel(partner) {
  if (partner.entity === 'IT') return 'INRAE Transfert';
  if (partner.entity === 'INRAE') return 'INRAE / INRA';
  if (['IRSTEA', 'CEMAGREF'].includes(partner.entity)) return 'IRSTEA / CEMAGREF';
  const known = knownInstitution(partner);
  if (known) return known.label;
  return '';
}

function knownInstitution(partner) {
  const n = normalisePartnerName(partner.name);
  const country = partner.country || '';
  if (country && country !== 'FR') return null;
  if (n.includes('INSTITUT PASTEUR') && /\b(MADAGASCAR|CAMBODGE|CAMBODGIEN|GUADELOUPE)\b/.test(n)) return null;
  const rules = [
    ['CNRS', 'CNRS', ['CENTRE NATIONAL DE LA RECHERCHE SCIENTIFIQUE', ' CNRS ']],
    ['INSERM', 'INSERM', ['INSTITUT NATIONAL DE LA SANTE ET DE LA RECHERCHE MEDICALE', ' INSERM ']],
    ['CIRAD', 'CIRAD', ['CENTRE DE COOPERATION INTERNATIONALE EN RECHERCHE AGRONOMIQUE POUR LE DEVELOPPEMENT', ' CIRAD ']],
    ['CEA', 'CEA', ['COMMISSARIAT A L ENERGIE ATOMIQUE', ' CEA ']],
    ['IRD', 'IRD', ['INSTITUT DE RECHERCHE POUR LE DEVELOPPEMENT', ' IRD ']],
    ['INSTITUT_PASTEUR', 'Institut Pasteur', ['INSTITUT PASTEUR']],
    ['IFREMER', 'IFREMER', ['INSTITUT FRANCAIS DE RECHERCHE POUR L EXPLOITATION DE LA MER', ' IFREMER ']],
    ['ANSES', 'ANSES', ['AGENCE NATIONALE DE SECURITE SANITAIRE', ' ANSES ']]
  ];
  const padded = ` ${n} `;
  for (const [key, label, needles] of rules) {
    if (needles.some(needle => padded.includes(needle))) return { key, label };
  }
  return null;
}

function normalisePartnerName(name) {
  return String(name || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toUpperCase()
    .replace(/\s+[-–/]\s+(UMR|UR|USC|UMS|UMT|UNITE)\b.*$/g, '')
    .replace(/[^A-Z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function dominantName(names) {
  return [...names.entries()]
    .sort((a, b) => b[1] - a[1] || a[0].length - b[0].length || a[0].localeCompare(b[0], 'en'))[0]?.[0] || '-';
}

function renderPartnerFilterIndicator() {
  const el = document.getElementById('partner-filter-active');
  const label = document.getElementById('partner-filter-label');
  if (!PARTNER_FILTER) {
    el.classList.remove('on');
    return;
  }
  label.textContent = `Filtering projects by partner: ${PARTNER_FILTER.label}`;
  el.classList.add('on');
}

function setPartnerFilter(row) {
  if (PARTNER_FILTER && PARTNER_FILTER.key === row.key) {
    PARTNER_FILTER = null;
  } else {
    PARTNER_FILTER = { key: row.key, label: row.name };
  }
  apply();
}

function clearPartnerFilter() {
  PARTNER_FILTER = null;
  apply();
}

function setPartnerPage(page) {
  PARTNER_PAGE = page;
  renderPartners();
}
