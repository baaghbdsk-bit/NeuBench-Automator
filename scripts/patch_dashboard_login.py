from pathlib import Path

html_path = Path("src/web/templates/dashboard.html")
content = html_path.read_text(encoding="utf-8")

connection_card = '''
        <!-- LinkedIn Autonomous Account Connection Card -->
        <div id="linkedin-conn-card" class="card-base p-4 border border-blue-500/30 bg-gradient-to-r from-blue-500/10 via-sky-500/5 to-transparent">
          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div class="flex items-center space-x-3">
              <div class="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-lg shadow-md shadow-blue-500/25 shrink-0">
                <i class="fa-brands fa-linkedin-in"></i>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <h4 class="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">LinkedIn Account Connection</h4>
                  <span id="linkedin-status-badge" class="badge-base badge-amber text-[10px] px-2 py-0.5 rounded font-mono">Checking...</span>
                </div>
                <p id="linkedin-status-desc" class="text-[11px] text-slate-500 dark:text-xmuted mt-0.5">
                  Connect your LinkedIn session to enable 100% autonomous background posting.
                </p>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0">
              <button id="btn-linkedin-login-ui" onclick="launchLinkedInLogin()" class="btn-primary bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 text-xs font-semibold rounded-lg flex items-center gap-2 transition shadow shadow-blue-600/30">
                <i class="fa-solid fa-key"></i>
                <span id="btn-linkedin-login-text">Log in to LinkedIn (1-Click)</span>
              </button>
              <button onclick="checkAuthStatus()" class="btn-ghost text-xs p-2 rounded-lg text-slate-400 hover:text-slate-200 border border-slate-200 dark:border-xborder" title="Refresh status">
                <i class="fa-solid fa-rotate"></i>
              </button>
            </div>
          </div>
          <div id="linkedin-login-alert" class="hidden mt-3 p-3 rounded-lg bg-blue-500/15 border border-blue-500/30 text-xs text-blue-300 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <i class="fa-solid fa-spinner fa-spin text-blue-400"></i>
              <span id="linkedin-login-alert-text">Browser window opened on your desktop! Please log in with your credentials...</span>
            </div>
            <span class="text-[10px] text-blue-400/80 font-mono">Auto-detecting feed...</span>
          </div>
        </div>
'''

# 1. Insert connection card right at top of view-linkedin
target_view = '<div id="view-linkedin" class="hidden space-y-4">'
if "id=\"linkedin-conn-card\"" not in content:
    content = content.replace(target_view, target_view + "\n" + connection_card)
    print("Added LinkedIn connection card to view-linkedin.")

# 2. Upgrade the buttons row in the drafting pad
old_buttons = '''          <div class="flex items-center justify-between pt-2 border-t border-slate-200 dark:border-xborder">
            <span class="text-[11px] text-slate-500 dark:text-xmuted">Zero corporate cringe • Backed by NeuBench benchmark data</span>
            <button onclick="copyLinkedInStudioText()" id="linkedin-copy-btn" class="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-4 py-1.5 rounded-full transition flex items-center gap-1.5 shadow-sm shadow-blue-600/25 active:scale-95">
              <i class="fa-regular fa-copy"></i>
              <span>Copy LinkedIn Post</span>
            </button>
          </div>'''

new_buttons = '''          <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-2 border-t border-slate-200 dark:border-xborder">
            <span class="text-[11px] text-slate-500 dark:text-xmuted">Zero corporate cringe • Backed by NeuBench benchmark data</span>
            <div class="flex items-center gap-2">
              <button onclick="copyLinkedInStudioText()" id="linkedin-copy-btn" class="bg-slate-200 dark:bg-[#1a2233] hover:bg-slate-300 dark:hover:bg-[#222c42] text-slate-800 dark:text-white font-semibold text-xs px-3.5 py-1.5 rounded-lg transition flex items-center gap-1.5 active:scale-95">
                <i class="fa-regular fa-copy"></i>
                <span>Copy</span>
              </button>
              <button onclick="openLinkedInWebComposer()" class="bg-slate-200 dark:bg-[#1a2233] hover:bg-slate-300 dark:hover:bg-[#222c42] text-blue-600 dark:text-blue-400 font-semibold text-xs px-3.5 py-1.5 rounded-lg transition flex items-center gap-1.5 active:scale-95" title="Open native LinkedIn web composer">
                <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
                <span>Open in Web</span>
              </button>
              <button onclick="publishLinkedInAutonomous()" id="btn-linkedin-publish-autonomous" class="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-4 py-1.5 rounded-lg transition flex items-center gap-1.5 shadow-sm shadow-blue-600/25 active:scale-95">
                <i class="fa-solid fa-paper-plane text-xs"></i>
                <span id="btn-linkedin-pub-text">Publish Autonomously</span>
              </button>
            </div>
          </div>'''

