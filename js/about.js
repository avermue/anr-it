function renderAbout() {
  const dataDate = window._anrDataDate || window._generatedAt || '-';
  const projects = ALL.length;
  const withIT = ALL.filter(p => p.hasIT).length;
  const withINRAE = ALL.filter(p => p.hasINRAE).length;
  const units = new Set(ALL.flatMap(projectUnitCodes)).size;
  const dgds = ALL.filter(p => p.programme === 'DGDS').length;
  const dgpie = ALL.filter(p => p.programme === 'DGPIE').length;

  document.getElementById('about-body').innerHTML = `
    <section class="about-sec">
      <div class="about-sec-title">Mission</div>
      <p class="about-text">This observatory tracks ANR projects involving INRAE-family organisations and INRAE Transfert. It is designed for commercial prospection: identify projects, partner organisations, and INRAE research units through RNSR codes.</p>
    </section>
    <section class="about-sec">
      <div class="about-sec-title">Dataset</div>
      <ul class="about-list">
        <li><strong>${projects}</strong> retained projects</li>
        <li><strong>${dgds}</strong> DGDS projects and <strong>${dgpie}</strong> DGPIE / PIA projects</li>
        <li><strong>${withINRAE}</strong> projects with INRAE-family participation</li>
        <li><strong>${withIT}</strong> projects with INRAE Transfert participation</li>
        <li><strong>${units}</strong> distinct RNSR units</li>
      </ul>
    </section>
    <section class="about-sec">
      <div class="about-sec-title">Sources</div>
      <ul class="about-list">
        <li>ANR open data exports: DGDS since 2005 and DGPIE / PIA since 2010</li>
        <li>ESR SIREN participant export for partial SIREN enrichment</li>
        <li>Raw CSV files are processed locally by <code>scripts/build_data.py</code></li>
        <li>ANR data date: <strong>${esc(dataDate)}</strong></li>
      </ul>
    </section>
    <section class="about-sec">
      <div class="about-sec-title">Notes</div>
      <p class="about-text">ANR data has no reliable status or end date in this V1, so the app focuses on start date, edition, schemes, partners, aid amounts, and RNSR units. DGPIE does not provide partner-level aid, which means INRAE and IT aid totals are available mainly for DGDS projects.</p>
    </section>`;

  const ver = document.getElementById('about-version');
  if (ver) ver.textContent = dataDate && dataDate !== '-' ? `· data ${dataDate}` : '';
}

