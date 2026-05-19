/* DataDiggers — site behaviors */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile menu toggle
  const toggle = document.querySelector('.menu-toggle');
  const links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      links.classList.toggle('open');
      toggle.setAttribute('aria-expanded', links.classList.contains('open'));
    });
    // Close menu when a link is clicked
    links.querySelectorAll('a').forEach((a) => {
      a.addEventListener('click', () => {
        if (window.innerWidth <= 720) links.classList.remove('open');
      });
    });
  }

  // Year in footer
  const year = document.getElementById('current-year');
  if (year) year.textContent = new Date().getFullYear();

  // Generic contact form (no backend — replace with your handler later)
  document.querySelectorAll('form[data-dd-form]').forEach((form) => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const success = form.querySelector('.form-success');
      if (success) success.classList.add('show');
      form.reset();
      setTimeout(() => success && success.classList.remove('show'), 6000);
    });
  });

  // Reveal on scroll for elements with [data-reveal]
  const reveals = document.querySelectorAll('[data-reveal]');
  if (reveals.length && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = 1;
          entry.target.style.transform = 'translateY(0)';
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    reveals.forEach((el) => {
      el.style.opacity = 0;
      el.style.transform = 'translateY(24px)';
      el.style.transition = 'opacity 0.7s ease, transform 0.7s ease';
      io.observe(el);
    });
  }
});
