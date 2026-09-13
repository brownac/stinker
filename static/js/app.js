// Dashboard interactivity

document.addEventListener('DOMContentLoaded', function() {
    // Manual Review Form
    const reviewForm = document.getElementById('reviewForm');
    const reviewMessage = document.getElementById('reviewMessage');
    
    if (reviewForm) {
        reviewForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const repo = document.getElementById('repo').value.trim();
            const prNumber = document.getElementById('pr_number').value.trim();
            
            // Validate inputs
            if (!repo || !prNumber) {
                showMessage(reviewMessage, 'Please fill in all fields', 'error');
                return;
            }
            
            if (!repo.includes('/')) {
                showMessage(reviewMessage, 'Repository format should be: owner/repo', 'error');
                return;
            }
            
            // Disable button during request
            const submitBtn = reviewForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Starting Review...';
            
            try {
                const response = await fetch('/api/review', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        repo: repo,
                        pr_number: parseInt(prNumber)
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showMessage(reviewMessage, `✅ ${data.message}. Review is processing in the background. Check back soon!`, 'success');
                    reviewForm.reset();
                    
                    // Refresh page after 3 seconds
                    setTimeout(() => {
                        location.reload();
                    }, 3000);
                } else {
                    showMessage(reviewMessage, `❌ Error: ${data.error || 'Failed to start review'}`, 'error');
                }
            } catch (error) {
                showMessage(reviewMessage, `❌ Error: ${error.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }
    
    // Analyze Repository Form
    const analyzeForm = document.getElementById('analyzeForm');
    const analyzeMessage = document.getElementById('analyzeMessage');
    
    if (analyzeForm) {
        analyzeForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const repo = document.getElementById('analyze_repo').value.trim();
            
            // Validate input
            if (!repo) {
                showMessage(analyzeMessage, 'Please enter a repository name', 'error');
                return;
            }
            
            if (!repo.includes('/')) {
                showMessage(analyzeMessage, 'Repository format should be: owner/repo', 'error');
                return;
            }
            
            // Disable button during request
            const submitBtn = analyzeForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Analyzing...';
            
            try {
                const response = await fetch('/api/analyze-repo', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        repo: repo
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    showMessage(analyzeMessage, `✅ ${data.message}. Analyzed ${data.data.files_analyzed} files.`, 'success');
                    analyzeForm.reset();
                } else {
                    showMessage(analyzeMessage, `❌ Error: ${data.error || 'Failed to analyze repository'}`, 'error');
                }
            } catch (error) {
                showMessage(analyzeMessage, `❌ Error: ${error.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }
    
    // Auto-refresh reviews every 30 seconds if on dashboard
    if (window.location.pathname === '/') {
        setInterval(function() {
            // Only refresh if user hasn't interacted recently
            const lastInteraction = localStorage.getItem('lastInteraction');
            const now = Date.now();
            
            if (!lastInteraction || (now - parseInt(lastInteraction)) > 30000) {
                location.reload();
            }
        }, 30000);
        
        // Track user interaction
        document.addEventListener('click', function() {
            localStorage.setItem('lastInteraction', Date.now().toString());
        });
    }
});

function showMessage(element, text, type) {
    element.textContent = text;
    element.className = `message ${type} show`;
    
    // Auto-hide after 5 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            element.classList.remove('show');
        }, 5000);
    }
}

// Health check indicator
async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        if (data.status === 'success') {
            console.log('✅ Service healthy:', data.data);
        } else {
            console.warn('⚠️ Service health check failed');
        }
    } catch (error) {
        console.error('❌ Health check error:', error);
    }
}

// Run health check on page load
checkHealth();
