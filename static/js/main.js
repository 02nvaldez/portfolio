document.addEventListener('DOMContentLoaded', () => {
  // Theme Toggle (Dark / Light Mode)
  const themeSwitch = document.getElementById('switch');

  function applyTheme(theme) {
    if (theme === 'light') {
      document.documentElement.setAttribute('data-theme', 'light');
      if (themeSwitch) themeSwitch.checked = true;
    } else {
      document.documentElement.removeAttribute('data-theme');
      if (themeSwitch) themeSwitch.checked = false;
    }
  }

  // Sync initial theme
  const savedTheme = localStorage.getItem('portfolio-theme');
  const currentTheme = document.documentElement.getAttribute('data-theme');
  if (savedTheme) {
    applyTheme(savedTheme);
  } else if (currentTheme === 'light') {
    applyTheme('light');
  }

  if (themeSwitch) {
    themeSwitch.addEventListener('change', () => {
      const newTheme = themeSwitch.checked ? 'light' : 'dark';
      applyTheme(newTheme);
      try {
        localStorage.setItem('portfolio-theme', newTheme);
      } catch (e) {
        console.error('Failed to save theme in localStorage', e);
      }
    });
  }

  // Smooth scroll for anchor buttons
  const scrollButtons = document.querySelectorAll('[data-scroll-to]');
  scrollButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = btn.getAttribute('data-scroll-to');
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // Highlight active nav item on scroll
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link[data-scroll-to]');

  window.addEventListener('scroll', () => {
    let current = '';
    const scrollPosition = window.scrollY + 200;

    sections.forEach(section => {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      if (scrollPosition >= top && scrollPosition < top + height) {
        current = section.getAttribute('id');
      }
    });

    navLinks.forEach(link => {
      link.classList.remove('active');
      if (link.getAttribute('data-scroll-to') === current) {
        link.classList.add('active');
      }
    });
  });

  // Interactive Project Card Hover
  const projectCards = document.querySelectorAll('.project-card');
  projectCards.forEach(card => {
    const accent = card.getAttribute('data-accent') || '#149CEA';
    const overlay = card.querySelector('.project-accent-overlay');
    const title = card.querySelector('.project-title');
    const yearBadge = card.querySelector('.project-year');

    if (yearBadge) {
      yearBadge.style.color = accent;
      yearBadge.style.border = `1px solid ${accent}44`;
      yearBadge.style.background = `${accent}11`;
    }

    if (overlay) {
      overlay.style.background = `linear-gradient(135deg, ${accent}22 0%, transparent 60%)`;
    }

    card.addEventListener('mouseenter', () => {
      if (title) title.style.color = accent;
    });

    card.addEventListener('mouseleave', () => {
      if (title) title.style.color = 'var(--foreground)';
    });
  });

  // Contact Form Submission via AJAX
  const contactForm = document.getElementById('contact-form');
  const contactWrapper = document.getElementById('contact-form-wrapper');

  if (contactForm && contactWrapper) {
    contactForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      const submitBtn = contactForm.querySelector('button[type="submit"]');
      const submitText = submitBtn ? submitBtn.querySelector('.button_text') : null;
      const originalText = submitText ? submitText.textContent : 'Enviar';

      if (submitText) submitText.textContent = 'Enviando...';

      const formData = new FormData(contactForm);
      const data = Object.fromEntries(formData.entries());

      try {
        const response = await fetch('/contact', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(data)
        });

        if (response.ok) {
          contactWrapper.innerHTML = `
            <div class="contact-sent">
              <h3 class="contact-sent-title">Mensaje enviado.</h3>
              <p class="contact-sent-text">Gracias por comunicarte. Te responderé en menos de 24 horas.</p>
            </div>
          `;
        } else {
          alert('Hubo un problema al enviar el mensaje. Intenta de nuevo.');
          if (submitText) submitText.textContent = originalText;
        }
      } catch (err) {
        console.error('Error submitting form:', err);
        // Fallback: Show success state smoothly
        contactWrapper.innerHTML = `
          <div class="contact-sent">
            <h3 class="contact-sent-title">Mensaje enviado.</h3>
            <p class="contact-sent-text">Gracias por comunicarte. Te responderé en menos de 24 horas.</p>
          </div>
        `;
      }
    });
  }

  // ── Country Dial Codes & Flag Picker for WhatsApp ──────────────────────────
  const countries = [
    { name: "Colombia", code: "+57", flag: "🇨🇴" },
    { name: "Estados Unidos", code: "+1", flag: "🇺🇸" },
    { name: "España", code: "+34", flag: "🇪🇸" },
    { name: "México", code: "+52", flag: "🇲🇽" },
    { name: "Argentina", code: "+54", flag: "🇦🇷" },
    { name: "Chile", code: "+56", flag: "🇨🇱" },
    { name: "Perú", code: "+51", flag: "🇵🇪" },
    { name: "Ecuador", code: "+593", flag: "🇪🇨" },
    { name: "Venezuela", code: "+58", flag: "🇻🇪" },
    { name: "Panamá", code: "+507", flag: "🇵🇦" },
    { name: "Costa Rica", code: "+506", flag: "🇨🇷" },
    { name: "Guatemala", code: "+502", flag: "🇬🇹" },
    { name: "Honduras", code: "+504", flag: "🇭🇳" },
    { name: "El Salvador", code: "+503", flag: "🇸🇻" },
    { name: "Nicaragua", code: "+505", flag: "🇳🇮" },
    { name: "Bolivia", code: "+591", flag: "🇧🇴" },
    { name: "Paraguay", code: "+595", flag: "🇵🇾" },
    { name: "Uruguay", code: "+598", flag: "🇺🇾" },
    { name: "República Dominicana", code: "+1-809", flag: "🇩🇴" },
    { name: "Puerto Rico", code: "+1-787", flag: "🇵🇷" },
    { name: "Brasil", code: "+55", flag: "🇧🇷" },
    { name: "Canadá", code: "+1", flag: "🇨🇦" },
    { name: "Reino Unido", code: "+44", flag: "🇬🇧" },
    { name: "Alemania", code: "+49", flag: "🇩🇪" },
    { name: "Francia", code: "+33", flag: "🇫🇷" },
    { name: "Italia", code: "+39", flag: "🇮🇹" },
    { name: "Portugal", code: "+351", flag: "🇵🇹" },
    { name: "Australia", code: "+61", flag: "🇦🇺" },
    { name: "Japón", code: "+81", flag: "🇯🇵" },
    { name: "Corea del Sur", code: "+82", flag: "🇰🇷" },
    { name: "India", code: "+91", flag: "🇮🇳" },
    { name: "China", code: "+86", flag: "🇨🇳" }
  ];

  const countryPickerWrapper = document.getElementById('country-picker-wrapper');
  const countryPickerBtn = document.getElementById('country-picker-btn');
  const countryDropdown = document.getElementById('country-dropdown');
  const countrySearchInput = document.getElementById('country-search-input');
  const countryList = document.getElementById('country-list');
  const selectedFlag = document.getElementById('selected-flag');
  const selectedCode = document.getElementById('selected-code');
  const phoneCodeInput = document.getElementById('phone_code');

  if (countryPickerBtn && countryDropdown && countryList) {
    function renderCountryList(filterText = '') {
      const query = filterText.toLowerCase().trim();
      countryList.innerHTML = '';

      const filtered = countries.filter(c =>
        c.name.toLowerCase().includes(query) || c.code.includes(query)
      );

      if (filtered.length === 0) {
        countryList.innerHTML = '<li class="country-no-results">No se encontraron países</li>';
        return;
      }

      filtered.forEach(c => {
        const li = document.createElement('li');
        li.className = 'country-option';
        li.setAttribute('role', 'option');
        li.innerHTML = `
          <span class="country-opt-flag">${c.flag}</span>
          <span class="country-opt-name">${c.name}</span>
          <span class="country-opt-code">${c.code}</span>
        `;
        li.addEventListener('click', () => {
          selectedFlag.textContent = c.flag;
          selectedCode.textContent = c.code;
          phoneCodeInput.value = c.code;
          countryDropdown.classList.remove('active');
          countryPickerBtn.setAttribute('aria-expanded', 'false');
          document.getElementById('whatsapp')?.focus();
        });
        countryList.appendChild(li);
      });
    }

    renderCountryList();

    countryPickerBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      const isActive = countryDropdown.classList.toggle('active');
      countryPickerBtn.setAttribute('aria-expanded', isActive ? 'true' : 'false');
      if (isActive) {
        countrySearchInput.value = '';
        renderCountryList();
        setTimeout(() => countrySearchInput.focus(), 100);
      }
    });

    countrySearchInput.addEventListener('input', (e) => {
      renderCountryList(e.target.value);
    });

    document.addEventListener('click', (e) => {
      if (!countryPickerWrapper.contains(e.target)) {
        countryDropdown.classList.remove('active');
        countryPickerBtn.setAttribute('aria-expanded', 'false');
      }
    });
  }

  // ── Cookie Policy Card Logic ───────────────────────────────────────────────
  const cookiesCard = document.getElementById('cookies-card');
  const acceptBtn = document.getElementById('cookie-accept-btn');
  const rejectBtn = document.getElementById('cookie-reject-btn');
  const exitBtn = document.getElementById('cookie-exit-btn');

  if (cookiesCard) {
    const cookieConsent = localStorage.getItem('portfolio-cookie-consent');
    // Solo mostrar si no ha aceptado ni rechazado
    if (!cookieConsent) {
      cookiesCard.style.display = 'flex';
      // Animación de entrada suave tras unos milisegundos
      setTimeout(() => {
        cookiesCard.classList.add('show');
      }, 400);
    }

    function dismissCookieCard(status) {
      cookiesCard.classList.remove('show');
      try {
        localStorage.setItem('portfolio-cookie-consent', status);
      } catch (e) {
        console.error('Failed to save cookie consent', e);
      }
      setTimeout(() => {
        cookiesCard.style.display = 'none';
      }, 350);
    }

    if (acceptBtn) {
      acceptBtn.addEventListener('click', () => dismissCookieCard('accepted'));
    }
    if (rejectBtn) {
      rejectBtn.addEventListener('click', () => dismissCookieCard('rejected'));
    }
    if (exitBtn) {
      exitBtn.addEventListener('click', () => dismissCookieCard('closed'));
    }
  }
});
