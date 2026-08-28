/**
 * Pattern Explorer - Browse and interact with crystallized patterns
 */

class PatternExplorer {
    constructor() {
        this.patterns = [];
        this.total = 0;
        this.limit = 20;
        this.offset = 0;
        this.filters = {
            domain: '',
            min_confidence: 0,
            search: ''
        };
        this.isLoading = false;
    }
    
    init() {
        this.container = document.getElementById('pattern-explorer-container');
        if (!this.container) return;
        this.render();
        this.loadPatterns();
        this.setupEventListeners();
    }
    
    render() {
        this.container.innerHTML = `
            <div class="pattern-explorer-panel">
                <div class="explorer-header">
                    <div class="header-left">
                        <span class="icon">💎</span>
                        <span class="title">Pattern Explorer</span>
                        <span class="badge" id="pattern-count">0 patterns</span>
                    </div>
                    <div class="header-right">
                        <button class="refresh-btn" onclick="patternExplorer.refresh()">
                            🔄 Refresh
                        </button>
                    </div>
                </div>
                
                <div class="explorer-filters">
                    <div class="search-bar">
                        <input 
                            type="text" 
                            id="pattern-search" 
                            placeholder="Search patterns..." 
                            class="search-input"
                        >
                        <button class="search-btn" onclick="patternExplorer.search()">
                            🔍 Search
                        </button>
                    </div>
                    <div class="filter-group">
                        <select id="domain-filter" class="filter-select">
                            <option value="">All Domains</option>
                            <option value="security">🔒 Security</option>
                            <option value="compliance">📋 Compliance</option>
                            <option value="clinical">🏥 Clinical</option>
                            <option value="general">🧠 General</option>
                        </select>
                        <select id="confidence-filter" class="filter-select">
                            <option value="0">All Confidence</option>
                            <option value="0.5">Medium (>50%)</option>
                            <option value="0.7">High (>70%)</option>
                            <option value="0.9">Very High (>90%)</option>
                        </select>
                    </div>
                </div>
                
                <div class="pattern-grid" id="pattern-grid">
                    <div class="loading-state">
                        <span>⏳ Loading patterns...</span>
                    </div>
                </div>
                
                <div class="explorer-footer">
                    <div class="pattern-stats" id="pattern-stats">
                        <span>📊 Total: <strong id="total-patterns">0</strong></span>
                        <span>📈 Avg. Confidence: <strong id="avg-confidence">0%</strong></span>
                        <span>⚡ Compression: <strong>10,000:1</strong></span>
                    </div>
                    <div class="pagination" id="pagination">
                        <button class="page-btn prev" onclick="patternExplorer.prevPage()">←</button>
                        <span class="page-info" id="page-info">Page 1</span>
                        <button class="page-btn next" onclick="patternExplorer.nextPage()">→</button>
                    </div>
                </div>
            </div>
        `;
    }
    
    async loadPatterns() {
        if (this.isLoading) return;
        this.isLoading = true;
        
        const grid = document.getElementById('pattern-grid');
        grid.innerHTML = `<div class="loading-state">⏳ Loading patterns...</div>`;
        
        try {
            const params = new URLSearchParams({
                limit: this.limit,
                offset: this.offset,
                domain: this.filters.domain,
                min_confidence: this.filters.min_confidence,
                search: this.filters.search
            });
            
            const response = await fetch(`/api/v1/patterns/?${params}`);
            const data = await response.json();
            
            this.patterns = data.patterns || [];
            this.total = data.total || 0;
            
            this.renderPatterns();
            this.updateStats();
            this.updatePagination();
            
        } catch (error) {
            console.error('Failed to load patterns:', error);
            grid.innerHTML = `
                <div class="error-state">
                    <span>❌ Failed to load patterns</span>
                    <button onclick="patternExplorer.loadPatterns()">Retry</button>
                </div>
            `;
        }
        
        this.isLoading = false;
    }
    
