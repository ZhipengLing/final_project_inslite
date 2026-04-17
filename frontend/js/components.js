/* ── Toast Notifications ──────────────────────────────── */
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = "toastOut 0.3s ease forwards";
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

/* ── Loading Spinner ─────────────────────────────────── */
function showSpinner(btn) {
  const original = btn.innerHTML;
  const width = btn.offsetWidth;
  btn.style.minWidth = width + "px";
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner spinner-white"></span>';
  return function stop() {
    btn.innerHTML = original;
    btn.disabled = false;
    btn.style.minWidth = "";
  };
}

/* ── Time Ago ─────────────────────────────────────────── */
function timeAgo(timestamp) {
  const ts = typeof timestamp === "string" ? parseInt(timestamp, 10) : timestamp;
  const seconds = Math.floor((Date.now() - ts) / 1000);
  if (seconds < 5) return "just now";
  if (seconds < 60) return seconds + "s ago";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return minutes + "m ago";
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return hours + "h ago";
  const days = Math.floor(hours / 24);
  if (days < 7) return days + "d ago";
  const weeks = Math.floor(days / 7);
  return weeks + "w ago";
}

/* ── API Log Toggle ───────────────────────────────────── */
function toggleApiLog() {
  const log = document.getElementById("api-log");
  const toggle = document.getElementById("api-log-toggle");
  if (log.classList.contains("collapsed")) {
    log.classList.remove("collapsed");
    log.classList.add("expanded");
    toggle.innerHTML = "&#9660;";
  } else {
    log.classList.remove("expanded");
    log.classList.add("collapsed");
    toggle.innerHTML = "&#9650;";
  }
}

/* ── Avatar Helper ────────────────────────────────────── */
function avatarHTML(username, url, size = "") {
  const cls = "avatar" + (size ? " avatar-" + size : "");
  if (url) {
    return `<div class="${cls}"><img src="${url}" alt="${username}"></div>`;
  }
  return `<div class="${cls}">${(username || "?")[0].toUpperCase()}</div>`;
}

/* ── Navbar ───────────────────────────────────────────── */
let notifPollTimer = null;

function renderNavbar() {
  const nav = document.getElementById("navbar");
  if (!isLoggedIn()) {
    nav.innerHTML = `
      <div class="nav-inner">
        <a href="#login" class="nav-logo">InstaLite</a>
        <div class="nav-links">
          <a href="#login">Log In</a>
        </div>
      </div>`;
    if (notifPollTimer) { clearInterval(notifPollTimer); notifPollTimer = null; }
    return;
  }

  const user = getCurrentUser();
  nav.innerHTML = `
    <div class="nav-inner">
      <a href="#feed" class="nav-logo" onclick="forceNavigate('feed')">InstaLite</a>
      <div class="nav-links">
        <a href="#feed" title="Home" onclick="forceNavigate('feed')">&#x1F3E0;</a>
        <a href="#search" title="Search" onclick="forceNavigate('search')">&#x1F50D;</a>
        <a href="#new" title="New Post" onclick="forceNavigate('new')">&#x2795;</a>
        <a href="#notifications" title="Notifications" id="nav-notif" onclick="forceNavigate('notifications')">
          &#x1F514;<span id="notif-badge" class="notif-badge" style="display:none">0</span>
        </a>
        <a href="#profile/${user.userId}" title="Profile" onclick="forceNavigate('profile/${user.userId}')">&#x1F464;</a>
        <a href="#" onclick="logout(); return false;" title="Logout">&#x2716;</a>
      </div>
    </div>`;

  pollNotifCount();
  if (notifPollTimer) clearInterval(notifPollTimer);
  notifPollTimer = setInterval(pollNotifCount, 10000);
}

/* Force re-navigate even if hash is the same */
function forceNavigate(page) {
  event.preventDefault();
  if (location.hash === "#" + page) {
    navigate();
  } else {
    location.hash = "#" + page;
  }
}

