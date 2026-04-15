/* ── Auth Page ────────────────────────────────────────── */
function renderLogin() {
  const app = document.getElementById("app");
  app.innerHTML = `
    <div class="auth-container">
      <div class="auth-card">
        <div class="auth-logo">InstaLite</div>
        <p style="color:var(--text-secondary);font-size:14px;margin-bottom:20px">
          Share photos with friends
        </p>

        <div id="auth-form"></div>

        <div class="auth-divider">OR</div>

        <div class="quick-login">
          <div class="quick-login-title">Quick Demo Login</div>
          <div class="quick-login-buttons">
            <button class="btn btn-secondary" onclick="quickLogin('alice')">Alice</button>
            <button class="btn btn-secondary" onclick="quickLogin('bob')">Bob</button>
          </div>
        </div>
      </div>

      <div class="auth-toggle" id="auth-toggle"></div>
    </div>`;

  showLoginForm();
}

function showLoginForm() {
  document.getElementById("auth-form").innerHTML = `
    <form onsubmit="handleLogin(event)">
      <div class="form-group">
        <input type="text" id="login-username" placeholder="Username" required>
      </div>
      <div class="form-group">
        <input type="password" id="login-password" placeholder="Password" required>
      </div>
      <button type="submit" class="btn btn-primary" style="width:100%" id="login-btn">Log In</button>
    </form>`;
  document.getElementById("auth-toggle").innerHTML =
    'Don\'t have an account? <a onclick="showSignupForm()">Sign up</a>';
}

function showSignupForm() {
  document.getElementById("auth-form").innerHTML = `
    <form onsubmit="handleSignup(event)">
      <div class="form-group">
        <input type="email" id="signup-email" placeholder="Email" required>
      </div>
      <div class="form-group">
        <input type="text" id="signup-username" placeholder="Username" required>
      </div>
      <div class="form-group">
        <input type="password" id="signup-password" placeholder="Password (6+ chars)" required minlength="6">
      </div>
      <button type="submit" class="btn btn-primary" style="width:100%" id="signup-btn">Sign Up</button>
    </form>`;
  document.getElementById("auth-toggle").innerHTML =
    'Have an account? <a onclick="showLoginForm()">Log in</a>';
}

async function handleLogin(e) {
  e.preventDefault();
  const btn = document.getElementById("login-btn");
  const stop = showSpinner(btn);
  try {
    const data = await api.post("/auth/login", {
      username: document.getElementById("login-username").value,
      password: document.getElementById("login-password").value,
    });
    saveAuth(data.token, data.user);
    location.hash = "#feed";
  } catch (err) { /* toast shown by api */ }
  finally { stop(); }
}

async function handleSignup(e) {
  e.preventDefault();
  const btn = document.getElementById("signup-btn");
  const stop = showSpinner(btn);
  try {
    const data = await api.post("/auth/signup", {
      email: document.getElementById("signup-email").value,
      username: document.getElementById("signup-username").value,
      password: document.getElementById("signup-password").value,
    });
    saveAuth(data.token, data.user);
    location.hash = "#feed";
  } catch (err) { /* toast shown by api */ }
  finally { stop(); }
}

async function quickLogin(username) {
  try {
    const data = await api.post("/auth/login", { username, password: "password123" });
    saveAuth(data.token, data.user);
    location.hash = "#feed";
  } catch (err) {
    try {
      const data = await api.post("/auth/signup", {
        email: `${username}@demo.com`,
        username,
        password: "password123",
      });
      saveAuth(data.token, data.user);
      location.hash = "#feed";
    } catch (err2) { /* toast shown */ }
  }
}
