/**
 * Keyword Autocomplete Module
 * Provides intelligent keyword suggestions from component_app.keyword table
 */

class KeywordAutocomplete {
    constructor(inputId, dropdownId, tagsId, hiddenInputId) {
        // Elements
        this.keywordInput = document.getElementById(inputId);
        this.keywordDropdown = document.getElementById(dropdownId);
        this.keywordTags = document.getElementById(tagsId);
        this.keywordsHiddenInput = document.getElementById(hiddenInputId);
        
        // State
        this.selectedKeywords = new Set();
        this.keywordSuggestions = [];
        this.selectedSuggestionIndex = -1;
        this.isDropdownVisible = false;
        this.searchTimeout = null;
        
        this.init();
    }
    
    init() {
        if (!this.keywordInput || !this.keywordDropdown || !this.keywordTags || !this.keywordsHiddenInput) {
            console.error('KeywordAutocomplete: Required elements not found');
            return;
        }
        
        console.log('KeywordAutocomplete: Initializing');
        
        // Initialize existing keywords
        this.keywordTags.querySelectorAll('.tag').forEach(tag => {
            this.selectedKeywords.add(tag.dataset.keyword);
        });
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        // Input events
        this.keywordInput.addEventListener('input', (e) => this.handleInputChange(e));
        this.keywordInput.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.keywordInput.addEventListener('focus', () => this.handleFocus());
        this.keywordInput.addEventListener('blur', () => this.handleBlur());
        
        // Tag removal
        this.keywordTags.addEventListener('click', (e) => this.handleTagRemove(e));
        
        // Dropdown clicks
        this.keywordDropdown.addEventListener('click', (e) => this.handleDropdownClick(e));
        
        console.log('KeywordAutocomplete: Event listeners set up');
    }
    
    handleInputChange(e) {
        const value = e.target.value.trim();
        console.log('KeywordAutocomplete: Input changed:', value);
        
        // Clear existing timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }
        
        // Debounce search requests
        if (value.length > 0) {
            this.searchTimeout = setTimeout(() => {
                this.searchKeywords(value);
            }, 300);
        } else {
            this.hideDropdown();
        }
    }
    
    handleKeydown(e) {
        const value = e.target.value.trim();
        
        switch(e.key) {
            case 'Enter':
                e.preventDefault();
                if (this.selectedSuggestionIndex >= 0 && this.keywordSuggestions[this.selectedSuggestionIndex]) {
                    this.selectSuggestion(this.keywordSuggestions[this.selectedSuggestionIndex]);
                } else if (value) {
                    this.addKeyword(value);
                }
                break;
                
            case ',':
            case 'Tab':
                e.preventDefault();
                if (value) {
                    this.addKeyword(value);
                }
                break;
                
            case 'ArrowDown':
                e.preventDefault();
                if (this.isDropdownVisible) {
                    this.selectedSuggestionIndex = Math.min(this.selectedSuggestionIndex + 1, this.keywordSuggestions.length - 1);
                    this.updateDropdownHighlight();
                }
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                if (this.isDropdownVisible) {
                    this.selectedSuggestionIndex = Math.max(this.selectedSuggestionIndex - 1, -1);
                    this.updateDropdownHighlight();
                }
                break;
                
            case 'Escape':
                this.hideDropdown();
                break;
        }
    }
    
    handleFocus() {
        const value = this.keywordInput.value.trim();
        if (value.length > 0) {
            this.searchKeywords(value);
        } else {
            // Show popular keywords when focused with empty input
            this.searchKeywords('');
        }
    }
    
    handleBlur() {
        // Delay hiding dropdown to allow for clicks on suggestions
        setTimeout(() => {
            this.hideDropdown();
        }, 150);
    }
    
    handleTagRemove(e) {
        if (e.target.closest('.tag-remove')) {
            const tag = e.target.closest('.tag');
            const keyword = tag.dataset.keyword;
            this.selectedKeywords.delete(keyword);
            tag.remove();
            this.updateKeywordsInput();
        }
    }
    
