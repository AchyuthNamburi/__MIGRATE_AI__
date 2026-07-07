// frontend/static/js/dashboard.js

function migrationApp() {
    return {
        // State
        sidebarCollapsed: false,
        currentView: 'dashboard',
        user: {
            name: 'John Doe',
            email: 'john@example.com',
            avatar: '',
            full_name: 'John Doe'
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
        
        // Initialize
        init() {
            this.fetchDashboard();
            this.fetchRepositories();
            this.fetchHistory();
            this.connectWebSocket();
            this.setupAutoRefresh();
        },
        
        // ===== API Calls =====
        async fetchDashboard() {
            try {
                const response = await fetch('/api/dashboard', {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
                const data = await response.json();
                this.metrics = data.metrics;
                this.recent_migrations = data.recent_migrations;
                this.renderCharts();
            } catch (error) {
                console.error('Failed to fetch dashboard:', error);
            }
        },
        
        async fetchRepositories() {
            try {
                const response = await fetch('/api/repositories', {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
                this.repositories = await response.json();
            } catch (error) {
                console.error('Failed to fetch repositories:', error);
            }
        },
        
        async fetchHistory() {
            try {
                const response = await fetch('/api/migrations/history', {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
                this.migration_history = await response.json();
            } catch (error) {
                console.error('Failed to fetch history:', error);
            }
        },
        
        // ===== WebSocket Connection =====
        connectWebSocket() {
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
        },
        
        handleWebSocketMessage(data) {
            switch(data.type) {
                case 'progress':
                    this.progress = data.progress;
                    this.status_message = data.status;
                    this.current_step = data.step || 0;
                    break;
                case 'log':
                    this.logs.push({
                        timestamp: data.timestamp,
                        level: data.level || 'info',
                        message: data.message
                    });
                    this.scrollLogsToBottom();
                    break;
                case 'complete':
                    this.isMigrating = false;
                    this.status_message = 'Migration completed successfully! 🎉';
                    this.fetchDashboard();
                    this.fetchHistory();
                    break;
                case 'error':
                    this.isMigrating = false;
                    this.status_message = 'Migration failed: ' + data.message;
                    break;
            }
        },
        
        // ===== Migration Actions =====
        async startMigration() {
            if (!this.selected_repo || this.isMigrating) return;
            
            this.isMigrating = true;
            this.progress = 0;
            this.current_step = -1;
            this.status_message = 'Starting migration...';
            this.logs = [];
            
            try {
                const response = await fetch('/api/migrations', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: JSON.stringify({
                        repository_id: this.selected_repo,
                        options: this.migration_options
                    })
                });
                
                const data = await response.json();
                this.migration_job_id = data.id;
                
                // Subscribe to WebSocket updates for this job
                this.ws.send(JSON.stringify({
                    type: 'subscribe',
                    job_id: data.id
                }));
                
            } catch (error) {
                console.error('Failed to start migration:', error);
                this.isMigrating = false;
                this.status_message = 'Failed to start migration';
            }
        },
        
        async rerunMigration(jobId) {
            try {
                const response = await fetch(`/api/migrations/${jobId}/rerun`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
                const data = await response.json();
                // Show notification
                this.showNotification('Migration re-run started', 'success');
            } catch (error) {
                console.error('Failed to rerun migration:', error);
            }
        },
        
        async viewReport(jobId) {
            window.open(`/api/reports/${jobId}`, '_blank');
        },
        
        async deleteMigration(jobId) {
            if (!confirm('Are you sure you want to delete this migration?')) return;
            
            try {
                await fetch(`/api/migrations/${jobId}`, {
                    method: 'DELETE',
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });
                this.fetchHistory();
                this.showNotification('Migration deleted', 'success');
            } catch (error) {
                console.error('Failed to delete migration:', error);
            }
        },
        
        // ===== Repository Actions =====
        async importRepository() {
            if (!this.import_url) return;
            
            try {
                const response = await fetch('/api/repositories/import', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: JSON.stringify({
                        url: this.import_url,
                        branch: this.import_branch
                    })
                });
                
                const data = await response.json();
                this.showImportModal = false;
                this.fetchRepositories();
                this.showNotification('Repository imported successfully!', 'success');
            } catch (error) {
                console.error('Failed to import repository:', error);
                this.showNotification('Failed to import repository', 'error');
            }
        },
        
        // ===== Settings Actions =====
        async updateProfile() {
            try {
                const response = await fetch('/api/user/profile', {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: JSON.stringify({
                        full_name: this.user.full_name
                    })
                });
                await response.json();
                this.showNotification('Profile updated successfully!', 'success');
            } catch (error) {
                console.error('Failed to update profile:', error);
            }
        },
        
        connectGitHub() {
            window.location.href = '/auth/github/login';
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
            // Simple notification implementation
            const notification = document.createElement('div');
            notification.className = `notification notification-${type}`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 3000);
        },
        
        setupAutoRefresh() {
            // Refresh data every 30 seconds
            setInterval(() => {
                if (this.currentView === 'dashboard') {
                    this.fetchDashboard();
                }
                if (this.currentView === 'history') {
                    this.fetchHistory();
                }
            }, 30000);
        },
        
        // ===== Computed =====
        get filtered_history() {
            let items = this.migration_history;
            
            if (this.history_filter) {
                const filter = this.history_filter.toLowerCase();
                items = items.filter(item => 
                    item.repository.toLowerCase().includes(filter)
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
            // This would use Chart.js or similar library
            // Simplified for now
            console.log('Rendering charts...');
        },
        
        // ===== Logout =====
        logout() {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
    };
}

// Initialize when DOM is ready
document.addEventListener('alpine:init', () => {
    console.log('Migration App initialized');
});