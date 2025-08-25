// Global variables
let currentCrops = [];
let imageFile = null;

// DOM elements
const uploadForm = document.getElementById('uploadForm');
const imageInput = document.getElementById('imageInput');
const uploadArea = document.getElementById('uploadArea');
const imagePreview = document.getElementById('imagePreview');
const previewImg = document.getElementById('previewImg');
const changeImageBtn = document.getElementById('changeImage');
const cameraBtn = document.getElementById('cameraBtn');
const textInput = document.getElementById('textInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const loadingSection = document.getElementById('loadingSection');
const cropResults = document.getElementById('cropResults');
const cropList = document.getElementById('cropList');
const customCrop = document.getElementById('customCrop');
const addCropBtn = document.getElementById('addCropBtn');
const getRecommendations = document.getElementById('getRecommendations');
const recommendationsSection = document.getElementById('recommendationsSection');
const recommendationsList = document.getElementById('recommendationsList');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const retryBtn = document.getElementById('retryBtn');
const startOver = document.getElementById('startOver');
const saveResults = document.getElementById('saveResults');

// Initialize app
document.addEventListener('DOMContentLoaded', function () {
    initializeEventListeners();
    initializeScrollAnimations();
    initializeStaggerAnimations();
});

function initializeEventListeners() {
    // File upload events
    uploadArea.addEventListener('click', () => imageInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('drop', handleDrop);
    imageInput.addEventListener('change', handleFileSelect);
    changeImageBtn.addEventListener('click', () => imageInput.click());

    // Camera button
    cameraBtn.addEventListener('click', handleCameraCapture);

    // Form submission
    uploadForm.addEventListener('submit', handleFormSubmit);

    // Crop management
    addCropBtn.addEventListener('click', addCustomCrop);
    customCrop.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addCustomCrop();
    });

    // Recommendations
    getRecommendations.addEventListener('click', fetchRecommendations);

    // Action buttons
    startOver.addEventListener('click', resetApp);
    saveResults.addEventListener('click', saveResultsToFile);
    retryBtn.addEventListener('click', hideError);
}

function handleDragOver(e) {
    e.preventDefault();
    uploadArea.classList.add('bg-farm-light');
}

function handleDrop(e) {
    e.preventDefault();
    uploadArea.classList.remove('bg-farm-light');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        showError('Please select a valid image file (JPEG or PNG).');
        return;
    }

    imageFile = file;

    const reader = new FileReader();
    reader.onload = function (e) {
        previewImg.src = e.target.result;
        uploadArea.classList.add('hidden');
        imagePreview.classList.remove('hidden');
        analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

async function handleCameraCapture() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' }
        });

        // Create video element for camera preview
        const video = document.createElement('video');
        video.srcObject = stream;
        video.autoplay = true;
        video.playsInline = true;
        video.className = 'w-full h-64 object-cover rounded-lg';

        // Create capture button
        const captureBtn = document.createElement('button');
        captureBtn.type = 'button';
        captureBtn.className = 'mt-4 bg-farm-green text-white px-6 py-3 rounded-lg hover:bg-farm-dark transition-colors';
        captureBtn.innerHTML = '<i class="fas fa-camera mr-2"></i>Capture Photo';

        // Replace upload area with camera preview
        uploadArea.innerHTML = '';
        uploadArea.appendChild(video);
        uploadArea.appendChild(captureBtn);

        captureBtn.addEventListener('click', () => {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0);

            canvas.toBlob((blob) => {
                imageFile = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });

                previewImg.src = canvas.toDataURL();
                uploadArea.classList.add('hidden');
                imagePreview.classList.remove('hidden');
                analyzeBtn.disabled = false;

                // Stop camera stream
                stream.getTracks().forEach(track => track.stop());
            }, 'image/jpeg', 0.8);
        });

    } catch (error) {
        showError('Camera access denied or not available. Please use file upload instead.');
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();

    if (!imageFile) {
        showError('Please select an image first.');
        return;
    }

    showLoading();

    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('text', textInput.value);

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            displayCropResults(data.identified_crops);
        } else {
            showError(data.error || 'Failed to analyze image.');
        }
    } catch (error) {
        showError('Network error. Please check your connection and try again.');
    } finally {
        hideLoading();
    }
}

function displayCropResults(crops) {
    currentCrops = crops;
    cropList.innerHTML = '';

    crops.forEach((crop, index) => {
        const cropItem = createCropItem(crop, index);
        cropList.appendChild(cropItem);
    });

    cropResults.classList.remove('hidden');
    cropResults.scrollIntoView({ behavior: 'smooth' });
}

