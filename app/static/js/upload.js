/**
 * Upload page functionality
 */

const fileInput = document.getElementById('file-input');
const fileName = document.getElementById('file-name');
const uploadForm = document.getElementById('upload-form');
const uploadStatus = document.getElementById('upload-status');
const progressBar = document.getElementById('progress-bar');
const statusMessage = document.getElementById('status-message');
const uploadResult = document.getElementById('upload-result');
const resultContent = document.getElementById('result-content');

// File input change handler
if (fileInput) {
    fileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const size = (file.size / (1024 * 1024)).toFixed(2);
            fileName.textContent = `${file.name} (${size} MB)`;
        } else {
            fileName.textContent = 'No file selected';
        }
    });
}

// Form submission handler
if (uploadForm) {
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const file = fileInput.files[0];
        if (!file) {
            showNotification('Please select a file', 'warning');
            return;
        }

        // Validate file size (50 MB)
        if (file.size > 50 * 1024 * 1024) {
            showNotification('File size exceeds 50 MB limit', 'error');
            return;
        }

        // Create FormData
        const formData = new FormData();
        formData.append('file', file);

        uploadForm.style.display = 'none';
        uploadStatus.style.display = 'block';
        uploadResult.style.display = 'none';
        progressBar.style.width = '0%';
        
        try {
            // Step 1: Upload document
            statusMessage.textContent = 'Uploading document...';
            progressBar.style.width = '25%';
            
            const uploadResponse = await api.postFormData('/api/v1/documents', formData);
            const documentId = uploadResponse.document_id;
            
            progressBar.style.width = '50%';
            statusMessage.textContent = 'Processing document with OCR...';
            
            // Step 2: Process document
            const ocr_engine = document.getElementById('ocr-engine').value;
            const extract_method = document.getElementById('extract-method').value;
            
            const processResponse = await api.post(`/api/v1/documents/${documentId}/process`, {
                ocr_engine: ocr_engine,
                extract_method: extract_method
            });
            
            progressBar.style.width = '100%';
            statusMessage.textContent = 'Complete!';
            
            // Show results
            setTimeout(() => {
                uploadStatus.style.display = 'none';
                uploadResult.style.display = 'block';
                
                resultContent.innerHTML = `
                    <div class="result-details">
                        <p><strong>Document ID:</strong> ${documentId}</p>
                        <p><strong>Extraction Run ID:</strong> ${processResponse.extraction_run_id}</p>
                        <p><strong>Total Records:</strong> ${processResponse.total_records}</p>
                        <p><strong>Records Requiring Review:</strong> ${processResponse.records_requiring_review}</p>
                        <p><strong>Duplicates Found:</strong> ${processResponse.duplicates_found}</p>
                        <p><strong>Average Confidence:</strong> ${formatConfidence(processResponse.average_confidence)}</p>
                        <div style="margin-top: 1.5rem;">
                            <a href="/records" class="btn btn-primary">View Records</a>
                            <button onclick="resetForm()" class="btn btn-secondary">Upload Another</button>
                        </div>
                    </div>
                `;
                
                showNotification('Document processed successfully!', 'success');
            }, 500);
            
        } catch (error) {
            uploadStatus.style.display = 'none';
            uploadForm.style.display = 'block';
            showNotification('Upload failed: ' + error.message, 'error');
            progressBar.style.width = '0%';
        }
    });
}

function resetForm() {
    uploadForm.reset();
    fileInput.value = '';
    fileName.textContent = 'No file selected';
    uploadForm.style.display = 'block';
    uploadResult.style.display = 'none';
}