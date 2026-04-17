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
  } finally { stop(); }
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
    const topLevel = comments.filter(c => !c.parentCommentId);
    const replies = comments.filter(c => c.parentCommentId);

    function renderComment(c, isReply = false) {
      const replyBtn = !isReply
        ? `<button onclick="showReplyInput('${postId}', '${c.commentId}', '${c.username}')"
            style="background:none;border:none;color:var(--text-secondary);font-size:11px;cursor:pointer;margin-left:8px">
            Reply
          </button>`
        : "";
      const commentReplies = replies.filter(r => r.parentCommentId === c.commentId);
      const repliesHTML = commentReplies.map(r => renderComment(r, true)).join("");
      return `
        <div class="comment-item" style="${isReply ? "margin-left:24px;border-left:2px solid var(--border);padding-left:8px" : ""}">
          <strong><a href="#profile/${c.userId}" style="color:var(--text)">${c.username}</a></strong>
          ${c.text}
          <span style="color:var(--text-secondary);font-size:11px;margin-left:8px">${timeAgo(c.createdAt)}</span>
          ${replyBtn}
          <div id="reply-input-${c.commentId}"></div>
          ${repliesHTML}
        </div>`;
    }

    const commentsHTML = topLevel.map(c => renderComment(c)).join("");

    app.innerHTML = `
      ${renderPostCard(post)}
      <div class="card">
        <div style="padding:12px 16px;font-weight:600;font-size:14px">
          Comments (${topLevel.length})
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

function showReplyInput(postId, parentCommentId, parentUsername) {
  const container = document.getElementById(`reply-input-${parentCommentId}`);
  if (container.innerHTML) { container.innerHTML = ""; return; }
  container.innerHTML = `
    <div style="display:flex;gap:8px;margin-top:6px">
      <input type="text" id="reply-text-${parentCommentId}" placeholder="Reply to ${parentUsername}..."
        style="flex:1;padding:6px 10px;border:1px solid var(--border);border-radius:16px;font-size:13px"
        onkeypress="if(event.key==='Enter')submitReply('${postId}', '${parentCommentId}')">
      <button onclick="submitReply('${postId}', '${parentCommentId}')"
        style="padding:6px 12px;background:var(--primary);color:#fff;border:none;border-radius:16px;cursor:pointer;font-size:13px">
        Reply
      </button>
    </div>`;
  document.getElementById(`reply-text-${parentCommentId}`).focus();
}

async function submitReply(postId, parentCommentId) {
  const input = document.getElementById(`reply-text-${parentCommentId}`);
  const text = input.value.trim();
  if (!text) return;

  try {
    const comment = await api.post(`/posts/${postId}/comments`, { text, parentCommentId });
    const user = getCurrentUser();
    const container = document.getElementById(`reply-input-${parentCommentId}`);
    const replyDiv = document.createElement("div");
    replyDiv.className = "comment-item";
    replyDiv.style = "margin-left:24px;border-left:2px solid var(--border);padding-left:8px";
    replyDiv.innerHTML = `<strong>${user.username}</strong> ${text}
      <span style="color:var(--text-secondary);font-size:11px;margin-left:8px">just now</span>`;
    container.parentElement.appendChild(replyDiv);
    container.innerHTML = "";
  } catch (err) { /* toast shown */ }
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