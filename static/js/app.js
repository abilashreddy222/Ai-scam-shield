document.addEventListener('DOMContentLoaded', () => {

    // --- Tabs Logic ---
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.classList.remove('active'));

            // Add active
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(tabId).classList.add('active');

            resetScanner();
        });
    });

    // --- File Upload Logic ---
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('screenshot-upload');
    const fileNameDisplay = document.getElementById('selected-file-name');
    const analyzeImgBtn = document.getElementById('analyze-img-btn');

    if (dropZone) {
        dropZone.addEventListener('click', () => fileInput.click());

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                updateFileInfo();
            }
        });

        fileInput.addEventListener('change', updateFileInfo);

        function updateFileInfo() {
            if (fileInput.files.length > 0) {
                fileNameDisplay.textContent = `Selected: ${fileInput.files[0].name}`;
                analyzeImgBtn.disabled = false;
            } else {
                fileNameDisplay.textContent = '';
                analyzeImgBtn.disabled = true;
            }
        }
    }

    // --- Text Analysis Submit ---
    const textForm = document.getElementById('text-scan-form');
    if (textForm) {
        textForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const text = document.getElementById('job-description').value;
            const email = document.getElementById('recruiter-email').value;

            if (!text.trim()) return;

            showLoading();
            try {
                const response = await fetch('/api/analyze/text', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text, email })
                });
                if (!response.ok) throw new Error("Server Error");
                const result = await response.json();
                setTimeout(() => displayResults(result), 800);
            } catch (err) {
                console.error("Analysis failed", err);
                showError("The system encountered an error connecting to the AI models. Please try again later.");
            }
        });
    }

    // --- Image OCR Analysis Submit ---
    const imgForm = document.getElementById('image-scan-form');
    if (imgForm) {
        imgForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (fileInput.files.length === 0) return;

            const formData = new FormData();
            formData.append('file', fileInput.files[0]);

            showLoading();
            try {
                const response = await fetch('/api/analyze/image', {
                    method: 'POST',
                    body: formData
                });
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || errorData.details || "Server Error");
                }
                const result = await response.json();
                setTimeout(() => displayResults(result, true), 1200);
            } catch (err) {
                console.error("Image analysis failed", err);
                showError(err.message || "OCR extraction or analysis failed. Please ensure the image is clear and try again.");
            }
        });
    }

    // --- Display Logic ---
    let loadingInterval;

    function showLoading() {
        document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
        document.getElementById('loading-spinner').classList.remove('hidden');
        document.getElementById('results-panel').classList.add('hidden');

        const alertBox = document.getElementById('error-alert');
        if (alertBox) alertBox.classList.add('hidden');

        // Cycle loading text
        const textElement = document.getElementById('loading-text');
        if (textElement) {
            const messages = ["Extracting text...", "Applying NLP models...", "Checking recruiter domains...", "Calculating risk vectors..."];
            let idx = 0;
            textElement.textContent = "Analyzing Content...";
            loadingInterval = setInterval(() => {
                textElement.textContent = messages[idx % messages.length];
                idx++;
            }, 1200);
        }
    }

    function hideLoading() {
        document.getElementById('loading-spinner').classList.add('hidden');
        if (loadingInterval) clearInterval(loadingInterval);
    }

    function showError(msg) {
        hideLoading();
        const alertBox = document.getElementById('error-alert');
        if (alertBox) {
            alertBox.classList.remove('hidden');
            document.getElementById('error-message').textContent = msg;
        }

        const activeTab = document.querySelector('.tab-btn.active').getAttribute('data-tab');
        document.getElementById(activeTab).classList.remove('hidden');
    }

    function animateScore(targetScore, elementId) {
        const el = document.getElementById(elementId);
        let start = 0;
        const duration = 1500; // ms
        const incrementTime = 20;
        const step = Math.max(1, targetScore / (duration / incrementTime));

        // Clear previous interval if any
        if (el.dataset.intervalId) clearInterval(parseInt(el.dataset.intervalId));

        const timer = setInterval(() => {
            start += step;
            if (start >= targetScore) {
                el.textContent = targetScore;
                clearInterval(timer);
                el.dataset.intervalId = "";
            } else {
                el.textContent = Math.floor(start);
            }
        }, incrementTime);
        el.dataset.intervalId = timer;
    }

    function displayResults(data, isImage = false) {
        hideLoading();
        const resultsPanel = document.getElementById('results-panel');
        resultsPanel.classList.remove('hidden');

        // Score
        const scoreCircle = document.getElementById('score-circle');
        animateScore(data.risk_score || 0, 'risk-score');

        scoreCircle.className = 'score-circle'; // reset

        const label = document.getElementById('prediction-label');
        label.textContent = data.prediction;
        label.style.color = 'var(--text-main)';

        setTimeout(() => {
            if (data.risk_score > 70) {
                scoreCircle.classList.add('score-danger');
                label.style.color = 'var(--danger)';
            } else if (data.risk_score > 35) {
                scoreCircle.classList.add('score-warn');
                label.style.color = 'var(--warning)';
            } else {
                scoreCircle.classList.add('score-safe');
                label.style.color = 'var(--success)';
            }
        }, 100);

        // Reasons
        const reasonsList = document.getElementById('reasons-list');
        reasonsList.innerHTML = '';
        data.reasons.forEach(r => {
            const li = document.createElement('li');
            li.textContent = r;
            reasonsList.appendChild(li);
        });

        // Keywords
        const kwContainer = document.getElementById('keywords-container');
        const kwTags = document.getElementById('keywords-tags');
        if (data.keywords_found && data.keywords_found.length > 0) {
            kwContainer.classList.remove('hidden');
            kwTags.innerHTML = '';
            data.keywords_found.forEach(kw => {
                const span = document.createElement('span');
                span.className = 'tag';
                span.textContent = kw;
                kwTags.appendChild(span);
            });
        } else {
            kwContainer.classList.add('hidden');
        }

        // Extracted Text
        const ocrContainer = document.getElementById('ocr-text-container');
        if (isImage && data.extracted_text) {
            ocrContainer.classList.remove('hidden');
            document.getElementById('ocr-text').textContent = data.extracted_text;
        } else {
            ocrContainer.classList.add('hidden');
        }
    }

    const resetBtn = document.getElementById('reset-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetScanner);
    }

    function resetScanner() {
        document.getElementById('results-panel').classList.add('hidden');
        const alertBox = document.getElementById('error-alert');
        if (alertBox) alertBox.classList.add('hidden');

        hideLoading();
        const activeTab = document.querySelector('.tab-btn.active').getAttribute('data-tab');
        document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
        document.getElementById(activeTab).classList.remove('hidden');
    }

    // --- Report Form Logic ---
    const reportForm = document.getElementById('report-form');
    if (reportForm) {
        reportForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const email = document.getElementById('report-email').value;
            const res = document.getElementById('report-result').value;
            const text = document.getElementById('report-text').value;
            const reason = document.getElementById('report-reason').value;

            try {
                await fetch('/api/report', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email, result: res, text, reason, score: 0 })
                });

                reportForm.reset();
                reportForm.classList.add('hidden');
                document.getElementById('report-success').classList.remove('hidden');
            } catch (e) {
                console.error("Report failed", e);
            }
        });
    }

    // --- Admin Dashboard Logic ---
    const addKeywordForm = document.getElementById('add-keyword-form');
    if (addKeywordForm) {
        addKeywordForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const keyword = document.getElementById('new-keyword').value;
            if (!keyword.trim()) return;

            try {
                const response = await fetch('/api/admin/keywords', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ keyword })
                });
                if (response.ok) {
                    window.location.reload(); // Quick refresh to show new tag
                } else {
                    alert("Failed to add keyword.");
                }
            } catch (err) {
                console.error("Error adding keyword", err);
            }
        });

        // Delete Keyword Logic
        const deleteBtns = document.querySelectorAll('.delete-kw-btn');
        deleteBtns.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const kwId = e.target.closest('.delete-kw-btn').getAttribute('data-id');
                if (!confirm("Are you sure you want to remove this keyword rule?")) return;

                try {
                    const response = await fetch(`/api/admin/keywords/${kwId}`, {
                        method: 'DELETE'
                    });
                    if (response.ok) {
                        window.location.reload();
                    } else {
                        alert("Failed to delete keyword.");
                    }
                } catch (err) {
                    console.error("Error deleting keyword", err);
                }
            });
        });

        // Delete Single Report Logic
        const deleteReportBtns = document.querySelectorAll('.delete-report-btn');
        deleteReportBtns.forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const reportId = e.target.closest('.delete-report-btn').getAttribute('data-id');
                if (!confirm("Are you sure you want to delete this report?")) return;

                try {
                    const response = await fetch(`/api/admin/reports/${reportId}`, {
                        method: 'DELETE'
                    });
                    if (response.ok) {
                        window.location.reload();
                    } else {
                        alert("Failed to delete report.");
                    }
                } catch (err) {
                    console.error("Error deleting report", err);
                }
            });
        });

        // Clear All Reports Logic
        const clearAllReportsBtn = document.getElementById('clear-all-reports-btn');
        if (clearAllReportsBtn) {
            clearAllReportsBtn.addEventListener('click', async () => {
                if (!confirm("WARNING: Are you sure you want to delete ALL reports? This action cannot be undone.")) return;

                try {
                    const response = await fetch('/api/admin/reports/all', {
                        method: 'DELETE'
                    });
                    if (response.ok) {
                        window.location.reload();
                    } else {
                        alert("Failed to clear reports.");
                    }
                } catch (err) {
                    console.error("Error clearing reports", err);
                }
            });
        }
    }
});
