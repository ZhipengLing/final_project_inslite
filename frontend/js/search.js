async function renderSearch() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="card" style="padding:20px">
      <h2 style="margin-bottom:16px;font-size:18px">Search Users</h2>
      <div style="display:flex;gap:8px;margin-bottom:16px">
        <input type="text" id="search-input" placeholder="Search by username..."
          style="flex:1;padding:10px 14px;border:1px solid var(--border);border-radius:20px;font-size:14px"
          onkeypress="if(event.key==='Enter')doSearch()">
        <button onclick="doSearch()" class="btn btn-primary" id="search-btn">Search</button>
      </div>
      <div id="search-results"></div>
    </div>`;
  document.getElementById("search-input").focus();
}

async function doSearch() {
  const input = document.getElementById("search-input");
  const q = input.value.trim();
  if (!q) return;

  const btn = document.getElementById("search-btn");
  const stop = showSpinner(btn);
  const results = document.getElementById("search-results");
  results.innerHTML = "";

  try {
    const data = await api.get(`/search/users?q=${encodeURIComponent(q)}`, true);
    const users = data.users || [];
    const currentUser = getCurrentUser();

    if (users.length === 0) {
      results.innerHTML = '<div style="color:var(--text-secondary);text-align:center;padding:20px">No users found</div>';
      return;
    }

    results.innerHTML = users.map(u => `
      <div class="card" style="display:flex;align-items:center;gap:12px;padding:12px;margin-bottom:8px">
        <a href="#profile/${u.userId}" style="display:flex;align-items:center;gap:12px;flex:1;text-decoration:none;color:var(--text)">
          ${avatarHTML(u.username, u.avatarUrl)}
          <div>
            <div style="font-weight:600">${u.username}</div>
            <div style="font-size:12px;color:var(--text-secondary)">${u.followerCount || 0} followers</div>
          </div>
        </a>
        ${u.userId !== currentUser.userId
          ? `<button id="follow-btn-${u.userId}" onclick="toggleFollowFromSearch('${u.userId}', this)"
              class="btn btn-primary" style="padding:6px 16px;font-size:13px">
              Follow
            </button>`
          : ""}
      </div>`).join("");
  } catch (err) {
    results.innerHTML = '<div style="color:var(--text-secondary);text-align:center;padding:20px">Search failed</div>';
  } finally { stop(); }
}

async function toggleFollowFromSearch(userId, btn) {
  const isFollowing = btn.textContent.trim() === "Following";
  try {
    if (isFollowing) {
      await api.del(`/users/${userId}/follow`);
      btn.textContent = "Follow";
      btn.classList.remove("btn-secondary");
      btn.classList.add("btn-primary");
    } else {
      await api.post(`/users/${userId}/follow`);
      btn.textContent = "Following";
      btn.classList.remove("btn-primary");
      btn.classList.add("btn-secondary");
    }
  } catch (err) { /* toast shown */ }
}