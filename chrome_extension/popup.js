document.addEventListener('DOMContentLoaded', function () {
    const scanBtn = document.getElementById('scan-btn');
    const resultCard = document.getElementById('result-card');
    const loading = document.getElementById('loading');
    const errorMsg = document.getElementById('error-msg');

    // Connect to local Flask API (adjust URL for production)
    const API_URL = 'http://127.0.0.1:5000/api/analyze/url';

    scanBtn.addEventListener('click', async () => {
        scanBtn.style.display = 'none';
        loading.style.display = 'block';
        errorMsg.style.display = 'none';
        resultCard.style.display = 'none';

        try {
            // Get active tab URL
            let [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            let currentUrl = tab.url;

            document.getElementById('current-url').textContent = currentUrl;

            // Send request to AI Engine
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: currentUrl })
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }

            const data = await response.json();
            displayResults(data);

        } catch (err) {
            errorMsg.style.display = 'block';
            errorMsg.textContent = "Failed to connect to AI Engine. Make sure backend is running.";
            scanBtn.style.display = 'block';
            console.error(err);
        } finally {
            loading.style.display = 'none';
        }
    });

    function displayResults(data) {
        resultCard.style.display = 'block';
        const badge = document.getElementById('risk-badge');
        const typeEl = document.getElementById('scam-type');
        const reasonsContainer = document.getElementById('reasons-container');
        const reasonsList = document.getElementById('reasons-list');

        // Ensure accurate styling
        resultCard.className = 'status-card';
        badge.className = 'risk-badge';

        if (data.risk_score >= 60) {
            resultCard.classList.add('risk-high');
            badge.classList.add('badge-high');
            badge.textContent = `High Risk (${data.risk_score}%)`;
            typeEl.textContent = "⚠️ DANGER: Likely Phishing/Scam";
        } else if (data.risk_score >= 30) {
            resultCard.classList.add('risk-medium');
            badge.classList.add('badge-medium');
            badge.textContent = `Medium Risk (${data.risk_score}%)`;
            typeEl.textContent = "⚠️ Warning: Suspicious Activity";
        } else {
            resultCard.classList.add('risk-low');
            badge.classList.add('badge-low');
            badge.textContent = `Safe (${data.risk_score}%)`;
            typeEl.textContent = "✅ Legitimate Site";
        }

        // Populate reasons
        if (data.reasons && data.reasons.length > 0) {
            reasonsContainer.style.display = 'block';
            reasonsList.innerHTML = '';
            data.reasons.forEach(r => {
                const li = document.createElement('li');
                li.textContent = r;
                reasonsList.appendChild(li);
            });
        } else {
            reasonsContainer.style.display = 'none';
        }

        scanBtn.style.display = 'block';
        scanBtn.textContent = "Scan Again";
    }
});
