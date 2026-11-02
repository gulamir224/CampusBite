document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.querySelector('.main-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', String(open));
      toggle.textContent = open ? '×' : '☰';
    });
  }

  document.querySelectorAll('.toast-close').forEach((button) => {
    button.addEventListener('click', () => button.closest('.toast')?.remove());
  });
  document.querySelectorAll('.toast').forEach((toast) => {
    window.setTimeout(() => {
      toast.classList.add('toast-leave');
      window.setTimeout(() => toast.remove(), 300);
    }, 5200);
  });

  document.querySelectorAll('img.food-image, img.cart-image').forEach((image) => {
    image.addEventListener('error', () => {
      const label = (image.alt || 'CampusBite').replace(/[<>&]/g, '').slice(0, 20);
      const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 400"><rect width="600" height="400" fill="#fff0e6"/><circle cx="300" cy="177" r="82" fill="#f7d9c5"/><text x="300" y="202" text-anchor="middle" font-size="72">🍽</text><text x="300" y="320" text-anchor="middle" fill="#8d6b57" font-family="Arial" font-size="24">${label}</text></svg>`;
      image.src = `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
    }, { once: true });
  });

  document.querySelectorAll('form[data-confirm]').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });

  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (event.defaultPrevented || form.dataset.confirm) return;
      const submit = event.submitter;
      if (submit && submit.type === 'submit' && !submit.disabled) {
        submit.dataset.originalLabel = submit.innerHTML;
        submit.disabled = true;
        submit.innerHTML = '<span class="button-spinner" aria-label="Loading"></span>';
        window.setTimeout(() => {
          if (submit.isConnected) {
            submit.disabled = false;
            submit.innerHTML = submit.dataset.originalLabel;
          }
        }, 4000);
      }
    });
  });
});
