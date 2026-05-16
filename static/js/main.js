document.addEventListener('DOMContentLoaded', () => {
    const videoUrlInput = document.getElementById('videoUrl');
    const getBtn = document.getElementById('getBtn');
    const btnText = document.getElementById('btnText');
    const btnIcon = document.getElementById('btnIcon');
    const btnLoader = document.getElementById('btnLoader');
    const resultsSection = document.getElementById('resultsSection');
    const errorMessage = document.getElementById('errorMessage');

    getBtn.addEventListener('click', handleExtract);

    // Also support Enter key
    videoUrlInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleExtract();
    });

    async function handleExtract() {
        const url = videoUrlInput.value.trim();
        
        if (!url) {
            showError('Please paste a valid URL.');
            return;
        }

        // Reset UI
        hideError();
        resultsSection.classList.add('hidden');
        setLoading(true);

        try {
            const response = await fetch('/api/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const data = await response.json();

            if (data.success) {
                renderResults(data);
            } else {
                showError(data.error || 'Failed to extract video info.');
            }
        } catch (error) {
            showError('An error occurred while connecting to the server.');
            console.error(error);
        } finally {
            setLoading(false);
        }
    }

    function renderResults(data) {
        // Escape quotes to prevent breaking HTML attributes
        const safeTitle = (data.title || 'ReelFetch_Video').replace(/"/g, '&quot;');
        
        resultsSection.innerHTML = `
            <div class="glass-panel p-6 rounded-3xl flex flex-col md:flex-row gap-8 animate-in">
                <div class="w-full md:w-80 shrink-0 aspect-video rounded-2xl overflow-hidden border border-white/5 bg-black/20">
                    <img src="${data.thumbnail}" alt="${safeTitle}" class="w-full h-full object-cover" onerror="this.src='https://via.placeholder.com/320x180?text=No+Thumbnail'">
                </div>
                <div class="flex-grow flex flex-col justify-center space-y-4">
                    <div>
                        <h2 class="text-2xl font-bold text-on-surface font-headline leading-tight">${safeTitle}</h2>
                        <p class="text-sm text-on-surface-variant font-body mt-1">
                            Uploaded by <span class="text-primary font-semibold">${data.uploader || 'Unknown'}</span> • ${formatDuration(data.duration)}
                        </p>
                    </div>
                    <div class="flex flex-wrap gap-3 mt-4">
                        ${data.url ? `
                            <button data-url="${data.url}" data-title="${safeTitle}" class="download-btn bg-primary text-on-primary px-6 py-3 rounded-xl font-bold text-sm hover:brightness-110 transition-all flex items-center gap-2">
                                <span class="material-symbols-outlined text-sm">download</span>
                                <span>Download Best Quality</span>
                            </button>
                        ` : ''}
                        ${data.formats.filter(f => f.resolution).slice(0, 5).map(f => `
                            <button data-url="${f.url}" data-title="${safeTitle}_${f.resolution}" class="download-btn glass-panel hover:bg-white/10 px-4 py-3 rounded-xl text-sm font-medium transition-all flex items-center gap-2">
                                <span>${f.resolution} (${f.ext})</span>
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // Force download logic
    resultsSection.addEventListener('click', async (e) => {
        const btn = e.target.closest('.download-btn');
        if (!btn) return;
        
        e.preventDefault();
        const url = btn.dataset.url;
        const title = btn.dataset.title;
        
        // Show loading state on button
        const originalHtml = btn.innerHTML;
        btn.innerHTML = `<div class="loader w-4 h-4 border-2 border-t-white/80 border-white/20 rounded-full animate-spin"></div> <span>Downloading...</span>`;
        btn.style.pointerEvents = 'none';
        btn.style.opacity = '0.8';
        
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Network response was not ok');
            
            const blob = await response.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = blobUrl;
            // Clean filename
            a.download = title.replace(/[^a-z0-9_ -]/gi, '').trim() + '.mp4';
            
            document.body.appendChild(a);
            a.click();
            
            window.URL.revokeObjectURL(blobUrl);
            document.body.removeChild(a);
        } catch (err) {
            console.error('Direct download blocked by CORS, opening in new tab instead.', err);
            // Fallback: If CORS blocks the fetch, open it in a new tab where they can right-click -> save
            window.open(url, '_blank');
        } finally {
            // Restore button
            btn.innerHTML = originalHtml;
            btn.style.pointerEvents = 'auto';
            btn.style.opacity = '1';
        }
    });


    function setLoading(isLoading) {
        if (isLoading) {
            getBtn.disabled = true;
            btnText.classList.add('hidden');
            btnIcon.classList.add('hidden');
            btnLoader.classList.remove('hidden');
        } else {
            getBtn.disabled = false;
            btnText.classList.remove('hidden');
            btnIcon.classList.remove('hidden');
            btnLoader.classList.add('hidden');
        }
    }

    function showError(msg) {
        errorMessage.textContent = msg;
        errorMessage.classList.remove('hidden');
    }

    function hideError() {
        errorMessage.classList.add('hidden');
    }

    function formatDuration(seconds) {
        if (!seconds) return 'N/A';
        const hrs = Math.floor(seconds / 3600);
        const mins = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        return hrs > 0 
            ? `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
            : `${mins}:${secs.toString().padStart(2, '0')}`;
    }
});
