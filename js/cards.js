function renderCards() {
  const grid = document.getElementById('grid');
  if (!FILTERED.length) {
    grid.innerHTML = '<div class="empty"><span class="big">∅</span>No projects match.</div>';
    return;
  }

  grid.innerHTML = FILTERED.map(project => {
    const flags = (project.partnerCountries || []).map(flag).join('');
    const objective = project.objective
      ? `<div class="card-obj">${esc(project.objective)}</div>`
      : '<div class="card-obj">No summary available.</div>';
    const unitCount = projectUnitCodes(project).length;
    const rnsrTag = unitCount ? `<span class="tag tag-rnsr">${unitCount} RNSR</span>` : '';
    return `<div class="card" onclick="openModal('${esc(project.id)}')">
      <div class="card-top">
        <span class="card-acro" title="${esc(project.acronym || project.id)}">${esc(project.acronym || '-')}</span>
        <span class="card-title">${esc(project.title || project.id)}</span>
      </div>
      <div class="card-body">
        ${objective}
        <div class="card-tags">
          ${progTag(project)}
          <span class="tag tg-scheme">${esc(project.schemeGroup || 'Other')}</span>
          ${entityBadges(project)}
          ${rnsrTag}
        </div>
      </div>
      <div class="card-foot">
        <span class="card-meta">${fmtD(project.startDate)} · ${project.edition || '-'} · ${project.partnerCount || 0} partners</span>
        ${budgetChips(project)}
        <span class="card-flags" title="${esc((project.partnerCountries || []).join(', '))}">${flags}</span>
        <a class="card-link" href="${esc(project.anrUrl)}" target="_blank" onclick="event.stopPropagation()">ANR</a>
      </div>
    </div>`;
  }).join('');
}