    handleDropdownClick(e) {
        const suggestionItem = e.target.closest('.keyword-suggestion-item');
        const createNewItem = e.target.closest('.keyword-create-new');
        
        if (suggestionItem) {
            const keywordName = suggestionItem.dataset.keyword;
            const suggestion = this.keywordSuggestions.find(s => s.name === keywordName);
            if (suggestion) {
                this.selectSuggestion(suggestion);
            }
        } else if (createNewItem) {
            const keywordName = createNewItem.dataset.keyword;
            if (keywordName) {
                this.addKeyword(keywordName);
                this.keywordInput.value = '';
                this.hideDropdown();
                this.keywordInput.focus();
            }
        }
    }
    
    async searchKeywords(query) {
        console.log('KeywordAutocomplete: Searching for:', query);
        try {
            this.showLoadingInDropdown();
            
            const url = `/api/keyword/search?q=${encodeURIComponent(query)}&limit=8`;
            console.log('KeywordAutocomplete: Fetching from:', url);
            
            const response = await fetch(url);
            console.log('KeywordAutocomplete: Response status:', response.status);
            
            const data = await response.json();
            console.log('KeywordAutocomplete: Search results:', data);
            
            if (data.keywords) {
                // Filter out already selected keywords (case insensitive)
                this.keywordSuggestions = data.keywords.filter(k => !this.selectedKeywords.has(k.name.toLowerCase()));
                console.log('KeywordAutocomplete: Filtered suggestions:', this.keywordSuggestions);
                this.renderDropdown();
            }
        } catch (error) {
            console.error('KeywordAutocomplete: Error searching keywords:', error);
            this.hideDropdown();
        }
    }
    
    showLoadingInDropdown() {
        if (!this.keywordDropdown) return;
        
        this.keywordDropdown.innerHTML = `
            <div class="keyword-loading">
                <div class="spinner"></div>
                <span>Searching keywords...</span>
            </div>
        `;
        this.showDropdown();
    }
    
    renderDropdown() {
        if (!this.keywordDropdown) return;
        
        if (this.keywordSuggestions.length === 0) {
            const query = this.keywordInput.value.trim();
            if (query) {
                this.keywordDropdown.innerHTML = `
                    <div class="keyword-no-results">No existing keywords found</div>
                    <div class="keyword-create-new" data-keyword="${this.escapeHtml(query)}">
                        <strong>Create new:</strong> "${this.escapeHtml(query)}"
                    </div>
                `;
            } else {
                this.keywordDropdown.innerHTML = '<div class="keyword-no-results">Start typing to search keywords</div>';
            }
        } else {
            let html = '';
            this.keywordSuggestions.forEach((suggestion, index) => {
                const highlightedName = this.highlightMatch(suggestion.name, this.keywordInput.value.trim());
                const matchTypeText = this.getMatchTypeText(suggestion.match_type);
                
                html += `
                    <div class="keyword-suggestion-item ${index === this.selectedSuggestionIndex ? 'highlighted' : ''}" 
                         data-keyword="${this.escapeHtml(suggestion.name)}" 
                         data-index="${index}">
                        <div class="keyword-suggestion-content">
                            <div class="keyword-suggestion-name">${highlightedName}</div>
                            <div class="keyword-suggestion-type">${matchTypeText}</div>
                        </div>
                        <div class="keyword-usage-count">${suggestion.usage_count || 0}</div>
                    </div>
                `;
            });
            
            // Add create new option if query doesn't exactly match any suggestion
            const query = this.keywordInput.value.trim();
            if (query && !this.keywordSuggestions.some(s => s.name.toLowerCase() === query.toLowerCase())) {
                html += `
                    <div class="keyword-create-new" data-keyword="${this.escapeHtml(query)}">
                        <strong>Create new:</strong> "${this.escapeHtml(query)}"
                    </div>
                `;
            }
            
            this.keywordDropdown.innerHTML = html;
        }
        
        this.showDropdown();
    }
    
