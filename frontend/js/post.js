/* ── Create Post Page ─────────────────────────────────── */
let selectedFile = null;

function renderNewPost() {
  selectedFile = null;
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="card" style="padding:20px">
      <h2 style="margin-bottom:16px;font-size:18px">Create New Post</h2>

      <div class="upload-area" id="upload-area" onclick="document.getElementById('file-input').click()">
        <div class="upload-icon">&#x1F4F7;</div>
        <div class="upload-text">Click to select a photo</div>
      </div>
      <input type="file" id="file-input" accept="image/*" style="display:none" onchange="handleFileSelect(event)">

      <div class="form-group">
        <label>Caption</label>
        <textarea id="post-caption" placeholder="Write a caption..." rows="3"></textarea>
      </div>

      <button class="btn btn-primary" style="width:100%" id="create-post-btn" onclick="handleCreatePost()" disabled>
        Share Post
      </button>
    </div>`;
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;
  selectedFile = file;

  const reader = new FileReader();
  reader.onload = function(ev) {
    const area = document.getElementById("upload-area");
    area.classList.add("has-preview");
    area.innerHTML = `<img class="upload-preview" src="${ev.target.result}" alt="Preview">`;
    document.getElementById("create-post-btn").disabled = false;
  };
  reader.readAsDataURL(file);
}

async function handleCreatePost() {
  if (!selectedFile) return;

  const btn = document.getElementById("create-post-btn");
  const stop = showSpinner(btn);

  try {
    const presignData = await api.post("/media/presign", {
      contentType: selectedFile.type || "image/jpeg",
      filename: selectedFile.name,
    });

    showToast("Uploading image to S3...", "info");
    await uploadToS3(presignData.uploadUrl, selectedFile, selectedFile.type || "image/jpeg");
    showToast("Image uploaded to S3", "success");

    const caption = document.getElementById("post-caption").value;
    await api.post("/posts", {
      imageUrl: presignData.imageUrl,
      caption: caption,
    });

    selectedFile = null;
    location.hash = "#feed";
  } catch (err) {
    console.error("Create post error:", err);
    if (!err.status && !err.message?.includes("S3")) {
      showToast("Failed to create post: " + (err.message || "Unknown error"), "error");
    }
  }
  finally { stop(); }
}

/* ── Post Detail Page ─────────────────────────────────── */
async function renderPostDetail(postId) {
  const app = document.getElementById("app");
  app.innerHTML = '<div style="text-align:center;padding:40px"><span class="spinner"></span></div>';

  try {
    const post = await api.get(`/posts/${postId}`, true);
    const commentsData = await api.get(`/posts/${postId}/comments`, true);
    const likesData = await api.get(`/posts/${postId}/likes`, true);

    const user = getCurrentUser();
    const isLiked = (likesData.likes || []).some(l => l.userId === user.userId);
    post._liked = isLiked;

    const comments = commentsData.comments || [];
    let commentsHTML = comments.map(c => `
      <div class="comment-item">
        <strong><a href="#profile/${c.userId}" style="color:var(--text)">${c.username}</a></strong>
        ${c.text}
        <span style="color:var(--text-secondary);font-size:11px;margin-left:8px">${timeAgo(c.createdAt)}</span>
      </div>`).join("");

    app.innerHTML = `
      ${renderPostCard(post)}
      <div class="card">
        <div style="padding:12px 16px;font-weight:600;font-size:14px">
          Comments (${comments.length})
        </div>
        <div id="comments-list" style="padding:0 16px;max-height:400px;overflow-y:auto">
          ${commentsHTML || '<div style="color:var(--text-secondary);font-size:14px;padding:8px 0">No comments yet</div>'}
        </div>
        <div class="comment-input">
          <input type="text" id="comment-text" placeholder="Add a comment..." onkeypress="if(event.key==='Enter')submitComment('${postId}')">
          <button onclick="submitComment('${postId}')" id="comment-btn">Post</button>
        </div>
      </div>`;
  } catch (err) {
    app.innerHTML = '<div class="empty-state"><div class="empty-state-text">Post not found.</div></div>';
  }
}

async function submitComment(postId) {
  const input = document.getElementById("comment-text");
  const text = input.value.trim();
  if (!text) return;

  const btn = document.getElementById("comment-btn");
  btn.disabled = true;

  try {
    const comment = await api.post(`/posts/${postId}/comments`, { text });
    input.value = "";

    const list = document.getElementById("comments-list");
    const noComments = list.querySelector("div[style]");
    if (noComments && noComments.textContent.includes("No comments")) noComments.remove();

    const user = getCurrentUser();
    const div = document.createElement("div");
    div.className = "comment-item";
    div.innerHTML = `<strong>${user.username || comment.username}</strong> ${text}
      <span style="color:var(--text-secondary);font-size:11px;margin-left:8px">just now</span>`;
    list.appendChild(div);
  } catch (err) { /* toast shown */ }
  finally { btn.disabled = false; }
}
