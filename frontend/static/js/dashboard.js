// ============================================================
// COMPLETE DASHBOARD.JS - All Functions
// ============================================================

// ===== STATE =====
let currentUser = {};
let repositories = [];
let migrationHistory = [];
let currentJobId = null;
let pollInterval = null;

// ===== API HELPERS =====
function getToken() { 
    return localStorage.getItem('access_token'); 
}

function getHeaders() {
    return {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
    };
}

// ===== TOAST NOTIFICATION =====
function showToast(title, message, duration = 3000) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    document.getElementById('toastTitle').textContent = title;
    document.getElementById('toastMessage').textContent = message;
    toast.classList.add('show');
    clearTimeout(toast._timeout);
    toast._timeout = setTimeout(() => toast.classList.remove('show'), duration);
}

// ===== SWITCH VIEW =====
function switchView(view) {
    document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
    const section = document.getElementById(`section-${view}`);
    if (section) section.classList.add('active');
    document.querySelectorAll('nav a').forEach(el => el.classList.remove('active'));
    const navLink = document.querySelector(`nav a[data-view="${view}"]`);
    if (navLink) navLink.classList.add('active');
    if (view === 'repositories') loadRepositories();
    if (view === 'history') loadHistory();
    if (view === 'migrate') populateRepoSelect();
}

// ===== LOAD USER =====
async function loadUser() {
    try {
        const response = await fetch('/api/auth/me', { headers: getHeaders() });
        if (!response.ok) {
            if (response.status === 401) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                window.location.href = '/login';
                return;
            }
            throw new Error('Failed to load user');
        }
        const user = await response.json();
        currentUser = user;
        const name = user.full_name || user.username || 'User';
        document.getElementById('userName').textContent = name;
        document.getElementById('userEmail').textContent = user.email || '';
        document.getElementById('welcomeName').textContent = name;
        document.getElementById('userAvatar').textContent = name.charAt(0).toUpperCase();
    } catch (e) {
        console.error('Error loading user:', e);
        showToast('Error', 'Failed to load user data');
    }
}

// ===== LOAD DASHBOARD =====
async function loadDashboard() {
    try {
        const response = await fetch('/api/repositories/', { headers: getHeaders() });
        if (response.ok) {
            const repos = await response.json();
            document.getElementById('repoCount').textContent = repos.length || 0;
        }
        
        const history = JSON.parse(localStorage.getItem('migration_history') || '[]');
        document.getElementById('migrationCount').textContent = history.length || 0;
        
        const completed = history.filter(h => h.status === 'success').length;
        const rate = history.length > 0 ? Math.round((completed / history.length) * 100) : 0;
        document.getElementById('successRate').textContent = rate + '%';
        
        const active = history.filter(h => h.status === 'running').length;
        document.getElementById('activeJobs').textContent = active;
        document.getElementById('activeStatus').textContent = active > 0 ? '🔄 Running...' : '✅ Idle';
        
    } catch (e) {
        console.error('Error loading dashboard:', e);
    }
}

// ===== LOAD REPOSITORIES =====
async function loadRepositories() {
    try {
        const response = await fetch('/api/repositories/', { headers: getHeaders() });
        if (!response.ok) throw new Error('Failed to load repositories');
        repositories = await response.json();
        document.getElementById('repoCount').textContent = repositories.length;
        document.getElementById('repoCountBadge').textContent = repositories.length;
        renderRepositories();
        populateRepoSelect();
    } catch (e) {
        console.error('Error loading repositories:', e);
        document.getElementById('repoList').innerHTML = `
            <p style="color:var(--text-secondary);grid-column:1/-1;text-align:center;padding:40px;">
                <i class="fas fa-exclamation-circle" style="font-size:32px;display:block;margin-bottom:12px;"></i>
                Failed to load repositories
            </p>
        `;
        showToast('Error', 'Failed to load repositories');
    }
}

