// Global variables
let plants = {};
let currentEditingPlant = null;

// DOM elements
const plantsGrid = document.getElementById('plantsGrid');
const loadingIndicator = document.getElementById('loadingIndicator');
const searchInput = document.getElementById('searchInput');
const addPlantBtn = document.getElementById('addPlantBtn');
const plantModal = document.getElementById('plantModal');
const plantForm = document.getElementById('plantForm');
const modalTitle = document.getElementById('modalTitle');
const closeModal = document.getElementById('closeModal');
const cancelBtn = document.getElementById('cancelBtn');
const exportBtn = document.getElementById('exportBtn');
const importBtn = document.getElementById('importBtn');
const fileInput = document.getElementById('fileInput');

// Initialize the admin interface
document.addEventListener('DOMContentLoaded', function() {
    loadPlants();
    initializeEventListeners();
});

function initializeEventListeners() {
    // Search functionality
    searchInput.addEventListener('input', filterPlants);
    
    // Modal controls
    addPlantBtn.addEventListener('click', () => openModal());
    closeModal.addEventListener('click', () => closeModalHandler());
    cancelBtn.addEventListener('click', () => closeModalHandler());
    
    // Form submission
    plantForm.addEventListener('submit', handleFormSubmit);
    
    // Export/Import
    exportBtn.addEventListener('click', exportDatabase);
    importBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', importDatabase);
    
    // Close modal when clicking outside
    plantModal.addEventListener('click', (e) => {
        if (e.target === plantModal) {
            closeModalHandler();
        }
    });
}

