// Search Autocomplete
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const searchSuggestions = document.getElementById('search-suggestions');
    
    if (searchInput && searchSuggestions) {
        // Show suggestions when input is focused
        searchInput.addEventListener('focus', function() {
            if (searchInput.value && searchSuggestions.children.length > 0) {
                searchSuggestions.classList.add('show');
            }
        });
        
        // Hide suggestions when clicked outside
        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
                searchSuggestions.classList.remove('show');
            }
        });
        
        // Fetch suggestions as user types
        let typingTimer;
        const doneTypingInterval = 300; // ms
        
        searchInput.addEventListener('input', function() {
            clearTimeout(typingTimer);
            
            if (searchInput.value) {
                typingTimer = setTimeout(fetchSuggestions, doneTypingInterval);
            } else {
                searchSuggestions.innerHTML = '';
                searchSuggestions.classList.remove('show');
            }
        });
        
        // Function to fetch suggestions
        function fetchSuggestions() {
            const query = searchInput.value.trim();
            if (!query || query.length < 2) return;
            
            // Get any category selection if available
            const categorySelect = document.querySelector('select[name="category"]');
            const category = categorySelect ? categorySelect.value : 'all';
            
            // Get price range if available
            const priceMin = document.querySelector('input[name="price_min"]');
            const priceMax = document.querySelector('input[name="price_max"]');
            
            // Build query parameters
            const params = new URLSearchParams();
            params.append('q', query);
            if (category && category !== 'all') params.append('category', category);
            if (priceMin && priceMin.value) params.append('price_min', priceMin.value);
            if (priceMax && priceMax.value) params.append('price_max', priceMax.value);
            
            fetch(`/api/search_suggestions?${params.toString()}`)
                .then(response => response.json())
                .then(data => {
                    // Clear previous suggestions
                    searchSuggestions.innerHTML = '';
                    
                    if (data.suggestions && data.suggestions.length > 0) {
                        // Add new suggestions
                        data.suggestions.forEach(item => {
                            const suggestion = document.createElement('a');
                            suggestion.href = `#`;
                            suggestion.className = 'list-group-item list-group-item-action d-flex align-items-center';
                            
                            // Create suggestion content
                            suggestion.innerHTML = `
                                <div class="suggestion-img me-3">
                                    <img src="${item.image || '/static/images/food-placeholder.jpg'}" alt="${item.name}" class="rounded" width="40">
                                </div>
                                <div class="suggestion-content">
                                    <div class="suggestion-name">${highlightMatch(item.name, query)}</div>
                                    <div class="suggestion-price small text-success">₹${item.price.toFixed(2)}</div>
                                </div>
                            `;
                            
                            // Add click handler
                            suggestion.addEventListener('click', function(e) {
                                e.preventDefault();
                                searchInput.value = item.name;
                                searchSuggestions.classList.remove('show');
                                // Submit the parent form
                                const form = searchInput.closest('form');
                                if (form) form.submit();
                            });
                            
                            searchSuggestions.appendChild(suggestion);
                        });
                        
                        // Show suggestions dropdown
                        searchSuggestions.classList.add('show');
                    } else {
                        // No suggestions found
                        const noResults = document.createElement('div');
                        noResults.className = 'list-group-item text-muted text-center';
                        noResults.innerHTML = 'No matches found';
                        searchSuggestions.appendChild(noResults);
                        searchSuggestions.classList.add('show');
                    }
                })
                .catch(error => {
                    console.error('Error fetching search suggestions:', error);
                    
                    // Show error message
                    searchSuggestions.innerHTML = '<div class="list-group-item text-danger text-center">Error loading suggestions</div>';
                    searchSuggestions.classList.add('show');
                    
                    // Hide after a delay
                    setTimeout(() => {
                        searchSuggestions.classList.remove('show');
                    }, 3000);
                });
        }
        
        // Highlight matching text
        function highlightMatch(text, query) {
            const regex = new RegExp(`(${query})`, 'gi');
            return text.replace(regex, '<strong class="text-primary">$1</strong>');
        }
    }

// Function to highlight search results
document.addEventListener('DOMContentLoaded', function() {
    // Search result highlighting
    highlightSearchResults();
    
    // Price range slider functionality
    const priceMinInput = document.querySelector('input[name="price_min"]');
    const priceMaxInput = document.querySelector('input[name="price_max"]');
    
    if (priceMinInput && priceMaxInput) {
        // Ensure min cannot exceed max
        priceMinInput.addEventListener('change', function() {
            if (priceMaxInput.value && Number(priceMinInput.value) > Number(priceMaxInput.value)) {
                priceMaxInput.value = priceMinInput.value;
            }
        });
        
        // Ensure max cannot be less than min
        priceMaxInput.addEventListener('change', function() {
            if (priceMinInput.value && Number(priceMaxInput.value) < Number(priceMinInput.value)) {
                priceMinInput.value = priceMaxInput.value;
            }
        });
    }
    
    // Quick filters
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            const filter = this.getAttribute('data-filter');
            const value = this.getAttribute('data-value');
            
            // Update form input and submit
            if (filter === 'category') {
                const categorySelect = document.querySelector('select[name="category"]');
                if (categorySelect) categorySelect.value = value;
            } else if (filter === 'price_range') {
                const [min, max] = value.split('-');
                if (priceMinInput) priceMinInput.value = min;
                if (priceMaxInput) priceMaxInput.value = max;
            }
            
            // Submit form
            const searchForm = document.querySelector('form[action*="search"]');
            if (searchForm) searchForm.submit();
        });
    });
});

function highlightSearchResults() {
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('query');
    
    if (query && query.trim()) {
        const terms = query.trim().split(/\s+/).filter(term => term.length > 1);
        
        if (terms.length > 0) {
            // Find all food item name and description elements
            document.querySelectorAll('.card-title, .card-text').forEach(element => {
                let content = element.innerHTML;
                
                // Apply highlighting for each term
                terms.forEach(term => {
                    const regex = new RegExp(`(${term})`, 'gi');
                    content = content.replace(regex, '<mark>$1</mark>');
                });
                
                element.innerHTML = content;
            });
        }
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
                '<i class="fas fa-chevron-up"></i> Hide Filters' : 
                '<i class="fas fa-sliders-h"></i> More Filters';
        }
    }
}