// ===== RENDER REPOSITORIES =====
function renderRepositories() {
    const container = document.getElementById('repoList');
    if (!container) return;
    if (!repositories || repositories.length === 0) {
        container.innerHTML = `
            <p style="color:var(--text-secondary);grid-column:1/-1;text-align:center;padding:40px;">
                <i class="fas fa-inbox" style="font-size:32px;display:block;margin-bottom:12px;"></i>
                No repositories imported yet.
            </p>
        `;
        return;
    }
    container.innerHTML = repositories.map(r => `
        <div class="repo-card">
            <div class="repo-header">
                <i class="fas fa-github"></i>
                <span class="repo-name">${r.name || 'Unknown'}</span>
                <span class="repo-status ready">${r.status || 'Ready'}</span>
            </div>
            <div class="repo-details">
                <span><i class="fas fa-code"></i> ${r.framework || 'Unknown'}</span>
                <span><i class="fas fa-file-alt"></i> ${r.file_count || 0} files</span>
            </div>
            <div class="repo-actions">
                <button class="btn-migrate" onclick="runFullMigration('${r.id}')"><i class="fas fa-play"></i> Migrate</button>
                <button class="btn-analyze" onclick="runAnalyze('${r.id}')"><i class="fas fa-search"></i></button>
                <button class="btn-analyze" onclick="runReport('${r.id}')"><i class="fas fa-file-alt"></i></button>
                <button class="btn-download" onclick="downloadRepo('${r.id}', '${r.name}')"><i class="fas fa-download"></i> Download</button>
            </div>
        </div>
    `).join('');
}

// ===== POPULATE REPO SELECT =====
function populateRepoSelect() {
    const select = document.getElementById('migrateRepoSelect');
    if (!select) return;
    select.innerHTML = '<option value="">Choose a repository...</option>';
    repositories.forEach(r => {
        select.innerHTML += `<option value="${r.id}">${r.name}</option>`;
    });
}

// ===== OPEN/CLOSE IMPORT MODAL =====
function openImportModal() {
    document.getElementById('importModal').style.display = 'flex';
}

function closeImportModal() {
    document.getElementById('importModal').style.display = 'none';
}

// ===== IMPORT REPOSITORY =====
async function importRepository() {
    const url = document.getElementById('importUrl').value.trim();
    const branch = document.getElementById('importBranch').value.trim();
    if (!url) { showToast('Error', 'Please enter a GitHub URL'); return; }
    
    const btn = event.target;
    btn.textContent = 'Importing...';
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/repositories/import', {
            method: 'POST',
            headers: getHeaders(),
            body: JSON.stringify({ url, branch })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Import failed');
        showToast('✅ Success', 'Repository imported successfully!');
        closeImportModal();
        document.getElementById('importUrl').value = '';
        await loadRepositories();
        await loadDashboard();
    } catch (e) {
        showToast('❌ Error', e.message);
    } finally {
        btn.textContent = 'Import';
        btn.disabled = false;
    }
}

// ===== GET SELECTED REPO ID =====
function getSelectedRepo() {
    const select = document.getElementById('migrateRepoSelect');
    return select.value || (repositories.length > 0 ? repositories[0].id : null);
}

// ===== UPDATE PROGRESS =====
function updateProgress(percent, label) {
    const container = document.getElementById('progressContainer');
    const fill = document.getElementById('progressFill');
    const percentText = document.getElementById('progressPercent');
    const labelText = document.getElementById('progressLabel');
    if (container) container.classList.add('active');
    if (fill) fill.style.width = percent + '%';
    if (percentText) percentText.textContent = percent + '%';
    if (labelText) labelText.textContent = label || 'Processing...';
}

// ===== ADD LOG =====
function addLog(message, level = 'info') {
    const container = document.getElementById('logContainer');
    if (!container) return;
    container.classList.add('active');
    const time = new Date().toLocaleTimeString();
    container.innerHTML += `<div class="log-entry">
        <span class="log-time">${time}</span>
        <span class="log-level ${level}">${level}</span>
        ${message}
    </div>`;
    container.scrollTop = container.scrollHeight;
}

