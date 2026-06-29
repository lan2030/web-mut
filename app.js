document.addEventListener('DOMContentLoaded', () => {
    // Initialize Lucide Icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // DOM Elements
    const cameraSelect = document.getElementById('cameraSelect');
    const switchCameraBtn = document.getElementById('switchCameraBtn');
    const startBtn = document.getElementById('startBtn');
    const scannerModal = document.getElementById('scannerModal');
    const modalCloseBtn = document.getElementById('modalCloseBtn');
    const reader = document.getElementById('reader');
    const scannerOverlay = document.getElementById('scannerOverlay');
    const imageUpload = document.getElementById('imageUpload');
    const fileInfo = document.getElementById('fileInfo');
    const scannerStatus = document.getElementById('scannerStatus');
    
    const resultCard = document.getElementById('resultCard');
    const resultPlaceholder = document.getElementById('resultPlaceholder');
    const resultContent = document.getElementById('resultContent');
    const resultText = document.getElementById('resultText');
    const resultType = document.getElementById('resultType');
    const resultTime = document.getElementById('resultTime');
    
    const copyBtn = document.getElementById('copyBtn');
    const openLinkBtn = document.getElementById('openLinkBtn');
    const shareBtn = document.getElementById('shareBtn');
    const searchBtn = document.getElementById('searchBtn');
    
    const clearHistoryBtn = document.getElementById('clearHistoryBtn');
    const exportHistoryBtn = document.getElementById('exportHistoryBtn');
    const historySearch = document.getElementById('historySearch');
    const historyPlaceholder = document.getElementById('historyPlaceholder');
    const historyList = document.getElementById('historyList');
    
    const toast = document.getElementById('toast');

    // App State
    let html5QrCode = null;
    let scannerActive = false;
    let history = JSON.parse(localStorage.getItem('omniscan_history') || '[]');

    // Initialize html5-qrcode
    try {
        html5QrCode = new Html5Qrcode("reader");
    } catch (e) {
        console.error("Failed to initialize Html5Qrcode: ", e);
        updateStatus('error', 'Init Failed');
    }

    // Load available cameras and populate select dropdown
    async function initCameraOptions() {
        // Add default options first
        cameraSelect.innerHTML = `
            <option value="environment">Rear Camera (Auto)</option>
            <option value="user">Front Camera (Auto)</option>
        `;
        switchCameraBtn.style.display = 'inline-flex';

        try {
            // Attempt to get cameras. If permission hasn't been granted yet,
            // this might fail or return empty labels, which is fine because we have default options.
            const devices = await Html5Qrcode.getCameras();
            if (devices && devices.length > 0) {
                // Clear and add specific cameras
                cameraSelect.innerHTML = '';
                let defaultCameraId = null;
                
                devices.forEach((device) => {
                    const option = document.createElement('option');
                    option.value = device.id;
                    option.text = device.label || `Camera ${cameraSelect.options.length + 1}`;
                    cameraSelect.appendChild(option);
                    
                    // Try to identify if this is a rear camera by looking for standard keywords
                    const label = (device.label || '').toLowerCase();
                    if (!defaultCameraId && (
                        label.includes('back') || 
                        label.includes('rear') || 
                        label.includes('environment') || 
                        label.includes('основная') || 
                        label.includes('задняя') ||
                        label.includes('камера 0')
                    )) {
                        defaultCameraId = device.id;
                    }
                });
                
                // If we found a rear camera, use it.
                // Fallback: use the last camera in the list (front cameras are typically first at index 0)
                if (defaultCameraId) {
                    cameraSelect.value = defaultCameraId;
                } else if (devices.length > 1) {
                    cameraSelect.value = devices[devices.length - 1].id;
                } else {
                    cameraSelect.value = devices[0].id;
                }

                // Show switch button only if there is more than 1 camera
                if (devices.length > 1) {
                    switchCameraBtn.style.display = 'inline-flex';
                } else {
                    switchCameraBtn.style.display = 'none';
                }
            } else {
                switchCameraBtn.style.display = 'none';
            }
        } catch (err) {
            // Permission not granted yet, defaults are active.
            console.log("Cameras listing delayed until camera permission is granted.");
        }
    }

    initCameraOptions();
    renderHistory();

    // Helper to update scanner status indicator
    function updateStatus(state, text) {
        scannerStatus.className = `status-badge ${state}`;
        const dot = scannerStatus.querySelector('.status-dot');
        const statusText = scannerStatus.querySelector('.status-text');
        statusText.textContent = text;
    }

    // Toast notification helper
    function showToast(message, isSuccess = true) {
        const toastIcon = toast.querySelector('.toast-icon');
        const toastMsg = toast.querySelector('.toast-message');
        
        toastMsg.textContent = message;
        if (isSuccess) {
            toastIcon.setAttribute('data-lucide', 'check-circle');
            toastIcon.style.color = 'var(--success)';
        } else {
            toastIcon.setAttribute('data-lucide', 'alert-circle');
            toastIcon.style.color = 'var(--danger)';
        }
        
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    // Start Scanner function
    async function startScanning() {
        if (!html5QrCode) return;

        const cameraValue = cameraSelect.value;
        // Determine whether to use faceMode object or direct device ID
        const cameraConfig = (cameraValue === 'environment' || cameraValue === 'user') 
            ? { facingMode: cameraValue } 
            : cameraValue;

        const config = {
            fps: 15,
            // Dynamic scanner box size based on container width
            qrbox: function(width, height) {
                const size = Math.min(width, height) * 0.75;
                return { width: Math.round(size), height: Math.round(size) };
            },
            aspectRatio: 1.333333 // 4:3 default aspect ratio
        };

        try {
            // UI state updates before starting
            startBtn.disabled = true;
            
            // Show the modal overlay
            scannerModal.style.display = 'flex';
            
            await html5QrCode.start(
                cameraConfig,
                config,
                onScanSuccess,
                onScanFailure
            );

            scannerActive = true;
            scannerOverlay.style.display = 'block';
            updateStatus('scanning', 'Scanning');
            
            // Re-query cameras if we didn't have permissions/labels earlier
            if (cameraSelect.options.length <= 2) {
                await initCameraOptions();
                cameraSelect.value = cameraValue;
            }
        } catch (err) {
            console.error("Error starting scanner: ", err);
            showToast("Failed to start camera. Check permissions.", false);
            updateStatus('error', 'Camera Error');
            
            // Revert UI states
            startBtn.disabled = false;
            scannerModal.style.display = 'none';
            scannerOverlay.style.display = 'none';
        }
    }

    // Stop Scanner function
    async function stopScanning() {
        if (!html5QrCode || !scannerActive) {
            scannerModal.style.display = 'none';
            startBtn.disabled = false;
            return;
        }

        try {
            await html5QrCode.stop();
            scannerActive = false;
            
            // Update UI elements
            startBtn.disabled = false;
            scannerModal.style.display = 'none';
            scannerOverlay.style.display = 'none';
            updateStatus('ready', 'Ready');
        } catch (err) {
            console.error("Error stopping scanner: ", err);
        }
    }

    // Success scan handler
    function onScanSuccess(decodedText, decodedResult) {
        // Haptic feedback (Vibrate 100ms)
        if (navigator.vibrate) {
            navigator.vibrate(100);
        }

        const format = decodedResult?.result?.format?.formatName || "QR_CODE";
        
        // Stop scanning to allow user to view results
        stopScanning().then(() => {
            displayResult(decodedText, format);
            addToHistory(decodedText, format);
            showToast("Code successfully scanned!");
        });
    }

    // Scan failure callback (called on every frame where no code is detected)
    function onScanFailure(error) {
        // We suppress this to avoid console spamming
    }

    // Display Scanned Results UI
    function displayResult(text, format) {
        resultPlaceholder.style.display = 'none';
        resultContent.style.display = 'flex';
        
        resultText.value = text;
        resultType.textContent = format.replace(/_/g, ' ');
        
        const now = new Date();
        resultTime.innerHTML = `<i data-lucide="clock"></i> Scanned at ${now.toLocaleTimeString()}`;

        // URL Check
        if (isValidUrl(text)) {
            openLinkBtn.style.display = 'inline-flex';
            openLinkBtn.href = text;
            
            // Hide product card if it is a standard URL
            document.getElementById('productCard').style.display = 'none';
        } else {
            openLinkBtn.style.display = 'none';
            
            // Query 1C API for products
            fetchProductDetails(text);
        }

        // Re-render Lucide icons for the dynamic parts
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        // Scroll results into view on mobile
        if (window.innerWidth <= 900) {
            resultCard.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    // Expose for testing
    window.omniScanTest = displayResult;

    // Scan from File Upload
    imageUpload.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        fileInfo.textContent = file.name;

        // Stop live scanner if it's active
        if (scannerActive) {
            await stopScanning();
        }

        try {
            updateStatus('scanning', 'Decoding File');
            const decodedText = await html5QrCode.scanFile(file, true);
            
            // Note: scanFile might not return format information directly, default to QR/Barcode
            displayResult(decodedText, "FILE_SCAN");
            addToHistory(decodedText, "FILE_SCAN");
            showToast("File successfully decoded!");
            updateStatus('ready', 'Ready');
        } catch (err) {
            console.error("Error decoding file: ", err);
            showToast("No valid barcode or QR code found.", false);
            updateStatus('error', 'Decode Error');
            fileInfo.textContent = "Drag and drop or browse image";
        }
    });

    // History Logic
    function addToHistory(text, format) {
        // Prevent duplicate consecutive scans if they are exactly the same within short window
        if (history.length > 0 && history[0].text === text && (Date.now() - history[0].id < 5000)) {
            return; 
        }

        const newItem = {
            id: Date.now(),
            text: text,
            type: format,
            time: new Date().toLocaleString()
        };

        history.unshift(newItem);
        localStorage.setItem('omniscan_history', JSON.stringify(history));
        renderHistory();
    }

    function deleteHistoryItem(id) {
        history = history.filter(item => item.id !== id);
        localStorage.setItem('omniscan_history', JSON.stringify(history));
        renderHistory();
        showToast("Item removed from history");
    }

    function clearHistory() {
        if (history.length === 0) return;
        if (confirm("Are you sure you want to clear your scanning history?")) {
            history = [];
            localStorage.removeItem('omniscan_history');
            renderHistory();
            showToast("History cleared");
        }
    }

    function renderHistory() {
        const filter = historySearch.value.toLowerCase();
        const filteredHistory = history.filter(item => 
            item.text.toLowerCase().includes(filter) || 
            item.type.toLowerCase().includes(filter)
        );

        if (filteredHistory.length === 0) {
            historyList.style.display = 'none';
            historyPlaceholder.style.display = 'flex';
            // Update placeholder text depending on filter
            historyPlaceholder.querySelector('p').textContent = 
                filter ? "No matching records found" : "No history items yet";
        } else {
            historyPlaceholder.style.display = 'none';
            historyList.style.display = 'flex';
            historyList.innerHTML = '';

            filteredHistory.forEach(item => {
                const li = document.createElement('li');
                li.className = 'history-item';
                
                const cleanType = item.type.replace(/_/g, ' ');
                
                li.innerHTML = `
                    <div class="history-item-main" style="cursor: pointer;">
                        <span class="history-item-title">${escapeHtml(item.text)}</span>
                        <div class="history-item-meta">
                            <span class="history-item-badge">${cleanType}</span>
                            <span>${item.time}</span>
                        </div>
                    </div>
                    <div class="history-item-actions">
                        <button class="btn-history-action copy" title="Copy Text">
                            <i data-lucide="copy"></i>
                        </button>
                        <button class="btn-history-action delete" title="Delete">
                            <i data-lucide="trash-2"></i>
                        </button>
                    </div>
                `;

                // Load to results on item click
                li.querySelector('.history-item-main').addEventListener('click', () => {
                    displayResult(item.text, item.type);
                });

                // Copy to clipboard from history
                li.querySelector('.copy').addEventListener('click', (e) => {
                    e.stopPropagation();
                    navigator.clipboard.writeText(item.text)
                        .then(() => showToast("Copied to clipboard!"))
                        .catch(() => showToast("Failed to copy", false));
                });

                // Delete from history
                li.querySelector('.delete').addEventListener('click', (e) => {
                    e.stopPropagation();
                    deleteHistoryItem(item.id);
                });

                historyList.appendChild(li);
            });

            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
        }
    }

    // Export history to CSV
    function exportHistory() {
        if (history.length === 0) {
            showToast("History is empty", false);
            return;
        }

        let csvContent = "data:text/csv;charset=utf-8,ID,Format,Scanned Text,Date Scanned\n";
        history.forEach(item => {
            const escapedText = `"${item.text.replace(/"/g, '""')}"`;
            csvContent += `${item.id},${item.type},${escapedText},"${item.time}"\n`;
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `omniscan_history_${Date.now()}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast("History exported successfully!");
    }

    // Action Event Listeners
    copyBtn.addEventListener('click', () => {
        navigator.clipboard.writeText(resultText.value)
            .then(() => showToast("Copied to clipboard!"))
            .catch(() => showToast("Failed to copy", false));
    });

    shareBtn.addEventListener('click', () => {
        const text = resultText.value;
        if (navigator.share) {
            navigator.share({
                title: 'Scanned Content via OmniScan',
                text: text,
                url: isValidUrl(text) ? text : undefined
            })
            .then(() => showToast("Shared successfully!"))
            .catch((err) => {
                if (err.name !== 'AbortError') {
                    showToast("Failed to share", false);
                }
            });
        } else {
            // Fallback: Copy to clipboard
            navigator.clipboard.writeText(text)
                .then(() => showToast("Share not supported. Text copied!", true))
                .catch(() => showToast("Failed to copy", false));
        }
    });

    searchBtn.addEventListener('click', () => {
        const query = encodeURIComponent(resultText.value);
        window.open(`https://www.google.com/search?q=${query}`, '_blank');
    });

    // Event Handlers
    startBtn.addEventListener('click', startScanning);
    modalCloseBtn.addEventListener('click', stopScanning);
    switchCameraBtn.addEventListener('click', async () => {
        if (cameraSelect.options.length <= 1) return;
        
        // Visual spin effect for the icon on click
        const icon = switchCameraBtn.querySelector('i');
        if (icon) {
            icon.style.transform = 'rotate(180deg)';
            icon.style.transition = 'transform 0.4s ease';
            setTimeout(() => { icon.style.transform = 'none'; }, 400);
        }
        
        const currentIndex = cameraSelect.selectedIndex;
        const nextIndex = (currentIndex + 1) % cameraSelect.options.length;
        cameraSelect.selectedIndex = nextIndex;
        
        if (scannerActive) {
            await stopScanning();
            await startScanning();
        }
    });
    clearHistoryBtn.addEventListener('click', clearHistory);
    exportHistoryBtn.addEventListener('click', exportHistory);
    historySearch.addEventListener('input', renderHistory);

    // Drag & Drop visual feedback for File Upload
    const fileLabel = document.querySelector('.file-upload-wrapper label');
    ['dragenter', 'dragover'].forEach(eventName => {
        fileLabel.addEventListener(eventName, (e) => {
            e.preventDefault();
            fileLabel.style.borderColor = 'var(--accent-secondary)';
            fileLabel.style.background = 'rgba(6, 182, 212, 0.1)';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        fileLabel.addEventListener(eventName, (e) => {
            e.preventDefault();
            fileLabel.style.borderColor = 'var(--card-border)';
            fileLabel.style.background = 'rgba(255, 255, 255, 0.05)';
        }, false);
    });

    fileLabel.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length) {
            imageUpload.files = files;
            // Trigger change event programmatically
            const event = new Event('change');
            imageUpload.dispatchEvent(event);
        }
    });

    // Helper functions
    async function fetchProductDetails(barcode) {
        const productCard = document.getElementById('productCard');
        const productLoading = document.getElementById('productLoading');
        const productError = document.getElementById('productError');
        const productInfoContent = document.getElementById('productInfoContent');
        const productStatus = document.getElementById('productStatus');
        
        productCard.style.display = 'flex';
        productLoading.style.display = 'flex';
        productError.style.display = 'none';
        productInfoContent.style.display = 'none';
        
        productStatus.className = 'badge';
        productStatus.textContent = 'Searching...';
        
        try {
            const response = await fetch(`/api/proxy?barcode=${encodeURIComponent(barcode)}`);
            
            if (!response.ok) {
                throw new Error(`API returned HTTP ${response.status}`);
            }
            
            const data = await response.json();
            productLoading.style.display = 'none';
            
            if (!data || !data.NomCode) {
                showProductError("Product not found in 1C database.");
                return;
            }
            
            productStatus.className = 'badge badge-success';
            productStatus.textContent = 'Found';
            
            document.getElementById('prodDescription').textContent = data.NomDescription || 'No description available';
            document.getElementById('prodArt').textContent = data.Art || '-';
            document.getElementById('prodCode').textContent = data.NomCode || '-';
            
            const formattedPrice = data.Price ? `${data.Price} ₸` : '0 ₸';
            document.getElementById('prodPrice').textContent = formattedPrice;
            document.getElementById('prodUnit').textContent = data.Unit || 'шт';
            
            const prodRestsBody = document.getElementById('prodRestsBody');
            const restsTable = document.getElementById('restsTable');
            const noRestsMessage = document.getElementById('noRestsMessage');
            
            prodRestsBody.innerHTML = '';
            
            if (data.Rests && data.Rests.length > 0) {
                restsTable.style.display = 'table';
                noRestsMessage.style.display = 'none';
                
                data.Rests.forEach(rest => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${escapeHtml(rest.Warehouse || 'Unknown')}</td>
                        <td><strong>${rest.Quantity || 0}</strong></td>
                    `;
                    prodRestsBody.appendChild(tr);
                });
            } else {
                restsTable.style.display = 'none';
                noRestsMessage.style.display = 'block';
            }
            
            productInfoContent.style.display = 'flex';
            
        } catch (err) {
            console.error("Error fetching product details: ", err);
            showProductError(`Failed to fetch product details: ${err.message || 'Unknown error'}`);
        }
    }

    function showProductError(message) {
        const productLoading = document.getElementById('productLoading');
        const productError = document.getElementById('productError');
        const productErrorMessage = document.getElementById('productErrorMessage');
        const productStatus = document.getElementById('productStatus');
        
        productLoading.style.display = 'none';
        productError.style.display = 'flex';
        productErrorMessage.textContent = message;
        
        productStatus.className = 'badge badge-danger';
        productStatus.textContent = 'Error';
    }

    function isValidUrl(string) {
        try {
            const url = new URL(string.trim());
            return url.protocol === "http:" || url.protocol === "https:";
        } catch (_) {
            return false;
        }
    }

    function escapeHtml(unsafe) {
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
    }
});