async function loadPlants() {
    try {
        showLoading(true);
        const response = await fetch('/api/plants');
        const data = await response.json();
        
        if (response.ok) {
            plants = data.plants || {};
            renderPlants();
        } else {
            showError('Failed to load plants: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function renderPlants(filteredPlants = null) {
    const plantsToRender = filteredPlants || plants;
    plantsGrid.innerHTML = '';
    
    if (Object.keys(plantsToRender).length === 0) {
        plantsGrid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <i class="fas fa-seedling text-6xl text-gray-300 mb-4"></i>
                <p class="text-gray-500 text-lg">No plants found</p>
                <button onclick="openModal()" class="btn-primary px-6 py-3 rounded-lg mt-4 hover:opacity-90 transition-all duration-300">
                    <i class="fas fa-plus mr-2"></i>Add Your First Plant
                </button>
            </div>
        `;
        return;
    }
    
    Object.entries(plantsToRender).forEach(([plantId, plantData]) => {
        const plantCard = createPlantCard(plantId, plantData);
        plantsGrid.appendChild(plantCard);
    });
}

function createPlantCard(plantId, plantData) {
    const card = document.createElement('div');
    card.className = 'glass-effect rounded-2xl p-6 border border-white/30 hover:shadow-lg transition-all duration-300 transform hover:scale-105';
    
    const companionCount = plantData.companion_plants ? plantData.companion_plants.length : 0;
    const daysToMaturity = plantData.harvest_time?.days_to_maturity || 'N/A';
    const soilTypes = plantData.soil_requirements?.type ? plantData.soil_requirements.type.join(', ') : 'N/A';
    
    card.innerHTML = `
        <div class="flex justify-between items-start mb-4">
            <div>
                <h3 class="text-xl font-bold text-gray-800">${plantData.name || plantId}</h3>
                <p class="text-sm text-gray-600 italic">${plantData.scientific_name || ''}</p>
            </div>
            <div class="flex space-x-2">
                <button onclick="editPlant('${plantId}')" class="btn-warning px-3 py-2 rounded-lg text-sm hover:opacity-90 transition-all duration-300">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="deletePlant('${plantId}')" class="btn-danger px-3 py-2 rounded-lg text-sm hover:opacity-90 transition-all duration-300">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        
        <div class="space-y-3">
            <div class="flex items-center text-sm">
                <i class="fas fa-handshake text-green-600 mr-2"></i>
                <span class="text-gray-700">${companionCount} companion plants</span>
            </div>
            
            <div class="flex items-center text-sm">
                <i class="fas fa-calendar text-blue-600 mr-2"></i>
                <span class="text-gray-700">${daysToMaturity} days to maturity</span>
            </div>
            
            <div class="flex items-center text-sm">
                <i class="fas fa-mountain text-amber-600 mr-2"></i>
                <span class="text-gray-700">${soilTypes}</span>
            </div>
            
            ${plantData.benefits_provided ? `
                <div class="mt-3 p-3 bg-green-50 rounded-lg">
                    <p class="text-xs text-green-800 font-medium">Benefits:</p>
                    <p class="text-xs text-green-700">${plantData.benefits_provided.slice(0, 2).join(', ')}</p>
                </div>
            ` : ''}
        </div>
    `;
    
    return card;
}

function filterPlants() {
    const searchTerm = searchInput.value.toLowerCase();
    
    if (!searchTerm) {
        renderPlants();
        return;
    }
    
    const filteredPlants = {};
    Object.entries(plants).forEach(([plantId, plantData]) => {
        const searchableText = [
            plantId,
            plantData.name || '',
            plantData.scientific_name || '',
            ...(plantData.companion_plants || []),
            ...(plantData.benefits_provided || [])
        ].join(' ').toLowerCase();
        
        if (searchableText.includes(searchTerm)) {
            filteredPlants[plantId] = plantData;
        }
    });
    
    renderPlants(filteredPlants);
}

function openModal(plantId = null) {
    currentEditingPlant = plantId;
    
    if (plantId) {
        modalTitle.textContent = 'Edit Plant';
        populateForm(plants[plantId], plantId);
    } else {
        modalTitle.textContent = 'Add New Plant';
        plantForm.reset();
        document.getElementById('plantId').value = '';
    }
    
    plantModal.classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeModalHandler() {
    plantModal.classList.remove('show');
    document.body.style.overflow = '';
    currentEditingPlant = null;
    plantForm.reset();
}

function populateForm(plantData, plantId) {
    document.getElementById('plantId').value = plantId;
    document.getElementById('plantName').value = plantData.name || '';
    document.getElementById('scientificName').value = plantData.scientific_name || '';
    
    // Companion plants
    document.getElementById('companionPlants').value = (plantData.companion_plants || []).join(', ');
    document.getElementById('antagonisticPlants').value = (plantData.antagonistic_plants || []).join(', ');
    
    // Soil requirements
    if (plantData.soil_requirements) {
        document.getElementById('soilTypes').value = (plantData.soil_requirements.type || []).join(', ');
        document.getElementById('phMin').value = plantData.soil_requirements.ph_range ? plantData.soil_requirements.ph_range[0] : '';
        document.getElementById('phMax').value = plantData.soil_requirements.ph_range ? plantData.soil_requirements.ph_range[1] : '';
        document.getElementById('fertility').value = plantData.soil_requirements.fertility || '';
        document.getElementById('drainage').value = plantData.soil_requirements.drainage || '';
    }
    
    // Growing conditions
    if (plantData.growing_conditions) {
        document.getElementById('sunlight').value = plantData.growing_conditions.sunlight || '';
        document.getElementById('waterNeeds').value = plantData.growing_conditions.water_needs || '';
        document.getElementById('tempMin').value = plantData.growing_conditions.temperature_range ? plantData.growing_conditions.temperature_range[0] : '';
        document.getElementById('tempMax').value = plantData.growing_conditions.temperature_range ? plantData.growing_conditions.temperature_range[1] : '';
    }
    
    // Harvest information
    if (plantData.harvest_time) {
        document.getElementById('daysToMaturity').value = plantData.harvest_time.days_to_maturity || '';
        document.getElementById('season').value = plantData.harvest_time.season || '';
        document.getElementById('yieldDuration').value = plantData.harvest_time.yield_duration || '';
    }
    
    // Benefits
    document.getElementById('benefits').value = (plantData.benefits_provided || []).join(', ');
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(plantForm);
    const plantData = buildPlantData(formData);
    
    try {
        let response;
        let plantId = currentEditingPlant;
        
        if (currentEditingPlant) {
            // Update existing plant
            response = await fetch(`/api/plants/${currentEditingPlant}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(plantData)
            });
        } else {
            // Add new plant
            plantId = plantData.name.toLowerCase().replace(/\s+/g, '_');
            plantData.id = plantId;
            
            response = await fetch('/api/plants', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(plantData)
            });
        }
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess(currentEditingPlant ? 'Plant updated successfully!' : 'Plant added successfully!');
            closeModalHandler();
            await loadPlants(); // Reload the plants
        } else {
            showError('Failed to save plant: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

function buildPlantData(formData) {
    const data = {
        name: formData.get('name'),
        scientific_name: formData.get('scientific_name') || '',
        companion_plants: parseCommaSeparated(formData.get('companion_plants')),
        antagonistic_plants: parseCommaSeparated(formData.get('antagonistic_plants')),
        soil_requirements: {
            type: parseCommaSeparated(formData.get('soil_types')),
            ph_range: buildRange(formData.get('ph_min'), formData.get('ph_max')),
            fertility: formData.get('fertility') || '',
            drainage: formData.get('drainage') || ''
        },
        growing_conditions: {
            sunlight: formData.get('sunlight') || '',
            water_needs: formData.get('water_needs') || '',
            temperature_range: buildRange(formData.get('temp_min'), formData.get('temp_max'), true)
        },
        harvest_time: {
            days_to_maturity: parseInt(formData.get('days_to_maturity')) || null,
            season: formData.get('season') || '',
            yield_duration: formData.get('yield_duration') || ''
        },
        benefits_provided: parseCommaSeparated(formData.get('benefits'))
    };
    
    // Clean up empty values
    Object.keys(data).forEach(key => {
        if (typeof data[key] === 'object' && data[key] !== null) {
            Object.keys(data[key]).forEach(subKey => {
                if (data[key][subKey] === '' || data[key][subKey] === null) {
                    delete data[key][subKey];
                }
            });
            if (Object.keys(data[key]).length === 0) {
                delete data[key];
            }
        } else if (data[key] === '') {
            delete data[key];
        }
    });
    
    return data;
}

function parseCommaSeparated(value) {
    if (!value) return [];
    return value.split(',').map(item => item.trim()).filter(item => item.length > 0);
}

function buildRange(min, max, isNumber = false) {
    if (!min && !max) return null;
    const minVal = isNumber ? parseInt(min) : parseFloat(min);
    const maxVal = isNumber ? parseInt(max) : parseFloat(max);
    
    if (isNaN(minVal) && isNaN(maxVal)) return null;
    if (isNaN(minVal)) return [maxVal];
    if (isNaN(maxVal)) return [minVal];
    return [minVal, maxVal];
}

function editPlant(plantId) {
    openModal(plantId);
}

async function deletePlant(plantId) {
    if (!confirm(`Are you sure you want to delete "${plants[plantId]?.name || plantId}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/plants/${plantId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showSuccess('Plant deleted successfully!');
            await loadPlants(); // Reload the plants
        } else {
            showError('Failed to delete plant: ' + (result.error || 'Unknown error'));
        }
    } catch (error) {
        showError('Network error: ' + error.message);
    }
}

function exportDatabase() {
    const dataStr = JSON.stringify({ plants }, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `plant_database_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showSuccess('Database exported successfully!');
}

function importDatabase(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = async function(event) {
        try {
            const importedData = JSON.parse(event.target.result);
            
            if (!importedData.plants || typeof importedData.plants !== 'object') {
                showError('Invalid file format. Expected a JSON file with a "plants" object.');
                return;
            }
            
            if (confirm('This will replace your current database. Are you sure?')) {
                // Send the imported data to the server
                const response = await fetch('/api/plants/import', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(importedData)
                });
                
                if (response.ok) {
                    showSuccess('Database imported successfully!');
                    await loadPlants();
                } else {
                    showError('Failed to import database.');
                }
            }
        } catch (error) {
            showError('Invalid JSON file: ' + error.message);
        }
    };
    
    reader.readAsText(file);
    e.target.value = ''; // Reset file input
}

function showLoading(show) {
    loadingIndicator.style.display = show ? 'block' : 'none';
    plantsGrid.style.display = show ? 'none' : 'grid';
}

function showSuccess(message) {
    showNotification(message, 'success');
}

function showError(message) {
    showNotification(message, 'error');
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
    
    if (type === 'success') {
        notification.className += ' bg-green-500 text-white';
        notification.innerHTML = `<i class="fas fa-check-circle mr-2"></i>${message}`;
    } else {
        notification.className += ' bg-red-500 text-white';
        notification.innerHTML = `<i class="fas fa-exclamation-circle mr-2"></i>${message}`;
    }
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Animate out and remove
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}