// ===== RUN FUNCTIONS =====
async function runFullMigration(repoId = null) {
    const id = repoId || getSelectedRepo();
    if (!id) { showToast('Error', 'Please select a repository first'); return; }
    
    const repoName = repositories.find(r => r.id === id)?.name || 'Unknown';
    updateProgress(0, `🚀 Starting migration for ${repoName}...`);
    addLog(`🚀 Starting full migration for ${repoName}`, 'info');
    
    try {
        updateProgress(20, '🔍 Analyzing repository...');
        addLog('🔍 Running Discovery Agent...', 'info');
        const analyzeRes = await fetch(`/api/repositories/${id}/analyze`, { method: 'POST', headers: getHeaders() });
        const analyzeData = await analyzeRes.json();
        if (!analyzeRes.ok) throw new Error(analyzeData.detail || 'Analysis failed');
        addLog(`✅ Framework: ${analyzeData.framework || 'Unknown'}`, 'success');
        
        updateProgress(40, '📋 Creating migration plan...');
        addLog('📋 Running Planning Agent...', 'info');
        const planRes = await fetch(`/api/repositories/${id}/plan`, { method: 'POST', headers: getHeaders() });
        const planData = await planRes.json();
        if (!planRes.ok) throw new Error(planData.detail || 'Planning failed');
        addLog(`✅ Plan created with ${planData.steps?.length || 0} steps`, 'success');
        
        updateProgress(60, '✍️ Executing migration...');
        addLog('✍️ Running Execution Agent...', 'info');
        const migrateRes = await fetch(`/api/repositories/${id}/migrate`, { method: 'POST', headers: getHeaders() });
        const migrateData = await migrateRes.json();
        if (!migrateRes.ok) throw new Error(migrateData.detail || 'Migration failed');
        addLog(`✅ ${migrateData.modified_files || 0} files modified`, 'success');
        
        updateProgress(80, '🧪 Verifying migration...');
        addLog('🧪 Running Verification Agent...', 'info');
        const verifyRes = await fetch(`/api/repositories/${id}/verify`, { method: 'POST', headers: getHeaders() });
        const verifyData = await verifyRes.json();
        if (!verifyRes.ok) throw new Error(verifyData.detail || 'Verification failed');
        
        updateProgress(100, '✅ Migration complete!');
        addLog('✅ Migration completed successfully!', 'success');
        
        const history = JSON.parse(localStorage.getItem('migration_history') || '[]');
        history.push({ repo_id: id, repo_name: repoName, action: 'Full Migration', status: 'success', date: new Date().toISOString() });
        localStorage.setItem('migration_history', JSON.stringify(history));
        loadDashboard();
        loadHistory();
        showToast('🎉 Success', `Migration of ${repoName} completed!`);
        
    } catch (e) {
        updateProgress(100, '❌ Migration failed');
        addLog(`❌ Error: ${e.message}`, 'error');
        showToast('❌ Error', e.message);
        const history = JSON.parse(localStorage.getItem('migration_history') || '[]');
        history.push({ repo_id: id, repo_name: repoName, action: 'Full Migration', status: 'failed', date: new Date().toISOString() });
        localStorage.setItem('migration_history', JSON.stringify(history));
    }
}

