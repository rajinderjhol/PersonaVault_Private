/**
 * Intelligence Marketplace - Discover and install intelligence packs
 */

class Marketplace {
    constructor() {
        this.container = document.getElementById('marketplace-container');
        this.packs = [];
        this.total = 0;
        this.isLoading = false;
        this.filters = {
            category: '',
            search: '',
            minConfidence: 0
        };
        this.limit = 20;
        this.offset = 0;
        this.installedPacks = [];
    }
    
    init() {
        if (!this.container) return;
        this.render();
        this.loadPacks();
        this.loadInstalledPacks();
        this.setupEventListeners();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="marketplace-container">
                <!-- Header -->
                <div class="marketplace-header">
                    <div class="header-left">
                        <span class="icon">🏪</span>
                        <span class="title">Intelligence Marketplace</span>
                        <span class="badge">Beta</span>
                    </div>
                    <div class="header-right">
                        <button class="upload-btn" onclick="marketplace.showUploadModal()">
                            📤 Upload Pack
                        </button>
                    </div>
                </div>
                
                <!-- Stats -->
                <div class="marketplace-stats" id="marketplace-stats">
                    <div class="stat-item">
                        <span>📦 Total Packs: <span class="stat-value" id="total-packs">0</span></span>
                    </div>
                    <div class="stat-item">
                        <span>⬇️ Total Downloads: <span class="stat-value" id="total-downloads">0</span></span>
                    </div>
                    <div class="stat-item">
                        <span>⭐ Avg. Rating: <span class="stat-value" id="avg-rating">0.0</span></span>
                    </div>
                    <div class="stat-item">
                        <span>📥 Installed: <span class="stat-value" id="installed-count">0</span></span>
                    </div>
                </div>
                
                <!-- Filters -->
                <div class="marketplace-filters">
                    <div class="search-bar">
                        <input 
                            type="text" 
                            class="search-input" 
                            id="marketplace-search" 
                            placeholder="Search for intelligence packs..."
                        >
                        <button class="search-btn" onclick="marketplace.search()">
                            🔍 Search
                        </button>
                    </div>
                    <select class="filter-select" id="category-filter">
                        <option value="">All Categories</option>
                        <option value="clinical">🏥 Clinical</option>
                        <option value="security">🔒 Security</option>
                        <option value="compliance">📋 Compliance</option>
                        <option value="contracts">📝 Contracts</option>
                        <option value="education">📚 Education</option>
                        <option value="procurement">📦 Procurement</option>
                        <option value="insurance">🛡️ Insurance</option>
                        <option value="robotics">🤖 Robotics</option>
                    </select>
                    <select class="filter-select" id="confidence-filter">
                        <option value="0">All Confidence</option>
                        <option value="0.5">Medium (50%+)</option>
                        <option value="0.7">High (70%+)</option>
                        <option value="0.9">Very High (90%+)</option>
                    </select>
                </div>
                
                <!-- Pack Grid -->
                <div class="pack-grid" id="pack-grid">
                    <div class="loading-state">
                        <div class="spinner">⏳</div>
                        <p>Loading packs...</p>
                    </div>
                </div>
                
                <!-- Footer -->
                <div class="explorer-footer" style="margin-top: 20px; display: flex; justify-content: space-between; align-items: center; padding-top: 16px; border-top: 1px solid #e8e8e8;">
                    <div class="pagination" id="pagination">
                        <button class="page-btn prev" onclick="marketplace.prevPage()">←</button>
                        <span class="page-info" id="page-info">Page 1</span>
                        <button class="page-btn next" onclick="marketplace.nextPage()">→</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    async loadPacks() {
        if (this.isLoading) return;
        this.isLoading = true;
        
        const grid = document.getElementById('pack-grid');
        grid.innerHTML = `
            <div class="loading-state">
                <div class="spinner">⏳</div>
                <p>Loading packs...</p>
            </div>
        `;
        
        try {
            const params = new URLSearchParams({
                limit: this.limit,
                offset: this.offset,
                category: this.filters.category,
                search: this.filters.search,
                min_confidence: this.filters.minConfidence
            });
            
            const response = await fetch(`/api/v1/marketplace/packs?${params}`);
            const data = await response.json();
            
            this.packs = data.packs || [];
            this.total = data.total || 0;
            
            this.renderPacks();
            this.updateStats();
            this.updatePagination();
            
        } catch (error) {
            console.error('Failed to load packs:', error);
            grid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">❌</div>
                    <div class="empty-title">Failed to load packs</div>
                    <div class="empty-desc">${error.message}</div>
                    <button onclick="marketplace.loadPacks()" style="margin-top: 12px; padding: 8px 20px; border: none; border-radius: 6px; background: #2196F3; color: white; cursor: pointer;">Retry</button>
                </div>
            `;
        }
        
        this.isLoading = false;
    }
    
    async loadInstalledPacks() {
        try {
            const response = await fetch('/api/v1/marketplace/installed');
            const data = await response.json();
            this.installedPacks = data.packs || [];
            this.updateStats();
        } catch (error) {
            console.error('Failed to load installed packs:', error);
        }
    }
    
    renderPacks() {
        const grid = document.getElementById('pack-grid');
        
        if (this.packs.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">🔍</div>
                    <div class="empty-title">No packs found</div>
                    <div class="empty-desc">Try adjusting your search or filters</div>
                </div>
            `;
            return;
        }
        
        const installedIds = this.installedPacks.map(p => p.id);
        
        grid.innerHTML = this.packs.map(pack => {
            const metadata = pack.metadata || {};
            const stats = pack.statistics || {};
            const isInstalled = installedIds.includes(pack.id);
            const rating = stats.rating_avg || 0;
            const confidence = stats.confidence_avg || 0;
            
            return `
                <div class="pack-card">
                    ${isInstalled ? '<span class="installed-badge">✅ Installed</span>' : ''}
                    <div class="pack-badge ${metadata.category || 'general'}">${metadata.category || 'General'}</div>
                    <div class="pack-name">${metadata.name || pack.id}</div>
                    <div class="pack-version">v${metadata.version || '1.0.0'}</div>
                    <div class="pack-description">${metadata.description || 'No description available'}</div>
                    
                    <div class="pack-meta">
                        <span class="meta-item">👤 ${metadata.author || 'Unknown'}</span>
                        <span class="meta-item">📅 ${new Date(pack.created_at).toLocaleDateString()}</span>
                    </div>
                    
                    <div class="pack-stats">
                        <span class="stat">📥 Downloads: <span class="stat-value">${stats.download_count || 0}</span></span>
                        <span class="stat">📊 Confidence: <span class="stat-value">${Math.round(confidence * 100)}%</span></span>
                        <span class="stat">💎 Patterns: <span class="stat-value">${stats.pattern_count || 0}</span></span>
                        <span class="stat pack-rating">
                            ⭐ <span class="rating-value">${rating.toFixed(1)}</span>
                            <span class="rating-count">(${stats.rating_count || 0})</span>
                        </span>
                    </div>
                    
                    <div class="pack-actions">
                        ${isInstalled ? `
                            <button class="action-btn installed" disabled>✅ Installed</button>
                        ` : `
                            <button class="action-btn install" onclick="marketplace.installPack('${pack.id}')">
                                📥 Install
                            </button>
                        `}
                        <button class="action-btn details" onclick="marketplace.viewPack('${pack.id}')">
                            📋 Details
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    updateStats() {
        const totalPacks = document.getElementById('total-packs');
        const totalDownloads = document.getElementById('total-downloads');
        const avgRating = document.getElementById('avg-rating');
        const installedCount = document.getElementById('installed-count');
        
        if (totalPacks) totalPacks.textContent = this.total;
        
        if (this.packs.length > 0) {
            const downloads = this.packs.reduce((sum, p) => sum + (p.statistics?.download_count || 0), 0);
            if (totalDownloads) totalDownloads.textContent = downloads;
            
            const ratings = this.packs.filter(p => p.statistics?.rating_avg > 0);
            if (ratings.length > 0) {
                const avg = ratings.reduce((sum, p) => sum + (p.statistics?.rating_avg || 0), 0) / ratings.length;
                if (avgRating) avgRating.textContent = avg.toFixed(1);
            }
        }
        
        if (installedCount) installedCount.textContent = this.installedPacks.length;
    }
    
    updatePagination() {
        const pageInfo = document.getElementById('page-info');
        const totalPages = Math.ceil(this.total / this.limit);
        const currentPage = Math.floor(this.offset / this.limit) + 1;
        
        if (pageInfo) {
            pageInfo.textContent = `Page ${currentPage} of ${totalPages || 1}`;
        }
        
        const prevBtn = document.querySelector('.page-btn.prev');
        const nextBtn = document.querySelector('.page-btn.next');
        
        if (prevBtn) prevBtn.disabled = this.offset === 0;
        if (nextBtn) nextBtn.disabled = this.offset + this.limit >= this.total;
    }
    
    setupEventListeners() {
        // Search with debounce
        const searchInput = document.getElementById('marketplace-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.filters.search = e.target.value;
                    this.offset = 0;
                    this.loadPacks();
                }, 300);
            });
        }
        
        const categoryFilter = document.getElementById('category-filter');
        if (categoryFilter) {
            categoryFilter.addEventListener('change', (e) => {
                this.filters.category = e.target.value;
                this.offset = 0;
                this.loadPacks();
            });
        }
        
        const confidenceFilter = document.getElementById('confidence-filter');
        if (confidenceFilter) {
            confidenceFilter.addEventListener('change', (e) => {
                this.filters.minConfidence = parseFloat(e.target.value);
                this.offset = 0;
                this.loadPacks();
            });
        }
    }
    
    search() {
        const input = document.getElementById('marketplace-search');
        if (input) {
            this.filters.search = input.value;
            this.offset = 0;
            this.loadPacks();
        }
    }
    
    nextPage() {
        if (this.offset + this.limit < this.total) {
            this.offset += this.limit;
            this.loadPacks();
        }
    }
    
    prevPage() {
        if (this.offset >= this.limit) {
            this.offset -= this.limit;
            this.loadPacks();
        }
    }
    
    async installPack(packId) {
        if (!confirm('Install this intelligence pack?')) return;
        
        try {
            const response = await fetch(`/api/v1/marketplace/packs/${packId}/install`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('✅ Pack installed successfully!', 'success');
                await this.loadInstalledPacks();
                await this.loadPacks();
            } else {
                this.showNotification('⚠️ ' + (result.message || 'Installation failed'), 'warning');
            }
        } catch (error) {
            this.showNotification('❌ Error: ' + error.message, 'error');
        }
    }
    
    async viewPack(packId) {
        window.location.href = `/admin/marketplace/pack/${packId}`;
    }
    
    showUploadModal() {
        const modal = document.createElement('div');
        modal.className = 'upload-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <span class="title">📤 Upload Intelligence Pack</span>
                    <button class="close-btn" onclick="marketplace.closeUploadModal()">×</button>
                </div>
                <form id="upload-form">
                    <div class="form-group">
                        <label>Pack Name *</label>
                        <input type="text" id="upload-name" placeholder="e.g., Clinical Triage Protocol" required>
                    </div>
                    <div class="form-group">
                        <label>Domain *</label>
                        <input type="text" id="upload-domain" placeholder="e.g., clinical" required>
                    </div>
                    <div class="form-group">
                        <label>Description *</label>
                        <textarea id="upload-description" placeholder="Describe your intelligence pack..." required></textarea>
                    </div>
                    <div class="form-group">
                        <label>Category *</label>
                        <select id="upload-category" required>
                            <option value="">Select category...</option>
                            <option value="clinical">🏥 Clinical</option>
                            <option value="security">🔒 Security</option>
                            <option value="compliance">📋 Compliance</option>
                            <option value="contracts">📝 Contracts</option>
                            <option value="education">📚 Education</option>
                            <option value="procurement">📦 Procurement</option>
                            <option value="insurance">🛡️ Insurance</option>
                            <option value="robotics">🤖 Robotics</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Version</label>
                        <input type="text" id="upload-version" value="1.0.0">
                    </div>
                    <div class="form-group">
                        <label>Tags (comma separated)</label>
                        <input type="text" id="upload-tags" placeholder="e.g., triage, protocol, emergency">
                    </div>
                    <div class="form-group">
                        <label>Pack File (compressed .tar.gz) *</label>
                        <div class="file-input" onclick="document.getElementById('upload-file').click()">
                            📁 Click to select file
                            <span class="file-name" id="file-name">No file selected</span>
                        </div>
                        <input type="file" id="upload-file" accept=".tar.gz" style="display: none;" required>
                    </div>
                    <button type="submit" class="submit-btn">📤 Upload Pack</button>
                </form>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Handle file selection
        const fileInput = document.getElementById('upload-file');
        fileInput.addEventListener('change', (e) => {
            const fileName = document.getElementById('file-name');
            if (fileInput.files.length > 0) {
                fileName.textContent = fileInput.files[0].name;
            }
        });
        
        // Handle form submission
        const form = document.getElementById('upload-form');
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            await this.submitUpload();
        });
    }
    
    closeUploadModal() {
        const modal = document.querySelector('.upload-modal');
        if (modal) modal.remove();
    }
    
    async submitUpload() {
        const form = document.getElementById('upload-form');
        const formData = new FormData(form);
        
        const fileInput = document.getElementById('upload-file');
        if (!fileInput.files.length) {
            this.showNotification('Please select a file', 'warning');
            return;
        }
        
        formData.append('file', fileInput.files[0]);
        
        try {
            const response = await fetch('/api/v1/marketplace/packs/upload?' + new URLSearchParams({
                name: document.getElementById('upload-name').value,
                domain: document.getElementById('upload-domain').value,
                description: document.getElementById('upload-description').value,
                category: document.getElementById('upload-category').value,
                version: document.getElementById('upload-version').value || '1.0.0',
                tags: document.getElementById('upload-tags').value || ''
            }), {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('✅ Pack uploaded successfully!', 'success');
                this.closeUploadModal();
                this.loadPacks();
            } else {
                this.showNotification('⚠️ ' + (result.detail || 'Upload failed'), 'error');
            }
        } catch (error) {
            this.showNotification('❌ Error: ' + error.message, 'error');
        }
    }
    
    showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            background: ${type === 'success' ? '#4CAF50' : type === 'error' ? '#f44336' : '#FF9800'};
            color: white;
            font-size: 14px;
            z-index: 9999;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            animation: slideIn 0.3s ease;
        `;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.marketplace = new Marketplace();
    window.marketplace.init();
});
