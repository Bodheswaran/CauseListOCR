/**
 * Main JavaScript for CauseListOCR
 */

// Utility function to show notifications
function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.innerHTML = `
        ${message}
        <button class="alert-close" onclick="this.parentElement.style.display='none';">&times;</button>
    `;
    
    const main = document.querySelector('main');
    if (main) {
        main.insertBefore(alertDiv, main.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentElement) {
                alertDiv.style.display = 'none';
            }
        }, 5000);
    }
}

// API helper functions
const api = {
    async get(endpoint) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API GET error:', error);
            showNotification('Error loading data: ' + error.message, 'error');
            throw error;
        }
    },

    async post(endpoint, data) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API POST error:', error);
            showNotification('Error: ' + error.message, 'error');
            throw error;
        }
    },

    async postFormData(endpoint, formData) {
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                body: formData
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || `HTTP ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API FormData POST error:', error);
            showNotification('Error: ' + error.message, 'error');
            throw error;
        }
    }
};

// Format confidence as percentage
function formatConfidence(value) {
    return (value * 100).toFixed(1) + '%';
}

// Get confidence level badge HTML
function getConfidenceBadgeHTML(value) {
    let level = 'low';
    if (value >= 0.8) level = 'high';
    else if (value >= 0.5) level = 'medium';
    
    return `<span class="confidence-badge confidence-${level}">${formatConfidence(value)}</span>`;
}

// Get status badge HTML
function getStatusBadgeHTML(needsReview) {
    if (needsReview) {
        return '<span class="status-badge status-needs-review">Needs Review</span>';
    } else {
        return '<span class="status-badge status-reviewed">Reviewed</span>';
    }
}

// Format date
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Initialize tooltips (if using a library)
function initTooltips() {
    // Add tooltip initialization here if needed
}

// Global error handler
window.addEventListener('error', function(event) {
    console.error('Uncaught error:', event.error);
});

// Global fetch error handler
window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
});

// Initialize on document ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTooltips);
} else {
    initTooltips();
}