async function runAnalyze(repoId = null) {
    const id = repoId || getSelectedRepo();
    if (!id) { showToast('Error', 'Please select a repository first'); return; }
    showToast('🔍 Analyzing', 'Analyzing repository...');
    try {
        const res = await fetch(`/api/repositories/${id}/analyze`, { method: 'POST', headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Analysis failed');
        showToast('✅ Analysis Complete', `Framework: ${data.framework || 'Unknown'}`);
    } catch (e) {
        showToast('❌ Error', e.message);
    }
}

async function runPlan(repoId = null) {
    const id = repoId || getSelectedRepo();
    if (!id) { showToast('Error', 'Please select a repository first'); return; }
    showToast('📋 Planning', 'Creating migration plan...');
    try {
        const res = await fetch(`/api/repositories/${id}/plan`, { method: 'POST', headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Planning failed');
        showToast('✅ Plan Created', `${data.steps?.length || 0} steps planned`);
    } catch (e) {
        showToast('❌ Error', e.message);
    }
}

async function runMigrate(repoId = null) {
    const id = repoId || getSelectedRepo();
    if (!id) { showToast('Error', 'Please select a repository first'); return; }
    showToast('✍️ Migrating', 'Applying changes...');
    try {
        const res = await fetch(`/api/repositories/${id}/migrate`, { method: 'POST', headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Migration failed');
        showToast('✅ Migration Complete', `${data.modified_files || 0} files modified`);
    } catch (e) {
        showToast('❌ Error', e.message);
    }
}

async function runVerify(repoId = null) {
    const id = repoId || getSelectedRepo();
    if (!id) { showToast('Error', 'Please select a repository first'); return; }
    showToast('🧪 Verifying', 'Running tests...');
    try {
        const res = await fetch(`/api/repositories/${id}/verify`, { method: 'POST', headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Verification failed');
        showToast('✅ Verification Complete', `${data.passed || 0} tests passed`);
    } catch (e) {
        showToast('❌ Error', e.message);
    }
}

async function runReport(repoId = null) {
    const id = repoId || getSelectedRepo();
    if (!id) { showToast('Error', 'Please select a repository first'); return; }
    showToast('📊 Report', 'Generating report...');
    try {
        const res = await fetch(`/api/repositories/${id}/report`, { method: 'POST', headers: getHeaders() });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Report generation failed');
        showToast('✅ Report Ready', `Files modified: ${data.summary?.files_modified || 0}`);
    } catch (e) {
        showToast('❌ Error', e.message);
    }
}

// ===== LOAD HISTORY =====
function loadHistory() {
    const container = document.getElementById('historyList');
    if (!container) return;
    const history = JSON.parse(localStorage.getItem('migration_history') || '[]');
    if (history.length === 0) {
        container.innerHTML = `
            <p style="color:var(--text-secondary);text-align:center;padding:40px 0;">
                <i class="fas fa-history" style="font-size:32px;display:block;margin-bottom:12px;"></i>
                No migration history yet.
            </p>
        `;
        return;
    }
    container.innerHTML = `
        <div style="background:var(--glass-bg);backdrop-filter:blur(20px);border:1px solid var(--glass-border);border-radius:16px;overflow:hidden;">
            <table style="width:100%;border-collapse:collapse;">
                <thead style="background:rgba(0,0,0,0.2);">
                    <tr>
                        <th style="padding:12px 16px;text-align:left;font-size:12px;text-transform:uppercase;color:var(--text-secondary);font-weight:500;">Repository</th>
                        <th style="padding:12px 16px;text-align:left;font-size:12px;text-transform:uppercase;color:var(--text-secondary);font-weight:500;">Action</th>
                        <th style="padding:12px 16px;text-align:left;font-size:12px;text-transform:uppercase;color:var(--text-secondary);font-weight:500;">Status</th>
                        <th style="padding:12px 16px;text-align:left;font-size:12px;text-transform:uppercase;color:var(--text-secondary);font-weight:500;">Date</th>
                    </tr>
                </thead>
                <tbody>
                    ${history.slice().reverse().map(h => `
                        <tr>
                            <td style="padding:12px 16px;border-top:1px solid var(--glass-border);">${h.repo_name || 'Unknown'}</td>
                            <td style="padding:12px 16px;border-top:1px solid var(--glass-border);">${h.action || 'Migration'}</td>
                            <td style="padding:12px 16px;border-top:1px solid var(--glass-border);">
                                <span style="padding:4px 12px;border-radius:20px;font-size:11px;font-weight:500;background:${h.status === 'success' ? 'rgba(0,184,148,0.2)' : 'rgba(255,71,87,0.2)'};color:${h.status === 'success' ? '#00b894' : '#ff6b6b'};">
                                    ${h.status || 'Pending'}
                                </span>
                            </td>
                            <td style="padding:12px 16px;border-top:1px solid var(--glass-border);font-size:13px;color:var(--text-secondary);">${new Date(h.date).toLocaleString()}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// ===== LOGOUT =====
function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('migration_history');
    window.location.href = '/login';
}

// ===== DOWNLOAD REPOSITORY =====
function downloadRepo(repoId, repoName) {
    const token = localStorage.getItem('access_token');
    if (!token) {
        showToast('Error', 'Please login first');
        return;
    }
    
    showToast('📥 Downloading', `Starting download of ${repoName}...`);
    
    // Open download in new tab
    window.open(`/api/repositories/${repoId}/download?token=${token}`, '_blank');
    
    setTimeout(() => {
        showToast('✅ Success', `Download of ${repoName} started!`);
    }, 1000);
}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', async function() {
    const token = localStorage.getItem('access_token');
    if (!token) { window.location.href = '/login'; return; }
    await loadUser();
    await loadDashboard();
    await loadRepositories();
    await loadHistory();
    setTimeout(populateRepoSelect, 500);
});

// Click outside modal to close
document.getElementById('importModal').addEventListener('click', function(e) {
    if (e.target === this) closeImportModal();
});

// Close modal with Escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeImportModal();
});