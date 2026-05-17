function openModal(id) {
  const project = ALL.find(item => item.id === id);
  if (!project) return;

  document.getElementById('m-acro').textContent = project.acronym || '-';
  document.getElementById('m-title').textContent = project.title || project.id;
  document.getElementById('m-obj').textContent = project.objective || 'No summary available.';

  const unitCount = projectUnitCodes(project).length;
  document.getElementById('m-tags').innerHTML = `
    ${progTag(project)}
    <span class="tag tg-scheme">${esc(project.schemeGroup || 'Other')}</span>
    ${entityBadges(project)}
    ${unitCount ? `<span class="tag tag-rnsr">${unitCount} RNSR</span>` : ''}`;

  document.getElementById('m-info').innerHTML = `
    <dt>Project code</dt><dd>${esc(project.id)}</dd>
    <dt>Programme</dt><dd>${esc(project.frameworkProgramme || programmeLabel(project.programme))}</dd>
    <dt>Funding scheme</dt><dd>${esc(project.fundingScheme || '-')}</dd>
    <dt>Scheme group</dt><dd>${esc(project.schemeGroup || 'Other')}</dd>
    <dt>Start</dt><dd>${fmtD(project.startDate)}</dd>
    <dt>Edition</dt><dd>${esc(project.edition || '-')}</dd>
    <dt>Total ANR aid</dt><dd>${fmtM(project.ecMaxContribution)}</dd>`;

  let participation = '';
  if (project.hasIT) {
    participation += `<dt>IT role</dt><dd>${roleL(project.itRole)}</dd>
      <dt>IT ANR aid</dt><dd>${fmtM(project.itEcContribution)}</dd>`;
  }
  if (project.hasINRAE) {
    participation += `<dt>INRAE role</dt><dd>${roleL(project.inraeRole)}</dd>
      <dt>INRAE ANR aid</dt><dd>${fmtM(project.inraeEcContribution)}</dd>`;
  }
  participation += `<dt>Partners</dt><dd>${project.partnerCount || 0} organisations</dd>
    <dt>Countries</dt><dd>${(project.partnerCountries || []).map(cc => `${flag(cc)} ${esc(cc)}`).join(', ') || '-'}</dd>`;
  document.getElementById('m-participation').innerHTML = participation;

  document.getElementById('m-pt-title').textContent = `Partners (${project.partnerCount || 0})`;
  const roleRank = { coordinator: 0, participant: 1 };
  const partners = [...(project.partners || [])].sort((a, b) => {
    const ar = roleRank[a.role] ?? 9;
    const br = roleRank[b.role] ?? 9;
    return ar - br || (a.name || '').localeCompare(b.name || '', 'en');
  });

  document.getElementById('m-partners').innerHTML = partners.map(partner => {
    const klass = partner.entity === 'IT' ? 'is-it' : isInraeFamily(partner) ? 'is-inrae' : '';
    const lead = [partner.leadFirstName, partner.leadName].filter(Boolean).join(' ');
    return `<tr class="${klass}">
      <td>${esc(partnerDisplayName(partner))}</td>
      <td>${flag(partner.country)} ${esc(partner.country || partner.countryName || '-')}</td>
      <td>${roleL(partner.role)}</td>
      <td>${esc(partner.activityType || '-')}</td>
      <td>${fmtM(partner.ecContribution)}</td>
      <td class="mono">${esc(partner.rnsr || '-')}</td>
      <td>${esc(lead || '-')}</td>
    </tr>`;
  }).join('');

  document.getElementById('overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  document.getElementById('overlay').classList.remove('open');
  document.body.style.overflow = '';
}

function overlayClick(event) {
  if (event.target === document.getElementById('overlay')) closeModal();
}

document.addEventListener('keydown', event => {
  if (event.key === 'Escape' && document.getElementById('overlay').classList.contains('open')) closeModal();
});
