/* DataDiggers — shared header & footer.
   Auto-injects into <header data-dd-header> and <footer data-dd-footer>. */

(function () {
  // Compute path prefix: pages in /pages/ need ../ to reach root
  const isSubpage = location.pathname.includes('/pages/');
  const r = isSubpage ? '../' : '';

  const headerHTML = `
    <div class="container nav">
      <a href="${r}index.html" class="brand">
        <span class="brand-mark">DD</span>
        <span>DataDiggers</span>
      </a>
      <nav>
        <ul class="nav-links">
          <li class="has-dropdown">
            <a href="#" class="dropdown-toggle">Solutions</a>
            <div class="dropdown">
              <div class="dropdown-section">Done For You</div>
              <a href="${r}pages/qualitative-market-research.html">Qualitative Research</a>
              <a href="${r}pages/quantitative-market-research.html">Quantitative Research</a>
              <div class="dropdown-section">Done With You</div>
              <a href="${r}pages/proprietary-panels.html">Proprietary Panels</a>
              <a href="${r}pages/own-audience.html">Own Audience</a>
              <a href="${r}pages/syntheo.html">Syntheo</a>
              <a href="${r}pages/modeliq.html">Modeliq</a>
              <a href="${r}pages/correlix.html">Correlix</a>
              <a href="${r}pages/neopulse.html">NeoPulse</a>
              <a href="${r}pages/omnibus.html">Omnibus</a>
              <div class="dropdown-section">Do It Yourself</div>
              <a href="${r}pages/do-it-yourself.html">Brainactive Platform</a>
            </div>
          </li>
          <li><a href="${r}pages/quality-without-compromise.html">Quality</a></li>
          <li class="has-dropdown">
            <a href="#" class="dropdown-toggle">About</a>
            <div class="dropdown">
              <a href="${r}pages/company.html">Company</a>
              <a href="${r}pages/meet-the-team.html">Meet the Team</a>
              <a href="${r}pages/careers.html">Careers</a>
              <a href="${r}pages/csr.html">CSR</a>
            </div>
          </li>
          <li><a href="${r}pages/blog.html">Blog</a></li>
          <li><a href="${r}pages/contact.html">Contact</a></li>
        </ul>
      </nav>
      <div class="nav-cta">
        <a href="${r}pages/request-a-quote.html" class="btn btn-secondary">Request a Quote</a>
        <a href="${r}pages/request-a-demo.html" class="btn btn-primary">Request a Demo</a>
        <button class="menu-toggle" aria-label="Open menu" aria-expanded="false">☰</button>
      </div>
    </div>
  `;

  const footerHTML = `
    <div class="container">
      <div class="footer-grid">
        <div class="footer-brand">
          <div class="brand">
            <span class="brand-mark">DD</span>
            <span>DataDiggers</span>
          </div>
          <p>Technology-driven market research. Trusted by 1,000+ clients across 65+ countries since 2015.</p>
        </div>
        <div class="footer-col">
          <h5>Solutions</h5>
          <ul>
            <li><a href="${r}pages/qualitative-market-research.html">Qualitative</a></li>
            <li><a href="${r}pages/quantitative-market-research.html">Quantitative</a></li>
            <li><a href="${r}pages/proprietary-panels.html">Proprietary Panels</a></li>
            <li><a href="${r}pages/own-audience.html">Own Audience</a></li>
            <li><a href="${r}pages/syntheo.html">Syntheo</a></li>
            <li><a href="${r}pages/modeliq.html">Modeliq</a></li>
            <li><a href="${r}pages/correlix.html">Correlix</a></li>
            <li><a href="${r}pages/neopulse.html">NeoPulse</a></li>
            <li><a href="${r}pages/omnibus.html">Omnibus</a></li>
            <li><a href="${r}pages/do-it-yourself.html">Brainactive (DIY)</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h5>About</h5>
          <ul>
            <li><a href="${r}pages/company.html">Company</a></li>
            <li><a href="${r}pages/meet-the-team.html">Meet the Team</a></li>
            <li><a href="${r}pages/careers.html">Careers</a></li>
            <li><a href="${r}pages/csr.html">CSR</a></li>
            <li><a href="${r}pages/contact.html">Contact</a></li>
            <li><a href="${r}pages/quality-without-compromise.html">Quality & Compliance</a></li>
          </ul>
        </div>
        <div class="footer-col">
          <h5>Legal</h5>
          <ul>
            <li><a href="${r}pages/privacy-policy.html">Privacy Policy</a></li>
            <li><a href="${r}pages/terms-and-conditions.html">Terms & Conditions</a></li>
            <li><a href="${r}pages/cookie-policy.html">Cookie Policy</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <span>© <span id="current-year">2026</span> DataDiggers. All Rights Reserved.</span>
        <span>ISO 20252:2019 Certified · GDPR Compliant</span>
      </div>
    </div>
  `;

  const headerEl = document.querySelector('header[data-dd-header]');
  const footerEl = document.querySelector('footer[data-dd-footer]');
  if (headerEl) {
    headerEl.classList.add('site-header');
    headerEl.innerHTML = headerHTML;
  }
  if (footerEl) {
    footerEl.classList.add('site-footer');
    footerEl.innerHTML = footerHTML;
  }
})();