async function pollNotifCount() {
  try {
    const data = await api.get("/notifications", true);
    const badge = document.getElementById("notif-badge");
    if (badge && data.unreadCount > 0) {
      badge.textContent = data.unreadCount > 99 ? "99+" : data.unreadCount;
      badge.style.display = "flex";
    } else if (badge) {
      badge.style.display = "none";
    }
  } catch (e) { /* silent */ }
}

/* ── Auth Helpers ─────────────────────────────────────── */
function isLoggedIn() {
  return !!localStorage.getItem(CONFIG.TOKEN_KEY);
}

function getCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem(CONFIG.USER_KEY)) || {};
  } catch { return {}; }
}

function saveAuth(token, user) {
  localStorage.setItem(CONFIG.TOKEN_KEY, token);
  localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(user));
}

function logout() {
  localStorage.removeItem(CONFIG.TOKEN_KEY);
  localStorage.removeItem(CONFIG.USER_KEY);
  if (notifPollTimer) { clearInterval(notifPollTimer); notifPollTimer = null; }
  location.hash = "#login";
}

/* ── Post Card Renderer ───────────────────────────────── */
function renderPostCard(post) {
  const liked = post._liked ? "liked" : "";
  const heartIcon = post._liked ? "\u2764\uFE0F" : "\u2661";
  const currentUser = getCurrentUser();
  const isOwner = currentUser.userId === post.userId;
  const deleteBtn = isOwner
    ? `<button onclick="deletePost('${post.postId}')" title="Delete" style="margin-left:auto;color:var(--danger,#e74c3c);background:none;border:none;cursor:pointer;font-size:18px;">🗑️</button>`
    : "";
  return `
    <div class="post-card" id="post-${post.postId}">
      <div class="post-header">
        <a href="#profile/${post.userId}">
          ${avatarHTML(post.username, null)}
          ${post.username}
        </a>
        ${deleteBtn}
      </div>
      ${post.imageUrl ? `<img class="post-image" src="${post.imageUrl}" alt="Post image">` : ""}
      <div class="post-actions">
        <button class="${liked}" onclick="toggleLike('${post.postId}', this)" title="Like">${heartIcon}</button>
        <a href="#post/${post.postId}" style="color:var(--text);font-size:24px" title="Comments">&#x1F4AC;</a>
      </div>
      <div class="post-stats">${post.likeCount || 0} likes &middot; ${post.commentCount || 0} comments</div>
      <div class="post-caption"><strong>${post.username}</strong> ${post.caption || ""}</div>
      <div class="post-time">${timeAgo(post.createdAt)}</div>
    </div>`;
}

async function toggleLike(postId, btn) {
  const isLiked = btn.classList.contains("liked");
  try {
    if (isLiked) {
      await api.del(`/posts/${postId}/like`);
      btn.classList.remove("liked");
      btn.textContent = "\u2661";
    } else {
      await api.post(`/posts/${postId}/like`);
      btn.classList.add("liked");
      btn.textContent = "\u2764\uFE0F";
    }
    const card = document.getElementById(`post-${postId}`);
    if (card) {
      const stats = card.querySelector(".post-stats");
      const current = parseInt(stats.textContent) || 0;
      const newCount = isLiked ? Math.max(0, current - 1) : current + 1;
      const commentMatch = stats.textContent.match(/(\d+)\s*comments/);
      const commentCount = commentMatch ? commentMatch[1] : "0";
      stats.textContent = `${newCount} likes \u00B7 ${commentCount} comments`;
    }
  } catch (e) { /* toast already shown by api */ }
}

async function deletePost(postId) {
  if (!confirm("Delete this post?")) return;
  try {
    await api.del(`/posts/${postId}`);
    const card = document.getElementById(`post-${postId}`);
    if (card) card.remove();
    showToast("Post deleted", "success");
  } catch (e) { /* toast already shown by api */ }
}