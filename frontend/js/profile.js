/* ── Profile Page ─────────────────────────────────────── */
async function renderProfile(userId) {
  const app = document.getElementById("app");
  app.innerHTML = '<div style="text-align:center;padding:40px"><span class="spinner"></span></div>';

  try {
    const user = await api.get(`/users/${userId}`, true);
    const postsData = await api.get(`/users/${userId}/posts`, true);
    const posts = postsData.posts || [];

    const currentUser = getCurrentUser();
    const isOwn = currentUser.userId === userId;

    let followBtnHTML = "";
    let isFollowing = false;
    if (!isOwn) {
      try {
        const followingData = await api.get(`/users/${currentUser.userId}/following`, true);
        isFollowing = (followingData.following || []).some(f => f.followeeId === userId);
      } catch (e) { /* ignore */ }
      followBtnHTML = isFollowing
        ? `<button class="btn btn-secondary btn-follow" id="follow-btn" onclick="handleUnfollow('${userId}')">Following</button>`
        : `<button class="btn btn-primary btn-follow" id="follow-btn" onclick="handleFollow('${userId}')">Follow</button>`;
    }

    let gridHTML = "";
    if (posts.length > 0) {
      gridHTML = '<div class="posts-grid">' +
        posts.map(p => `<a href="#post/${p.postId}"><img src="${p.imageUrl}" alt="Post" onerror="this.parentElement.style.background='var(--border)'"></a>`).join("") +
        "</div>";
    } else {
      gridHTML = '<div class="empty-state" style="padding:40px 0"><div class="empty-state-icon">&#x1F4F7;</div><div class="empty-state-text">No posts yet</div></div>';
    }

    app.innerHTML = `
      <div class="profile-header">
        ${avatarHTML(user.username, user.avatarUrl, "lg")}
        <div class="profile-info">
          <div class="profile-username">
            ${user.username}
            ${followBtnHTML}
          </div>
          <div class="profile-stats">
            <span><strong id="post-count">${user.postCount || 0}</strong> posts</span>
            <span><strong id="follower-count">${user.followerCount || 0}</strong> followers</span>
            <span><strong id="following-count">${user.followingCount || 0}</strong> following</span>
          </div>
          <div class="profile-bio">
            <div class="profile-displayname">${user.displayName || user.username}</div>
            ${user.bio ? `<div>${user.bio}</div>` : ""}
          </div>
        </div>
      </div>
      ${gridHTML}`;
  } catch (err) {
    app.innerHTML = '<div class="empty-state"><div class="empty-state-text">User not found.</div></div>';
  }
}

async function handleFollow(userId) {
  const btn = document.getElementById("follow-btn");
  const stop = showSpinner(btn);
  try {
    await api.post(`/users/${userId}/follow`);
    btn.className = "btn btn-secondary btn-follow";
    btn.textContent = "Following";
    btn.setAttribute("onclick", `handleUnfollow('${userId}')`);
    const el = document.getElementById("follower-count");
    if (el) el.textContent = parseInt(el.textContent) + 1;
  } catch (e) { /* toast shown */ }
  finally { stop(); }
}

async function handleUnfollow(userId) {
  const btn = document.getElementById("follow-btn");
  const stop = showSpinner(btn);
  try {
    await api.del(`/users/${userId}/follow`);
    btn.className = "btn btn-primary btn-follow";
    btn.textContent = "Follow";
    btn.setAttribute("onclick", `handleFollow('${userId}')`);
    const el = document.getElementById("follower-count");
    if (el) el.textContent = Math.max(0, parseInt(el.textContent) - 1);
  } catch (e) { /* toast shown */ }
  finally { stop(); }
}