if old_buttons in content:
    content = content.replace(old_buttons, new_buttons)
    print("Upgraded LinkedIn drafting buttons.")

# 3. Add JS functions
js_code = '''
    // ==========================================
    // 8. AUTONOMOUS ACCOUNT LOGIN & DISPATCH
    // ==========================================
    let _authPollInterval = null;

    async function checkAuthStatus() {
      try {
        const res = await fetch('/api/auth/status');
        const data = await res.json();
        
        // Update LinkedIn status
        const liBadge = document.getElementById('linkedin-status-badge');
        const liDesc = document.getElementById('linkedin-status-desc');
        const liBtn = document.getElementById('btn-linkedin-login-ui');
        const liBtnText = document.getElementById('btn-linkedin-login-text');
        const liAlert = document.getElementById('linkedin-login-alert');

        if (data.linkedin && data.linkedin.logged_in) {
          if (liBadge) {
            liBadge.className = 'badge-base badge-emerald text-[10px] px-2 py-0.5 rounded font-mono';
            liBadge.innerText = 'Connected & Autonomous';
          }
          if (liDesc) liDesc.innerText = 'Session active! The automater can now publish to your profile 100% autonomously.';
          if (liBtnText) liBtnText.innerText = 'Re-login / Switch Account';
          if (liAlert) liAlert.classList.add('hidden');
          if (_authPollInterval) {
            clearInterval(_authPollInterval);
            _authPollInterval = null;
          }
        } else {
          if (liBadge) {
            liBadge.className = 'badge-base badge-amber text-[10px] px-2 py-0.5 rounded font-mono';
            liBadge.innerText = 'Login Required';
          }
          if (liDesc) liDesc.innerText = 'Click the login button to open a browser window and log in once.';
          if (liBtnText) liBtnText.innerText = 'Log in to LinkedIn (1-Click)';
          
          if (data.linkedin && data.linkedin.login_process_active) {
            if (liAlert) liAlert.classList.remove('hidden');
            if (!_authPollInterval) {
              _authPollInterval = setInterval(checkAuthStatus, 3000);
            }
          }
        }
      } catch (e) {
        console.error('Failed to check auth status:', e);
      }
    }

    async function launchLinkedInLogin() {
      const btn = document.getElementById('btn-linkedin-login-ui');
      const alertBox = document.getElementById('linkedin-login-alert');
      try {
        if (alertBox) alertBox.classList.remove('hidden');
        const res = await fetch('/api/auth/launch-linkedin-login', { method: 'POST' });
        const data = await res.json();
        alert(data.message || 'Browser opened! Please log into LinkedIn in the window on your desktop.');
        
        // Start polling for login completion
        if (_authPollInterval) clearInterval(_authPollInterval);
        _authPollInterval = setInterval(checkAuthStatus, 3000);
      } catch (e) {
        alert('Failed to launch login: ' + e);
      }
    }

    function openLinkedInWebComposer() {
      const text = document.getElementById('linkedin-studio-textarea').value;
      if (!text) {
        alert('Please draft or enter a post first!');
        return;
      }
      const url = `https://www.linkedin.com/feed/?shareActive=true&text=${encodeURIComponent(text)}`;
      window.open(url, '_blank');
    }

    async function publishLinkedInAutonomous() {
      const text = document.getElementById('linkedin-studio-textarea').value;
      if (!text) {
        alert('Please draft or enter a post first!');
        return;
      }
      const btn = document.getElementById('btn-linkedin-publish-autonomous');
      const btnText = document.getElementById('btn-linkedin-pub-text');
      
      btn.disabled = true;
      btnText.innerText = 'Publishing Headless...';

      try {
        const res = await fetch('/api/action/publish-linkedin', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: text })
        });
        const data = await res.json();
        if (data.status === 'success') {
          alert('🎉 ' + data.message);
          fetchStats();
        } else if (data.status === 'not_logged_in') {
          if (confirm(data.message + '\\n\\nWould you like to open the browser window to log in now?')) {
            launchLinkedInLogin();
          }
        } else {
          alert('Note: ' + (data.message || 'Action completed'));
        }
      } catch (e) {
        alert('Publish request error: ' + e);
      } finally {
        btn.disabled = false;
        btnText.innerText = 'Publish Autonomously';
      }
    }
'''

if "function launchLinkedInLogin()" not in content:
    target_js = "    // 7. General Actions & Settings"
    content = content.replace(target_js, js_code + "\n    // 7. General Actions & Settings")
    print("Added LinkedIn auth JavaScript functions.")

# Call checkAuthStatus on load
if "checkAuthStatus();" not in content:
    content = content.replace("fetchStats();", "fetchStats();\n      checkAuthStatus();")
    print("Added checkAuthStatus() to initialization.")

html_path.write_text(content, encoding="utf-8")
print("Dashboard HTML updated successfully!")
