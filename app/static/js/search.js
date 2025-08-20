// Search functionality
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.querySelector('form[action*="search"]');
    const searchInput = document.querySelector('input[name="q"]');
    const categorySelect = document.querySelector('select[name="category"]');
    
    // Auto-complete functionality (basic implementation)
    if (searchInput) {
        let searchTimeout;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(() => {
                    showSearchSuggestions(query);
                }, 300);
            } else {
                hideSearchSuggestions();
            }
        });
        
        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target)) {
                hideSearchSuggestions();
            }
        });
    }
    
    // Quick search filters
    const quickFilters = document.querySelectorAll('.quick-filter');
    quickFilters.forEach(filter => {
        filter.addEventListener('click', function(e) {
            e.preventDefault();
            const category = this.getAttribute('data-category');
            const query = this.getAttribute('data-query');
            
            if (searchInput) searchInput.value = query || '';
            if (categorySelect) categorySelect.value = category || 'all';
            
            if (searchForm) searchForm.submit();
        });
    });
    
    // Search result highlighting
    highlightSearchTerms();
});

function showSearchSuggestions(query) {
    // This would typically make an AJAX call to get suggestions
    // For now, we'll create a simple dropdown with mock suggestions
    const searchInput = document.querySelector('input[name="q"]');
    if (!searchInput) return;
    
    let suggestionsContainer = document.getElementById('search-suggestions');
    if (!suggestionsContainer) {
        suggestionsContainer = document.createElement('div');
        suggestionsContainer.id = 'search-suggestions';
        suggestionsContainer.className = 'position-absolute bg-white border rounded shadow-sm';
        suggestionsContainer.style.cssText = `
            top: 100%;
            left: 0;
            right: 0;
            z-index: 1000;
            max-height: 300px;
            overflow-y: auto;
        `;
        searchInput.parentNode.style.position = 'relative';
        searchInput.parentNode.appendChild(suggestionsContainer);
    }
    
    // Mock suggestions - in a real app, this would come from the server
    const mockSuggestions = [
        'Pizza', 'Burger', 'Biryani', 'Chicken', 'Vegetarian',
        'Dessert', 'Ice Cream', 'Pasta', 'Noodles', 'Sandwich'
    ].filter(item => item.toLowerCase().includes(query.toLowerCase()));
    
    if (mockSuggestions.length > 0) {
        suggestionsContainer.innerHTML = mockSuggestions
            .slice(0, 5)
            .map(suggestion => `
                <div class="p-2 border-bottom suggestion-item" 
                     style="cursor: pointer;"
                     data-suggestion="${suggestion}">
                    <i class="fas fa-search text-muted me-2"></i>${suggestion}
                </div>
            `).join('');
        
        // Add click handlers to suggestions
        suggestionsContainer.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', function() {
                searchInput.value = this.getAttribute('data-suggestion');
                hideSearchSuggestions();
                document.querySelector('form[action*="search"]').submit();
            });
            
            item.addEventListener('mouseenter', function() {
                this.style.backgroundColor = '#f8f9fa';
            });
            
            item.addEventListener('mouseleave', function() {
                this.style.backgroundColor = 'white';
            });
        });
        
        suggestionsContainer.style.display = 'block';
    } else {
        hideSearchSuggestions();
    }
}

function hideSearchSuggestions() {
    const suggestionsContainer = document.getElementById('search-suggestions');
    if (suggestionsContainer) {
        suggestionsContainer.style.display = 'none';
    }
}

function highlightSearchTerms() {
    const searchParams = new URLSearchParams(window.location.search);
    const query = searchParams.get('q');
    
    if (query && query.trim()) {
        const searchTerms = query.trim().split(/\s+/);
        const resultElements = document.querySelectorAll('.search-result');
        
        resultElements.forEach(element => {
            let html = element.innerHTML;
            
            searchTerms.forEach(term => {
                if (term.length >= 2) {
                    const regex = new RegExp(`(${term})`, 'gi');
                    html = html.replace(regex, '<mark>$1</mark>');
                }
            });
            
            element.innerHTML = html;
        });
    }
}

// Advanced search toggle
function toggleAdvancedSearch() {
    const advancedSearch = document.getElementById('advanced-search');
    if (advancedSearch) {
        const isHidden = advancedSearch.style.display === 'none' || !advancedSearch.style.display;
        advancedSearch.style.display = isHidden ? 'block' : 'none';
        
        const toggleButton = document.querySelector('.toggle-advanced-search');
        if (toggleButton) {
            toggleButton.innerHTML = isHidden ? 
                '<i class="fas fa-chevron-up"></i> Hide Advanced' : 
                '<i class="fas fa-chevron-down"></i> Advanced Search';
        }
    }
}

// Search filters
document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.getAttribute('data-filter');
            const value = this.getAttribute('data-value');
            
            // Update URL with filter
            const url = new URL(window.location);
            url.searchParams.set(filter, value);
            window.location.href = url.toString();
        });
    });
});
