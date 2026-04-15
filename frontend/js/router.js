/* ── Hash-based SPA Router ────────────────────────────── */
const routes = {
  login:         renderLogin,
  feed:          renderFeed,
  new:           renderNewPost,
  post:          renderPostDetail,
  profile:       renderProfile,
  notifications: renderNotifications,
};

const publicPages = ["login"];

function navigate() {
  const hash = location.hash.slice(1) || (isLoggedIn() ? "feed" : "login");
  const [page, ...params] = hash.split("/");
  const handler = routes[page];

  if (!handler) {
    location.hash = "#feed";
    return;
  }

  if (!publicPages.includes(page) && !isLoggedIn()) {
    location.hash = "#login";
    return;
  }

  if (page === "login" && isLoggedIn()) {
    location.hash = "#feed";
    return;
  }

  renderNavbar();
  const app = document.getElementById("app");
  app.innerHTML = "";
  handler(...params);
}

window.addEventListener("hashchange", navigate);
window.addEventListener("DOMContentLoaded", navigate);
