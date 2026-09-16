/**
 * Records page functionality
 */

const caseFilter = document.getElementById('case-filter');
const confidenceFilter = document.getElementById('confidence-filter');
const reviewFilter = document.getElementById('review-filter');
const exportBtn = document.getElementById('export-btn');
const recordsTbody = document.getElementById('records-tbody');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const pageInfo = document.getElementById('page-info');

let currentPage = 1;
const recordsPerPage = 20;

// Load records on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadRecords);
} else {
    loadRecords();
}

// Event listeners for filters
if (caseFilter) {
    caseFilter.addEventListener('change', () => {
        currentPage = 1;
        loadRecords();
    });
}

if (confidenceFilter) {
    confidenceFilter.addEventListener('change', () => {
        currentPage = 1;
        loadRecords();
    });
}

if (reviewFilter) {
    reviewFilter.addEventListener('change', () => {
        currentPage = 1;
        loadRecords();
    });
}

if (exportBtn) {
    exportBtn.addEventListener('click', exportRecords);
}

if (prevBtn) {
    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadRecords();
            window.scrollTo(0, 0);
        }
    });
}

if (nextBtn) {
    nextBtn.addEventListener('click', () => {
        currentPage++;
        loadRecords();
        window.scrollTo(0, 0);
    });
}

// Load records from API
async function loadRecords() {
    try {
        const offset = (currentPage - 1) * recordsPerPage;
        let endpoint = `/api/v1/records?limit=${recordsPerPage}&offset=${offset}`;
        
        // Add filters
        const caseNumber = caseFilter.value;
        if (caseNumber) {
            endpoint += `&case_number=${encodeURIComponent(caseNumber)}`;
        }
        
        const confidenceLevel = confidenceFilter.value;
        if (confidenceLevel) {
            endpoint += `&confidence_level=${confidenceLevel}`;
        }
        
        const needsReview = reviewFilter.value;
        if (needsReview !== '') {
            endpoint += `&needs_review=${needsReview}`;
        }
        
        const data = await api.get(endpoint);
        
        // Display records
        displayRecords(data.records);
        
        // Update pagination
        const totalPages = Math.ceil(data.total / recordsPerPage);
        pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
        prevBtn.disabled = currentPage === 1;
        nextBtn.disabled = currentPage === totalPages;
        
    } catch (error) {
        recordsTbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; color: #e74c3c; padding: 20px;">
                    Error loading records. Please try again later.
                </td>
            </tr>
        `;
    }
}

// Display records in table
function displayRecords(records) {
    if (records.length === 0) {
        recordsTbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 20px; color: #7f8c8d;">
                    No records found matching your filters.
                </td>
            </tr>
        `;
        return;
    }
    
    recordsTbody.innerHTML = records.map(record => `
        <tr>
            <td><strong>${record.case_number || 'N/A'}</strong></td>
            <td>${formatDate(record.hearing_date)}</td>
            <td>${record.party_name || 'N/A'}</td>
            <td>${record.advocate || 'N/A'}</td>
            <td>${getConfidenceBadgeHTML(record.overall_confidence)}</td>
            <td>${getStatusBadgeHTML(record.needs_review)}</td>
            <td>
                <button class="btn btn-sm" onclick="viewDetails(${record.id})">View</button>
            </td>
        </tr>
    `).join('');
}

// View record details
async function viewDetails(recordId) {
    try {
        const data = await api.get(`/api/v1/records/${recordId}`);
        
        const modal = document.getElementById('detail-modal');
        const detailContent = document.getElementById('detail-content');
        
        detailContent.innerHTML = `
            <table style="width: 100%;">
                <tr>
                    <td style="width: 40%; padding: 0.5rem 0;"><strong>Case Number:</strong></td>
                    <td style="width: 60%; padding: 0.5rem 0;">${data.case_number || 'N/A'}</td>
                </tr>
                <tr>
                    <td><strong>Hearing Date:</strong></td>
                    <td>${formatDate(data.hearing_date)}</td>
                </tr>
                <tr>
                    <td><strong>Party Name:</strong></td>
                    <td>${data.party_name || 'N/A'}</td>
                </tr>
                <tr>
                    <td><strong>Advocate:</strong></td>
                    <td>${data.advocate || 'N/A'}</td>
                </tr>
                <tr style="border-top: 1px solid #ddd;">
                    <td><strong>Case Number Confidence:</strong></td>
                    <td>${formatConfidence(data.case_number_confidence)}</td>
                </tr>
                <tr>
                    <td><strong>Date Confidence:</strong></td>
                    <td>${formatConfidence(data.date_confidence)}</td>
                </tr>
                <tr>
                    <td><strong>Party Name Confidence:</strong></td>
                    <td>${formatConfidence(data.party_name_confidence)}</td>
                </tr>
                <tr>
                    <td><strong>Advocate Confidence:</strong></td>
                    <td>${formatConfidence(data.advocate_confidence)}</td>
                </tr>
                <tr style="border-top: 1px solid #ddd;">
                    <td><strong>Overall Confidence:</strong></td>
                    <td>${getConfidenceBadgeHTML(data.overall_confidence)}</td>
                </tr>
                <tr>
                    <td><strong>Needs Review:</strong></td>
                    <td>${data.needs_review ? '✓ Yes' : '✗ No'}</td>
                </tr>
                <tr>
                    <td><strong>Is Duplicate:</strong></td>
                    <td>${data.is_duplicate ? '✓ Yes' : '✗ No'}</td>
                </tr>
                <tr>
                    <td><strong>Validation Passed:</strong></td>
                    <td>${data.validation_passed ? '✓ Yes' : '✗ No'}</td>
                </tr>
                ${data.validation_issues ? `
                <tr style="border-top: 1px solid #ddd;">
                    <td><strong>Validation Issues:</strong></td>
                    <td><pre>${data.validation_issues}</pre></td>
                </tr>
                ` : ''}
            </table>
        `;
        
        modal.style.display = 'block';
    } catch (error) {
        showNotification('Error loading record details', 'error');
    }
}

// Export records
async function exportRecords() {
    const format = prompt('Select export format:\n1. CSV\n2. JSON\n3. Excel\n4. HTML\n\nEnter number (1-4):', '1');
    
    if (!format) return;
    
    const formatMap = { '1': 'csv', '2': 'json', '3': 'excel', '4': 'html' };
    const selectedFormat = formatMap[format];
    
    if (!selectedFormat) {
        showNotification('Invalid format selected', 'warning');
        return;
    }
    
    try {
        const filters = {};
        if (caseFilter.value) filters.case_number = caseFilter.value;
        if (confidenceFilter.value) filters.confidence_level = confidenceFilter.value;
        if (reviewFilter.value !== '') filters.needs_review = reviewFilter.value === 'true';
        
        const response = await fetch('/api/v1/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                format: selectedFormat,
                filters: filters
            })
        });
        
        if (!response.ok) {
            throw new Error('Export failed');
        }
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `records_${new Date().toISOString().split('T')[0]}.${selectedFormat}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showNotification('Export completed successfully', 'success');
    } catch (error) {
        showNotification('Error exporting records: ' + error.message, 'error');
    }
}

// Close modal
function closeModal() {
    const modal = document.getElementById('detail-modal');
    modal.style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('detail-modal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
};