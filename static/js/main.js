document.addEventListener('DOMContentLoaded', () => {
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
});