    renderPatterns() {
        const grid = document.getElementById('pattern-grid');
        
        if (this.patterns.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <span>💎 No patterns found</span>
                    <span class="sub">Start asking complex questions to crystallize patterns!</span>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = this.patterns.map(pattern => `
            <div class="pattern-card" onclick="patternExplorer.viewPattern('${pattern.id}')">
                <div class="pattern-header">
                    <span class="pattern-domain">${pattern.pattern_type || 'general'}</span>
                    <span class="pattern-confidence ${pattern.weight >= 0.7 ? 'high' : pattern.weight >= 0.4 ? 'medium' : 'low'}">
                        ${Math.round(pattern.weight * 100)}%
                    </span>
                </div>
                <div class="pattern-content">
                    <div class="pattern-query">${this.truncate(pattern.trigger, 100)}</div>
                    <div class="pattern-response">${this.truncate(pattern.correction, 120)}</div>
                </div>
                <div class="pattern-footer">
                    <span class="pattern-uses">🔄 Used ${pattern.occurrence_count || 0} times</span>
                    <span class="pattern-date">${new Date(pattern.created_at || Date.now()).toLocaleDateString()}</span>
                    <div class="pattern-actions">
                        <button class="action-btn small" onclick="event.stopPropagation(); patternExplorer.replayPattern('${pattern.id}')">
                            ▶️ Replay
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }
    
    updateStats() {
        const totalEl = document.getElementById('total-patterns');
        const avgEl = document.getElementById('avg-confidence');
        const countEl = document.getElementById('pattern-count');
        
        if (totalEl) totalEl.textContent = this.total;
        if (countEl) countEl.textContent = `${this.total} patterns`;
        
        if (this.patterns.length > 0) {
            const avg = this.patterns.reduce((sum, p) => sum + p.weight, 0) / this.patterns.length;
            if (avgEl) avgEl.textContent = `${Math.round(avg * 100)}%`;
        } else {
            if (avgEl) avgEl.textContent = 'N/A';
        }
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
        // Debounced search
        const searchInput = document.getElementById('pattern-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.filters.search = e.target.value;
                    this.offset = 0;
                    this.loadPatterns();
                }, 300);
            });
        }
        
        const domainFilter = document.getElementById('domain-filter');
        if (domainFilter) {
            domainFilter.addEventListener('change', (e) => {
                this.filters.domain = e.target.value;
                this.offset = 0;
                this.loadPatterns();
            });
        }
        
        const confidenceFilter = document.getElementById('confidence-filter');
        if (confidenceFilter) {
            confidenceFilter.addEventListener('change', (e) => {
                this.filters.min_confidence = parseFloat(e.target.value);
                this.offset = 0;
                this.loadPatterns();
            });
        }
    }
    
    search() {
        const input = document.getElementById('pattern-search');
        if (input) {
            this.filters.search = input.value;
            this.offset = 0;
            this.loadPatterns();
        }
    }
    
    refresh() {
        this.loadPatterns();
    }
    
    nextPage() {
        if (this.offset + this.limit < this.total) {
            this.offset += this.limit;
            this.loadPatterns();
        }
    }
    
    prevPage() {
        if (this.offset >= this.limit) {
            this.offset -= this.limit;
            this.loadPatterns();
        }
    }
    
    viewPattern(patternId) {
        window.location.href = `/admin/patterns/${patternId}`;
    }
    
    async replayPattern(patternId) {
        const query = prompt('Enter a query to test this pattern:');
        if (!query) return;
        
        try {
            const response = await fetch(`/api/v1/patterns/${patternId}/replay`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            
            const result = await response.json();
            alert(`Replay complete!\n\nQuery: ${query}\nResponse: ${result.result.response}`);
        } catch (error) {
            alert('Failed to replay pattern: ' + error.message);
        }
    }
    
    truncate(text, length) {
        if (!text) return '';
        return text.length > length ? text.substring(0, length) + '...' : text;
    }
}

// Initialize
window.patternExplorer = new PatternExplorer();
if (document.readyState === 'complete' || document.readyState === 'interactive') {
    window.patternExplorer.init();
} else {
    document.addEventListener('DOMContentLoaded', () => {
        window.patternExplorer.init();
    });
}
