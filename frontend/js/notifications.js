/* ── Notifications Page ───────────────────────────────── */
async function renderNotifications() {
  const app = document.getElementById("app");
  app.innerHTML = '<div style="text-align:center;padding:40px"><span class="spinner"></span></div>';

  try {
    const data = await api.get("/notifications", true);
    const notifications = data.notifications || [];

    if (notifications.length === 0) {
      app.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">&#x1F514;</div>
          <div class="empty-state-text">No notifications yet</div>
        </div>`;
      return;
    }

    const typeIcons = { LIKE: "\u2764\uFE0F", COMMENT: "\uD83D\uDCAC", FOLLOW: "\uD83D\uDC64" };

    let html = '<div class="card">';
    html += '<div style="padding:12px 16px;font-weight:600;font-size:16px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center">Notifications <button class="btn btn-secondary" style="font-size:12px;padding:4px 12px" onclick="renderNotifications()">Refresh</button></div>';

    for (const n of notifications) {
      const icon = typeIcons[n.type] || "\uD83D\uDD14";
      const unread = !n.isRead ? "unread" : "";
      const link = n.postId ? `#post/${n.postId}` : `#profile/${n.sourceUserId}`;
      const safeNotifId = encodeURIComponent(n.notifId);

      html += `
        <div class="notif-item ${unread}" data-notifid="${safeNotifId}" data-link="${link}" onclick="handleNotifClick(this)">
          <div class="notif-icon">${icon}</div>
          <div class="notif-text">
            <a href="#profile/${n.sourceUserId}" style="font-weight:600;color:var(--text)" onclick="event.stopPropagation()">${n.sourceUsername}</a>
            ${getNotifAction(n)}
          </div>
          <div class="notif-time">${timeAgo(n.createdAt)}</div>
        </div>`;
    }
    html += "</div>";
    app.innerHTML = html;
  } catch (err) {
    app.innerHTML = '<div class="empty-state"><div class="empty-state-text">Failed to load notifications.</div></div>';
  }
}

function getNotifAction(n) {
  switch (n.type) {
    case "LIKE": return "liked your post";
    case "COMMENT": return "commented on your post";
    case "FOLLOW": return "started following you";
    default: return n.message || "";
  }
}

async function handleNotifClick(el) {
  const notifId = el.dataset.notifid;
  const link = el.dataset.link;
  if (el.classList.contains("unread")) {
    el.classList.remove("unread");
    try { await api.put(`/notifications/${notifId}/read`, {}, true); } catch (e) { /* silent */ }
  }
  location.hash = link;
}