    selectSuggestion(suggestion) {
        // Always use lowercase for consistency with database storage
        this.addKeyword(suggestion.name.toLowerCase());
        this.keywordInput.value = '';
        this.hideDropdown();
        this.keywordInput.focus();
    }
    
    addKeyword(keywordText) {
        const keyword = keywordText.trim().toLowerCase();
        if (keyword && !this.selectedKeywords.has(keyword)) {
            this.selectedKeywords.add(keyword);
            
            // Always display and store keywords in lowercase
            const tag = this.createTag(keyword, keyword);
            this.keywordTags.appendChild(tag);
            
            this.keywordInput.value = '';
            this.updateKeywordsInput();
            this.hideDropdown();
        }
    }
    
    createTag(text, value) {
        const tag = document.createElement('div');
        tag.className = 'tag';
        tag.dataset.keyword = value;
        
        const span = document.createElement('span');
        span.textContent = text;
        
        const removeBtn = document.createElement('button');
        removeBtn.type = 'button';
        removeBtn.className = 'tag-remove';
        removeBtn.setAttribute('aria-label', `Remove ${text}`);
        removeBtn.innerHTML = '<svg width="12" height="12" fill="currentColor" viewBox="0 0 16 16"><path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/></svg>';
        
        tag.appendChild(span);
        tag.appendChild(removeBtn);
        
        return tag;
    }
    
    showDropdown() {
        if (!this.keywordDropdown) return;
        
        this.keywordDropdown.classList.add('show');
        this.keywordDropdown.style.display = 'block';
        this.keywordInput.classList.add('keyword-input-with-autocomplete', 'has-suggestions');
        this.keywordInput.setAttribute('aria-expanded', 'true');
        this.keywordDropdown.setAttribute('aria-hidden', 'false');
        this.isDropdownVisible = true;
    }
    
    hideDropdown() {
        if (!this.keywordDropdown) return;
        
        this.keywordDropdown.classList.remove('show');
        this.keywordDropdown.style.display = 'none';
        this.keywordInput.classList.remove('has-suggestions');
        this.keywordInput.setAttribute('aria-expanded', 'false');
        this.keywordDropdown.setAttribute('aria-hidden', 'true');
        this.isDropdownVisible = false;
        this.selectedSuggestionIndex = -1;
    }
    
    updateDropdownHighlight() {
        if (!this.keywordDropdown) return;
        
        const items = this.keywordDropdown.querySelectorAll('.keyword-suggestion-item');
        items.forEach((item, index) => {
            if (index === this.selectedSuggestionIndex) {
                item.classList.add('highlighted');
            } else {
                item.classList.remove('highlighted');
            }
        });
    }
    
    highlightMatch(text, query) {
        if (!query.trim()) return this.escapeHtml(text);
        
        const escapedText = this.escapeHtml(text);
        const escapedQuery = this.escapeHtml(query);
        const regex = new RegExp(`(${escapedQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        
        return escapedText.replace(regex, '<span class="keyword-match-highlight">$1</span>');
    }
    
    getMatchTypeText(matchType) {
        switch(matchType) {
            case 'exact': return 'Exact match';
            case 'starts_with': return 'Starts with';
            case 'fuzzy': return 'Similar';
            case 'popular': return 'Popular';
            default: return 'Match';
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    updateKeywordsInput() {
        this.keywordsHiddenInput.value = Array.from(this.selectedKeywords).join(',');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize keyword autocomplete if elements exist
    if (document.getElementById('keyword_input') && 
        document.getElementById('keyword-dropdown') && 
        document.getElementById('keyword_tags') && 
        document.getElementById('keywords_input')) {
        
        console.log('KeywordAutocomplete: Starting initialization');
        window.keywordAutocomplete = new KeywordAutocomplete(
            'keyword_input',
            'keyword-dropdown', 
            'keyword_tags',
            'keywords_input'
        );
    } else {
        console.log('KeywordAutocomplete: Required elements not found, skipping initialization');
    }
});