function createCropItem(crop, index) {
    const div = document.createElement('div');
    div.className = 'flex items-center justify-between p-6 bg-gradient-to-r from-white/60 to-farm-light/30 rounded-2xl border-2 border-gray-200/50 hover:border-farm-green/50 transition-all duration-300 transform hover:scale-102 shadow-lg backdrop-blur-sm animate-scale-in';

    div.innerHTML = `
        <div class="flex items-center space-x-4">
            <div class="bg-gradient-to-r from-farm-green to-farm-accent p-3 rounded-full">
                <i class="fas fa-leaf text-white text-lg"></i>
            </div>
            <input type="text" value="${crop.name}" 
                   class="crop-name bg-transparent border-none text-xl font-semibold text-gray-800 focus:outline-none focus:bg-white/80 focus:border-2 focus:border-farm-green focus:rounded-lg px-3 py-2 transition-all duration-300"
                   data-index="${index}">
        </div>
        <div class="flex space-x-3">
            <button class="confirm-crop bg-gradient-to-r from-green-100 to-green-200 text-green-700 px-4 py-2 rounded-xl text-sm font-semibold hover:from-green-200 hover:to-green-300 transition-all duration-300 transform hover:scale-105 shadow-md" data-index="${index}">
                <i class="fas fa-check mr-2"></i>Confirm
            </button>
            <button class="remove-crop bg-gradient-to-r from-red-100 to-red-200 text-red-700 px-4 py-2 rounded-xl text-sm font-semibold hover:from-red-200 hover:to-red-300 transition-all duration-300 transform hover:scale-105 shadow-md" data-index="${index}">
                <i class="fas fa-times mr-2"></i>Remove
            </button>
        </div>
    `;

    // Add event listeners
    const nameInput = div.querySelector('.crop-name');
    const confirmBtn = div.querySelector('.confirm-crop');
    const removeBtn = div.querySelector('.remove-crop');

    nameInput.addEventListener('blur', () => {
        currentCrops[index].name = nameInput.value;
    });

    confirmBtn.addEventListener('click', () => {
        confirmBtn.innerHTML = '<i class="fas fa-check-circle mr-1"></i>Confirmed';
        confirmBtn.classList.remove('bg-green-100', 'text-green-700');
        confirmBtn.classList.add('bg-green-500', 'text-white');
        confirmBtn.disabled = true;
    });

    removeBtn.addEventListener('click', () => {
        currentCrops.splice(index, 1);
        displayCropResults(currentCrops);
    });

    return div;
}

function addCustomCrop() {
    const cropName = customCrop.value.trim();
    if (cropName) {
        const newCrop = {
            name: cropName,
            id: `crop_custom_${Date.now()}`
        };
        currentCrops.push(newCrop);
        displayCropResults(currentCrops);
        customCrop.value = '';
    }
}

async function fetchRecommendations() {
    if (currentCrops.length === 0) {
        showError('Please confirm at least one crop before getting recommendations.');
        return;
    }

    showLoading();

    const cropNames = currentCrops.map(crop => crop.name);

    try {
        const response = await fetch('/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ crops: cropNames })
        });

        const data = await response.json();

        if (response.ok) {
            displayRecommendations(data.recommendations);
        } else {
            showError(data.error || 'Failed to get recommendations.');
        }
    } catch (error) {
        showError('Network error. Please check your connection and try again.');
    } finally {
        hideLoading();
    }
}

function displayRecommendations(recommendations) {
    recommendationsList.innerHTML = '';

    recommendations.forEach((rec, index) => {
        const recItem = document.createElement('div');
        recItem.className = 'bg-gradient-to-br from-white/70 via-farm-light/20 to-emerald-50/30 p-8 rounded-2xl border-2 border-farm-green/20 hover:border-farm-green/40 transform hover:scale-105 transition-all duration-500 shadow-xl hover:shadow-2xl backdrop-blur-sm animate-scale-in';
        recItem.style.animationDelay = `${index * 0.1}s`;

        recItem.innerHTML = `
            <div class="flex items-start space-x-6">
                <div class="relative">
                    <div class="absolute inset-0 bg-gradient-to-r from-farm-green to-farm-accent rounded-full blur-lg opacity-30"></div>
                    <div class="relative bg-gradient-to-r from-farm-green to-farm-accent text-white rounded-full w-12 h-12 flex items-center justify-center font-bold text-lg shadow-lg">
                        ${index + 1}
                    </div>
                </div>
                <div class="flex-1">
                    <h4 class="text-2xl font-bold text-gray-800 mb-4 flex items-center">
                        <div class="bg-gradient-to-r from-farm-green to-farm-accent p-2 rounded-lg mr-3">
                            <i class="fas fa-seedling text-white"></i>
                        </div>
                        <span class="gradient-text">${rec.plant}</span>
                    </h4>
                    <p class="text-gray-700 leading-relaxed text-lg bg-white/50 p-4 rounded-xl border border-gray-200/50">${rec.reason}</p>
                    <div class="mt-4 flex items-center text-sm text-gray-500">
                        <i class="fas fa-lightbulb text-farm-accent mr-2"></i>
                        <span>AI-powered recommendation</span>
                    </div>
                </div>
            </div>
        `;

        recommendationsList.appendChild(recItem);
    });

    recommendationsSection.classList.remove('hidden');
    recommendationsSection.scrollIntoView({ behavior: 'smooth' });
}

