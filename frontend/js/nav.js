// frontend/js/nav.js
(function () {
  'use strict';

  const NAV_HTML = `
    <nav id="site-navbar">
      <hr>
      <div class="navbar">
        <a href="/" title="Inicio" class="nav-link" data-path="/">INICIO</a>

        <div class="navhidden">
          <a href="/identificacion.html" title="Identificación" class="nav-link" data-path="/identificacion.html">IDENTIFICACIÓN</a>
          <a href="/descargas.html" title="Recursos" class="nav-link" data-path="/descargas.html">RECURSOS</a>
          <a href="/contacto.html" title="Contacto" class="nav-link" data-path="/contacto.html">CONTACTO</a>
        </div>

        <div class="menu">
          <button class="menubtn" aria-haspopup="true" aria-expanded="false" type="button">
            MENÚ <i class="fa fa-caret-down"></i>
          </button>
          <div class="menu-content" role="menu">
            <a href="/identificacion.html" role="menuitem">IDENTIFICACIÓN</a>
            <a href="/descargas.html" role="menuitem">RECURSOS</a>
            <a href="/contacto.html" role="menuitem">CONTACTO</a>
            <a href="/accounts/login/" role="menuitem" id="nav-login-link" class="nav-link">LOGIN</a>
          </div>
        </div>

        <div class="nav-right">
          <a href="/accounts/login/" id="nav-login-inline" class="nav-link" title="Login">LOGIN</a>
        </div>
      </div>
    </nav>
  `;

  function markActiveLink() {
    const path = location.pathname.replace(/\/+$/, '') || '/';
    const links = document.querySelectorAll('#site-navbar .nav-link');
    links.forEach(a => {
      const p = (a.getAttribute('data-path') || a.getAttribute('href') || '').replace(/\/+$/, '') || '/';
      if (p === path) a.classList.add('active');
      else a.classList.remove('active');
    });
  }

  function setupMenuToggle() {
    const menubtn = document.querySelector('#site-navbar .menubtn');
    const menucontent = document.querySelector('#site-navbar .menu-content');
    if (!menubtn || !menucontent) return;

    menubtn.addEventListener('click', () => {
      const expanded = menubtn.getAttribute('aria-expanded') === 'true';
      menubtn.setAttribute('aria-expanded', String(!expanded));
      menucontent.style.display = expanded ? 'none' : 'block';
    });

    document.addEventListener('click', (ev) => {
      if (!menubtn.contains(ev.target) && !menucontent.contains(ev.target)) {
        menucontent.style.display = 'none';
        menubtn.setAttribute('aria-expanded', 'false');
      }
    });

    menubtn.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        menucontent.style.display = 'none';
        menubtn.setAttribute('aria-expanded', 'false');
        menubtn.focus();
      }
    });
  }

  function currentNextParam() {
    const here = window.location.pathname + window.location.search;
    return encodeURIComponent(here);
  }

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
  }

  async function fetchMe() {
    const resp = await fetch('/api/me', {
      method: 'GET',
      credentials: 'include',
      cache: 'no-store',
      headers: { 'Accept': 'application/json' },
    });
    if (!resp.ok) return { authenticated: false };
    return resp.json();
  }

  async function doLogout() {
    const csrf = getCookie('csrftoken');

    const resp = await fetch('/accounts/logout/', {
      method: 'POST',
      credentials: 'include',
      cache: 'no-store',
      headers: {
        'X-CSRFToken': csrf || '',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
      },
      body: 'next=/',
    });

    if (!resp.ok) {
      const txt = await resp.text().catch(() => '');
      throw new Error(`Logout failed: ${resp.status} ${txt}`);
    }
  }

  function setLoginLinks() {
    const loginMenu = document.getElementById('nav-login-link');
    const loginInline = document.getElementById('nav-login-inline');
    const next = currentNextParam();

    const apply = (a) => {
      if (!a) return;
      a.textContent = 'LOGIN';
      a.href = `/accounts/login/?next=${next}`;
      a.removeAttribute('data-action');
    };

    apply(loginMenu);
    apply(loginInline);
  }

  function setLogoutLinks() {
    const loginMenu = document.getElementById('nav-login-link');
    const loginInline = document.getElementById('nav-login-inline');

    const apply = (a) => {
      if (!a) return;
      a.textContent = 'LOGOUT';
      a.href = '/accounts/logout/'; // aunque se intercepte
      a.dataset.action = 'logout';
    };

    apply(loginMenu);
    apply(loginInline);
  }

  async function updateAuthLinks(forceLoggedOut = false) {
    if (forceLoggedOut) {
      setLoginLinks();
      return;
    }

    try {
      const data = await fetchMe();

      // Si /api/me usa otra clave, cambiar esta línea:
      // const loggedIn = !!data.logged_in;
      const loggedIn = !!data.authenticated;

      if (loggedIn) setLogoutLinks();
      else setLoginLinks();
    } catch {
      setLoginLinks();
    }
  }

  function normalizeHashHome() {
    if (window.location.pathname === '/' && window.location.hash) {
      history.replaceState(null, '', '/');
    }
  }

  function wireLogoutClick() {
    document.addEventListener('click', async (e) => {
      const a = e.target.closest('a');
      if (!a) return;

      if (a.dataset.action === 'logout') {
        e.preventDefault();

        // 1) Pintar LOGIN inmediatamente (evita parpadeo)
        await updateAuthLinks(true);

        // 2) Hacer logout real
        try {
          await doLogout();
        } catch (err) {
          console.warn(err);
          // si falla CSRF, se ve consola
        }

        // 3) Revalidar contra backend
        await updateAuthLinks(false);

        // 4) Redirigir a home (sin #)
        window.location.assign('/');
      }
    });
  }

  function insertNavbar() {
    const placeholder = document.getElementById('site-navbar-placeholder');

    if (placeholder) {
      placeholder.insertAdjacentHTML('afterend', NAV_HTML);
      placeholder.remove();
    } else {
      const header = document.querySelector('header');
      if (header && header.parentNode) header.insertAdjacentHTML('afterend', NAV_HTML);
      else document.body.insertAdjacentHTML('afterbegin', NAV_HTML);
    }

    markActiveLink();
    setupMenuToggle();
    wireLogoutClick();
    normalizeHashHome();
    updateAuthLinks(); // decide LOGIN/LOGOUT según sesión
  }

  document.addEventListener('DOMContentLoaded', insertNavbar);
})();