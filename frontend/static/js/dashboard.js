// frontend/static/js/dashboard.js

// ✅ Register the Alpine.js component
document.addEventListener('alpine:init', () => {
    console.log('✅ Alpine.js initializing...');
    
    Alpine.data('migrationApp', () => ({
        // ===== State =====
        sidebarCollapsed: false,
        currentView: 'dashboard',
        user: {
            name: 'Loading...',
            email: 'Loading...',
            avatar: '',
            full_name: ''
        },
        metrics: {
            total_migrations: 0,
            success_rate: 0,
            active_jobs: 0,
            avg_time: 0,
            migration_growth: 0
        },
        recent_migrations: [],
        repositories: [],
        selected_repo: '',
        isMigrating: false,
        progress: 0,
        current_step: -1,
        status_message: 'Ready to start',
        logs: [],
        history_filter: '',
        history_status_filter: '',
        migration_history: [],
        settings: {
            notifications: true,
            auto_repair: true
        },
        showImportModal: false,
        import_url: '',
        import_branch: 'main',
        migration_options: {
            auto_repair: true,
            generate_report: true,
            create_pr: false
        },
        migration_job_id: null,
        ws: null,
        
        // ===== Initialize =====
        async init() {
            console.log('🚀 Dashboard initializing...');
            await this.loadUserData();
            await this.fetchDashboard();
            await this.fetchRepositories();
            await this.fetchHistory();
            this.connectWebSocket();
            this.setupAutoRefresh();
        },
        
        // ===== Load User Data =====
        async loadUserData() {
            try {
                const token = localStorage.getItem('access_token');
                if (!token) {
                    window.location.href = '/login';
                    return;
                }
                
                const response = await fetch('/api/auth/me', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (!response.ok) {
                    if (response.status === 401) {
                        localStorage.removeItem('access_token');
                        localStorage.removeItem('refresh_token');
                        window.location.href = '/login';
                        return;
                    }
                    throw new Error('Failed to load user data');
                }
                
                const userData = await response.json();
                this.user = {
                    name: userData.full_name || userData.username || 'User',
                    email: userData.email || '',
                    full_name: userData.full_name || '',
                    avatar: userData.avatar_url || ''
                };
                
                console.log('✅ User data loaded:', this.user);
            } catch (error) {
                console.error('❌ Error loading user data:', error);
                this.user.name = 'Error';
                this.user.email = 'Please re-login';
            }
        },
        
        // ===== API Calls =====
        async fetchDashboard() {
            try {
                const token = localStorage.getItem('access_token');
                const response = await fetch('/api/dashboard', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (!response.ok) throw new Error('Failed to fetch dashboard');
                
                const data = await response.json();
                this.metrics = data.metrics || this.metrics;
                this.recent_migrations = data.recent_migrations || [];
                this.renderCharts();
            } catch (error) {
                console.error('Failed to fetch dashboard:', error);
                // Mock data for demo
                this.metrics = {
                    total_migrations: 12,
                    success_rate: 92,
                    active_jobs: 0,
                    avg_time: 3.5,
                    migration_growth: 15
                };
                this.recent_migrations = [
                    { id: 1, repository: 'my-django-app', framework: 'Django', from_version: '3.2', to_version: '4.2', status: 'completed', duration: 45 },
                    { id: 2, repository: 'react-dashboard', framework: 'React', from_version: '17', to_version: '18', status: 'completed', duration: 32 },
                    { id: 3, repository: 'fastapi-backend', framework: 'FastAPI', from_version: '0.68', to_version: '0.100', status: 'failed', duration: 18 }
                ];
            }
        },
        
        async fetchRepositories() {
            try {
                const token = localStorage.getItem('access_token');
                const response = await fetch('/api/repositories', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (!response.ok) throw new Error('Failed to fetch repositories');
                
                this.repositories = await response.json();
            } catch (error) {
                console.error('Failed to fetch repositories:', error);
                // Mock data for demo
                this.repositories = [
                    { id: 1, name: 'my-django-app', language: 'Python', framework: 'Django', file_count: 120, status: 'Ready' },
                    { id: 2, name: 'react-dashboard', language: 'JavaScript', framework: 'React', file_count: 85, status: 'Ready' },
                    { id: 3, name: 'fastapi-backend', language: 'Python', framework: 'FastAPI', file_count: 45, status: 'Ready' }
                ];
            }
        },
        
        async fetchHistory() {
            try {
                const token = localStorage.getItem('access_token');
                const response = await fetch('/api/migrations/history', {
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (!response.ok) throw new Error('Failed to fetch history');
                
                this.migration_history = await response.json();
            } catch (error) {
                console.error('Failed to fetch history:', error);
                // Mock data for demo
                this.migration_history = [
                    { id: 1, repository: 'my-django-app', framework: 'Django', status: 'completed', date: '2026-07-07', duration: 45 },
                    { id: 2, repository: 'react-dashboard', framework: 'React', status: 'completed', date: '2026-07-06', duration: 32 },
                    { id: 3, repository: 'fastapi-backend', framework: 'FastAPI', status: 'failed', date: '2026-07-05', duration: 18 }
                ];
            }
        },
        
        // ===== WebSocket Connection =====
        connectWebSocket() {
            try {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;
                
                this.ws = new WebSocket(wsUrl);
                
                this.ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                };
                
                this.ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                };
                
                this.ws.onopen = () => {
                    console.log('✅ WebSocket connected');
                };
            } catch (error) {
                console.warn('⚠️ WebSocket not available:', error);
            }
        },
        
        handleWebSocketMessage(data) {
            switch(data.type) {
                case 'progress':
                    this.progress = data.progress || 0;
                    this.status_message = data.status || 'Processing...';
                    this.current_step = data.step || 0;
                    break;
                case 'log':
                    this.logs.push({
                        timestamp: data.timestamp || new Date().toLocaleTimeString(),
                        level: data.level || 'info',
                        message: data.message || ''
                    });
                    this.scrollLogsToBottom();
                    break;
                case 'complete':
                    this.isMigrating = false;
                    this.status_message = '✅ Migration completed successfully!';
                    this.fetchDashboard();
                    this.fetchHistory();
                    break;
                case 'error':
                    this.isMigrating = false;
                    this.status_message = '❌ Migration failed: ' + (data.message || 'Unknown error');
                    break;
            }
        },
        
        // ===== Migration Actions =====
        async startMigration() {
            if (!this.selected_repo || this.isMigrating) return;
            
            this.isMigrating = true;
            this.progress = 0;
            this.current_step = -1;
            this.status_message = '🚀 Starting migration...';
            this.logs = [];
            
            try {
                const token = localStorage.getItem('access_token');
                const response = await fetch('/api/migrations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        repository_id: this.selected_repo,
                        options: this.migration_options
                    })
                });
                
                if (!response.ok) throw new Error('Failed to start migration');
                
                const data = await response.json();
                this.migration_job_id = data.id;
                
                if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                    this.ws.send(JSON.stringify({
                        type: 'subscribe',
                        job_id: data.id
                    }));
                }
                
            } catch (error) {
                console.error('Failed to start migration:', error);
                this.isMigrating = false;
                this.status_message = '❌ Failed to start migration: ' + error.message;
            }
        },
        
        async rerunMigration(jobId) {
            try {
                const token = localStorage.getItem('access_token');
                const response = await fetch(`/api/migrations/${jobId}/rerun`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                
                if (!response.ok) throw new Error('Failed to rerun migration');
                
                this.showNotification('🔄 Migration re-run started', 'success');
                this.fetchHistory();
            } catch (error) {
                console.error('Failed to rerun migration:', error);
                this.showNotification('❌ Failed to rerun migration', 'error');
            }
        },
        
        async viewReport(jobId) {
            window.open(`/api/reports/${jobId}`, '_blank');
        },
        
        async deleteMigration(jobId) {
            if (!confirm('Are you sure you want to delete this migration?')) return;
            
            try {
                const token = localStorage.getItem('access_token');
                await fetch(`/api/migrations/${jobId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });
                this.fetchHistory();
                this.showNotification('🗑️ Migration deleted', 'success');
            } catch (error) {
                console.error('Failed to delete migration:', error);
                this.showNotification('❌ Failed to delete migration', 'error');
            }
        },
        
        // ===== Repository Actions =====
        async importRepository() {
            if (!this.import_url) {
                this.showNotification('Please enter a repository URL', 'error');
                return;
            }
            
            try {
                const token = localStorage.getItem('access_token');
                const response = await fetch('/api/repositories/import', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        url: this.import_url,
                        branch: this.import_branch
                    })
                });
                
                if (!response.ok) throw new Error('Failed to import repository');
                
                const data = await response.json();
                this.showImportModal = false;
                this.import_url = '';
                this.import_branch = 'main';
                await this.fetchRepositories();
                this.showNotification('✅ Repository imported successfully!', 'success');
            } catch (error) {
                console.error('Failed to import repository:', error);
                this.showNotification('❌ Failed to import repository: ' + error.message, 'error');
            }
        },
        
        // ===== Settings Actions =====
        async updateProfile() {
            try {
                const token = localStorage.getItem('access_token');
                const response = await fetch('/api/user/profile', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        full_name: this.user.full_name
                    })
                });
                
                if (!response.ok) throw new Error('Failed to update profile');
                
                const data = await response.json();
                this.user.name = data.full_name || this.user.name;
                this.user.full_name = data.full_name || '';
                this.showNotification('✅ Profile updated successfully!', 'success');
            } catch (error) {
                console.error('Failed to update profile:', error);
                this.showNotification('❌ Failed to update profile', 'error');
            }
        },
        
        connectGitHub() {
            window.location.href = '/api/auth/github/login';
        },
        
        // ===== UI Helpers =====
        openImportModal() {
            this.showImportModal = true;
        },
        
        scrollLogsToBottom() {
            setTimeout(() => {
                const container = this.$refs.logContainer;
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            }, 100);
        },
        
        showNotification(message, type = 'info') {
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                border-radius: 8px;
                background: ${type === 'success' ? '#4caf50' : type === 'error' ? '#f44336' : '#2196f3'};
                color: white;
                font-weight: 500;
                z-index: 10000;
                box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                animation: slideIn 0.3s ease;
            `;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.opacity = '0';
                notification.style.transition = 'opacity 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        },
        
        setupAutoRefresh() {
            setInterval(() => {
                if (this.currentView === 'dashboard') {
                    this.fetchDashboard();
                }
                if (this.currentView === 'history') {
                    this.fetchHistory();
                }
            }, 30000);
        },
        
        viewRepoDetails(repoId) {
            console.log('Viewing repository:', repoId);
            this.showNotification('📂 Repository details coming soon!', 'info');
        },
        
        // ===== Computed =====
        get filtered_history() {
            let items = this.migration_history;
            
            if (this.history_filter) {
                const filter = this.history_filter.toLowerCase();
                items = items.filter(item => 
                    item.repository && item.repository.toLowerCase().includes(filter)
                );
            }
            
            if (this.history_status_filter) {
                items = items.filter(item => 
                    item.status === this.history_status_filter
                );
            }
            
            return items;
        },
        
        // ===== Charts =====
        renderCharts() {
            console.log('📊 Rendering charts...');
        },
        
        // ===== Logout =====
        logout() {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
    }));
    
    console.log('✅ migrationApp registered with Alpine.js!');
});

console.log('✅ dashboard.js loaded successfully!');