function showLoading() {
    loadingSection.classList.remove('hidden');
    analyzeBtn.disabled = true;
    getRecommendations.disabled = true;
}

function hideLoading() {
    loadingSection.classList.add('hidden');
    analyzeBtn.disabled = false;
    getRecommendations.disabled = false;
}

function showError(message) {
    errorMessage.textContent = message;
    errorSection.classList.remove('hidden');
    errorSection.scrollIntoView({ behavior: 'smooth' });
}

function hideError() {
    errorSection.classList.add('hidden');
}

function resetApp() {
    // Reset all variables
    currentCrops = [];
    imageFile = null;

    // Reset form
    uploadForm.reset();
    textInput.value = '';

    // Reset UI
    uploadArea.classList.remove('hidden');
    imagePreview.classList.add('hidden');
    cropResults.classList.add('hidden');
    recommendationsSection.classList.add('hidden');
    hideError();
    hideLoading();

    // Reset upload area content
    uploadArea.innerHTML = `
        <i class="fas fa-cloud-upload-alt text-farm-green text-5xl mb-4"></i>
        <p class="text-lg font-semibold text-gray-700 mb-2">Click to upload or drag and drop</p>
        <p class="text-gray-500">JPEG, PNG files supported</p>
    `;

    analyzeBtn.disabled = true;

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function saveResultsToFile() {
    const results = {
        timestamp: new Date().toISOString(),
        crops: currentCrops.map(crop => crop.name),
        recommendations: Array.from(recommendationsList.children).map(item => {
            const plant = item.querySelector('h4').textContent.trim();
            const reason = item.querySelector('p').textContent.trim();
            return { plant, reason };
        })
    };

    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `farm-recommendations-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Scroll animations
function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('revealed');
            }
        });
    }, observerOptions);

    // Observe all scroll-reveal elements
    document.querySelectorAll('.scroll-reveal').forEach(el => {
        observer.observe(el);
    });
}

// Stagger animations for elements
function initializeStaggerAnimations() {
    const staggerContainers = document.querySelectorAll('.stagger-animation');
    
    staggerContainers.forEach(container => {
        const children = container.children;
        Array.from(children).forEach((child, index) => {
            child.style.animationDelay = `${index * 0.1}s`;
        });
    });
}

// Enhanced mobile touch interactions
function addTouchFeedback(element) {
    element.addEventListener('touchstart', function() {
        this.style.transform = 'scale(0.98)';
    });
    
    element.addEventListener('touchend', function() {
        this.style.transform = '';
    });
}

// Add touch feedback to interactive elements
document.addEventListener('DOMContentLoaded', function() {
    const interactiveElements = document.querySelectorAll('button, .cursor-pointer');
    interactiveElements.forEach(addTouchFeedback);
});

// Smooth scroll for better UX
function smoothScrollTo(element) {
    element.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center',
        inline: 'nearest'
    });
}

// Enhanced error handling with animations
function showErrorWithAnimation(message) {
    errorMessage.textContent = message;
    errorSection.classList.remove('hidden');
    errorSection.classList.add('animate-scale-in');
    smoothScrollTo(errorSection);
}

// Enhanced loading with better animations
function showLoadingWithAnimation() {
    loadingSection.classList.remove('hidden');
    loadingSection.classList.add('animate-fade-in');
    analyzeBtn.disabled = true;
    getRecommendations.disabled = true;
}

// Responsive image handling
function handleResponsiveImage(img) {
    const maxWidth = window.innerWidth < 768 ? 300 : 400;
    const maxHeight = window.innerWidth < 768 ? 200 : 300;
    
    if (img.naturalWidth > maxWidth || img.naturalHeight > maxHeight) {
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        const ratio = Math.min(maxWidth / img.naturalWidth, maxHeight / img.naturalHeight);
        canvas.width = img.naturalWidth * ratio;
        canvas.height = img.naturalHeight * ratio;
        
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        return canvas.toDataURL('image/jpeg', 0.8);
    }
    
    return img.src;
}