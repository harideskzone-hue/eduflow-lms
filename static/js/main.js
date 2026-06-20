/**
 * EduFlow LMS — Shared JavaScript
 * Handles: notification dropdown, flash messages, mobile nav, tabs
 */

// ── Notification Dropdown ───────────────────────────────────────
function toggleNotifications(e) {
  e.stopPropagation();
  const menu = document.getElementById('notification-menu');
  const btn  = document.getElementById('notification-btn');
  if (!menu) return;
  const isOpen = menu.classList.toggle('open');
  btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
}

// ── Mobile Nav Drawer ───────────────────────────────────────────
function openNavDrawer() {
  const drawer  = document.getElementById('nav-drawer');
  const overlay = document.getElementById('nav-overlay');
  const btn     = document.getElementById('mobile-nav-btn');
  if (!drawer) return;
  drawer.classList.add('open');
  overlay.classList.add('open');
  btn.classList.add('open');
  btn.setAttribute('aria-expanded', 'true');
  document.body.style.overflow = 'hidden';
}
function closeNavDrawer() {
  const drawer  = document.getElementById('nav-drawer');
  const overlay = document.getElementById('nav-overlay');
  const btn     = document.getElementById('mobile-nav-btn');
  if (!drawer) return;
  drawer.classList.remove('open');
  overlay.classList.remove('open');
  btn.classList.remove('open');
  btn.setAttribute('aria-expanded', 'false');
  document.body.style.overflow = '';
}

// ── Tab System ──────────────────────────────────────────────────
function switchTab(tabId) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => {
    b.classList.remove('active');
    b.setAttribute('aria-selected', 'false');
  });
  const panel = document.getElementById('tab-' + tabId);
  const btn   = document.getElementById('btn-' + tabId);
  if (panel) panel.classList.add('active');
  if (btn)   { btn.classList.add('active'); btn.setAttribute('aria-selected', 'true'); }
}

// ── Flash / Toast Dismiss ───────────────────────────────────────
function dismissFlash(btn) {
  const flash = btn.closest('.flash');
  flash.classList.add('hiding');
  setTimeout(() => flash.remove(), 320);
}

function autoDismissFlash() {
  document.querySelectorAll('.flash').forEach((el, i) => {
    setTimeout(() => {
      el.classList.add('hiding');
      setTimeout(() => el.remove(), 320);
    }, 4000 + i * 300);
  });
}

// ── Close dropdown on outside click ────────────────────────────
document.addEventListener('click', () => {
  const menu = document.getElementById('notification-menu');
  const btn  = document.getElementById('notification-btn');
  if (menu && menu.classList.contains('open')) {
    menu.classList.remove('open');
    if (btn) btn.setAttribute('aria-expanded', 'false');
  }
});

// Prevent drawer overlay click from bubbling
document.addEventListener('DOMContentLoaded', () => {
  autoDismissFlash();

  const overlay = document.getElementById('nav-overlay');
  if (overlay) overlay.addEventListener('click', closeNavDrawer);

  // Escape key closes dropdown and drawer
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeNavDrawer();
      const menu = document.getElementById('notification-menu');
      if (menu) menu.classList.remove('open');
    }
  });
});
