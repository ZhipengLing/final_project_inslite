/* ── Feed Page ────────────────────────────────────────── */
async function renderFeed() {
  const app = document.getElementById("app");
  app.innerHTML = '<div style="text-align:center;padding:40px"><span class="spinner"></span></div>';

  try {
    const data = await api.get("/feed", true);
    const posts = data.posts || [];

    if (posts.length === 0) {
      app.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">&#x1F4F7;</div>
          <div class="empty-state-text">${data.message || "No posts yet. Follow someone or create a post!"}</div>
          <br>
          <a href="#new" class="btn btn-primary">Create Post</a>
        </div>`;
      return;
    }

    const user = getCurrentUser();
    const likedSet = new Set();
    try {
      const likePromises = posts.map(post =>
        api.get(`/posts/${post.postId}/likes`, true).catch(() => ({ likes: [] }))
      );
      const allLikes = await Promise.all(likePromises);
      for (let i = 0; i < posts.length; i++) {
        if ((allLikes[i].likes || []).some(l => l.userId === user.userId)) {
          likedSet.add(posts[i].postId);
        }
      }
    } catch (e) { /* best effort */ }

    let html = "";
    for (const post of posts) {
      post._liked = likedSet.has(post.postId);
      html += renderPostCard(post);
    }
    app.innerHTML = html;
  } catch (err) {
    app.innerHTML = '<div class="empty-state"><div class="empty-state-text">Failed to load feed.</div></div>';
  }
}
