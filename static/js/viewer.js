import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import { OBJExporter } from 'three/addons/exporters/OBJExporter.js';

// Scene setup
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a2e);
scene.fog = new THREE.Fog(0x1a1a2e, 200, 1000);

// Camera - configured for Z-up, Y-forward coordinate system
const camera = new THREE.PerspectiveCamera(
    60,
    window.innerWidth / window.innerHeight,
    0.1,
    2000
);
// Position camera: looking toward +Y (forward/north) with Z as up
camera.position.set(200, -200, 200);
camera.up.set(0, 0, 1); // Set Z as up vector

// Renderer
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.getElementById('container').appendChild(renderer.domElement);

// Controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.05;
controls.screenSpacePanning = true;
controls.minDistance = 10;
controls.maxDistance = 1000;

// Lights
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);

const sunLight = new THREE.DirectionalLight(0xffffff, 0.8);
sunLight.position.set(100, 200, 100);
sunLight.castShadow = true;
sunLight.shadow.camera.left = -500;
sunLight.shadow.camera.right = 500;
sunLight.shadow.camera.top = 500;
sunLight.shadow.camera.bottom = -500;
sunLight.shadow.mapSize.width = 2048;
sunLight.shadow.mapSize.height = 2048;
scene.add(sunLight);

const fillLight = new THREE.DirectionalLight(0x64ffda, 0.3);
fillLight.position.set(-100, 50, -100);
scene.add(fillLight);

// Ground plane (XY plane in Z-up system)
const groundGeometry = new THREE.PlaneGeometry(2000, 2000);
const groundMaterial = new THREE.MeshStandardMaterial({
    color: 0x16213e,
    roughness: 0.8,
    metalness: 0.2
});
const ground = new THREE.Mesh(groundGeometry, groundMaterial);
// No rotation needed - plane is already in XY, we just set the Z position
ground.position.z = -35; // Ground level below the model
ground.receiveShadow = true;
scene.add(ground);

// Grid (horizontal in XY plane)
const gridHelper = new THREE.GridHelper(1000, 50, 0x64ffda, 0x2a2a4e);
gridHelper.rotation.x = Math.PI / 2; // Rotate to XY plane
gridHelper.position.z = -34.9;
scene.add(gridHelper);

// State management
let metadata = null;
let allObjects = [];  // For UI list (array of objects)
let objectMeshMap = {};  // For mesh tracking by ID: { objectId: [mesh1, mesh2, ...] }
let selectedMesh = null;
let hoveredMesh = null;
let modelGroup = null;
const originalMaterials = new Map();

// Raycaster for 3D picking and hovering
const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();
let isMouseDown = false;

// Populate object list
function populateObjectList(objects) {
    const listContainer = document.getElementById('object-items');
    const listCount = document.getElementById('list-count');

    listContainer.innerHTML = '';
    listCount.textContent = objects.length;

    objects.forEach(obj => {
        const item = document.createElement('div');
        item.className = 'object-item';
        item.dataset.id = obj.id;

        // Truncate long names
        const displayName = obj.metadata?.name || obj.name || obj.id;
        const truncatedName = displayName.length > 35 ?
            displayName.substring(0, 35) + '...' : displayName;

        item.innerHTML = `
            <div class="object-name">${truncatedName}</div>
            <div class="object-type">${obj.element_type || obj.type}</div>
            <div class="object-stats">${obj.polygon_count || obj.polygonCount} polygons</div>
        `;

        item.addEventListener('click', () => selectObject(obj.id));
        listContainer.appendChild(item);
    });
}

// Search functionality
document.getElementById('search-box').addEventListener('input', (e) => {
    const query = e.target.value.toLowerCase();
    const filtered = allObjects.filter(obj => {
        const name = (obj.metadata?.name || obj.name || obj.id).toLowerCase();
        const type = (obj.element_type || obj.type).toLowerCase();
        return name.includes(query) || type.includes(query) || obj.id.toLowerCase().includes(query);
    });
    populateObjectList(filtered);
});

// Select object
function selectObject(objectId, objData = null, clickedMesh = null) {
    // Clear previous selection highlighting
    clearSelection();
    clearHover();

    // Store the clicked mesh
    selectedMesh = clickedMesh;

    // Update list selection
    document.querySelectorAll('.object-item').forEach(item => {
        item.classList.toggle('selected', item.dataset.id === objectId);
    });

    // Highlight the clicked mesh only
    if (clickedMesh) {
        highlightObject(clickedMesh);
    }

    // Find object data if not provided
    if (!objData) {
        objData = allObjects.find(o => o.id === objectId);
    }
    if (!objData) return;

    // Show attribute panel
    displayAttributes(objData);
}

// Highlight object in 3D (single mesh only)
function highlightObject(mesh) {
    if (!mesh) return;

    // Create highlight material (bright purple)
    const highlightMaterial = new THREE.MeshStandardMaterial({
        color: 0xaa55ff,
        emissive: 0x5500aa,
        emissiveIntensity: 0.5,
        roughness: 0.3,
        metalness: 0.1
    });

    // Apply highlight to this mesh only
    mesh.material = highlightMaterial;
}

// Clear all selections
function clearSelection() {
    if (selectedMesh) {
        // Restore original material
        const original = originalMaterials.get(selectedMesh);
        if (original) {
            selectedMesh.material = original.clone();
        }
        selectedMesh = null;
    }
}

// Display attributes
function displayAttributes(objData) {
    const panel = document.getElementById('attribute-panel');
    const title = document.getElementById('panel-title');
    const content = document.getElementById('panel-content');

    // Get building data if available
    const buildingId = objData.buildingId;
    const buildingData = buildingId && metadata?.buildings ? metadata.buildings[buildingId] : null;

    if (buildingData) {
        title.textContent = `Building: ${buildingId}`;
    } else {
        title.textContent = objData.metadata?.name || objData.name || objData.id;
    }

    let html = '<table class="attribute-table">';

    // Building info if available
    if (buildingData) {
        html += '<tr style="border-bottom: 2px solid rgba(100, 255, 218, 0.2);"><td colspan="2" style="color: #64ffda; font-weight: bold; padding-top: 10px; padding-bottom: 10px;">🏢 Building Information</td></tr>';
        html += `<tr><td>Building ID</td><td>${buildingData.id}</td></tr>`;

        if (buildingData.measuredHeight !== null && buildingData.measuredHeight !== undefined) {
            html += `<tr><td>Measured Height</td><td>${buildingData.measuredHeight} m</td></tr>`;
        }
        if (buildingData.storeysAboveGround !== null && buildingData.storeysAboveGround !== undefined) {
            html += `<tr><td>Storeys Above Ground</td><td>${buildingData.storeysAboveGround}</td></tr>`;
        }
        if (buildingData.storeysBelowGround !== null && buildingData.storeysBelowGround !== undefined) {
            html += `<tr><td>Storeys Below Ground</td><td>${buildingData.storeysBelowGround}</td></tr>`;
        }
        html += '<tr style="border-bottom: 2px solid rgba(100, 255, 218, 0.2);"><td colspan="2" style="color: #64ffda; font-weight: bold; padding-top: 10px; padding-bottom: 10px;">🔷 Surface Details</td></tr>';
    }

    // Surface info
    html += `<tr><td>Surface ID</td><td style="font-size: 11px; word-break: break-all;">${objData.id}</td></tr>`;
    html += `<tr><td>Surface Name</td><td>${objData.metadata?.name || objData.name || 'N/A'}</td></tr>`;
    html += `<tr><td>Surface Type</td><td>${objData.element_type || objData.type}</td></tr>`;
    html += `<tr><td>Polygons</td><td>${objData.polygon_count || objData.polygonCount}</td></tr>`;

    html += '</table>';
    html += '<button class="fly-to-btn" onclick="flyToObject()">🎯 Fly To Object</button>';

    content.innerHTML = html;
    panel.classList.add('visible');
}

// Fly to object
window.flyToObject = function () {
    // Get the first selected object (or the only one)
    const selectedObjectId = selectedMesh?.userData?.objectId; // Use selectedMesh directly
    if (!selectedObjectId) return;

    // Find the mesh by checking our stored meshes
    const meshes = objectMeshMap[selectedObjectId];
    if (!meshes || meshes.length === 0) {
        console.warn('Mesh not found for:', selectedObjectId);
        return;
    }

    // Use the first mesh to calculate the bounding box
    const targetMesh = meshes[0];

    // Calculate target position
    const box = new THREE.Box3().setFromObject(targetMesh.parent || targetMesh);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);

    // Calculate camera position (offset by object size)
    const targetPosition = new THREE.Vector3(
        center.x + maxDim * 2,
        center.y - maxDim * 2,
        center.z + maxDim * 1.5
    );

    // Smooth camera animation
    animateCamera(targetPosition, center, 1500);
};

// Animate camera
function animateCamera(targetPos, targetLookAt, duration) {
    const startPos = camera.position.clone();
    const startLookAt = controls.target.clone();
    const startTime = Date.now();

    function update() {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease in-out cubic
        const eased = progress < 0.5
            ? 4 * progress * progress * progress
            : 1 - Math.pow(-2 * progress + 2, 3) / 2;

        // Interpolate position
        camera.position.lerpVectors(startPos, targetPos, eased);
        controls.target.lerpVectors(startLookAt, targetLookAt, eased);
        controls.update();

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    update();
}

// Toggle object list
document.getElementById('toggle-sidebar').addEventListener('click', () => {
    document.getElementById('object-list').classList.toggle('visible');
});

// Close attribute panel
document.getElementById('close-panel').addEventListener('click', () => {
    document.getElementById('attribute-panel').classList.remove('visible');
    clearSelection();
    document.querySelectorAll('.object-item').forEach(item => {
        item.classList.remove('selected');
    });
});

// Clear hover effect
function clearHover() {
    if (hoveredMesh && hoveredMesh !== selectedMesh) {
        const original = originalMaterials.get(hoveredMesh);
        if (original) {
            hoveredMesh.material = original.clone();
        }
    }
    hoveredMesh = null;
}

// Handle mouse move for hover (THROTTLED for performance)
let lastHoverTime = 0;
const HOVER_THROTTLE_MS = 50;  // Only update hover every 50ms

function onMouseMove(event) {
    const now = Date.now();
    if (isMouseDown || (now - lastHoverTime < HOVER_THROTTLE_MS)) return; // Skip if dragging or too soon
    lastHoverTime = now;

    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(scene.children, true);

    if (intersects.length > 0) {
        const mesh = intersects[0].object;
        const objectId = mesh.userData.objectId; // Corrected from clickedMesh.userData.objectId

        if (objectId && mesh !== hoveredMesh && mesh !== selectedMesh) {
            // Clear previous hover
            clearHover();

            // Apply hover effect to this mesh only
            hoveredMesh = mesh;
            const hoverMaterial = new THREE.MeshStandardMaterial({
                color: 0xffdd00,
                emissive: 0x886600,
                emissiveIntensity: 0.3,
                roughness: 0.4,
                metalness: 0.1
            });
            mesh.material = hoverMaterial;
            renderer.domElement.style.cursor = 'pointer';
        } else if (!objectId || mesh === selectedMesh) {
            // If no objectId or it's the selected mesh, clear hover
            clearHover();
            renderer.domElement.style.cursor = 'default';
        }
    } else {
        clearHover();
        renderer.domElement.style.cursor = 'default';
    }
}

// 3D object click handler
function onCanvasClick(event) {
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects(scene.children, true);

    if (intersects.length > 0) {
        const clickedMesh = intersects[0].object;
        const objectId = clickedMesh.userData.objectId;

        if (objectId) {
            // DEBUG: Log what we're looking for
            console.log('=== CLICK DEBUG ===');
            console.log('Clicked objectId:', objectId);
            console.log('Metadata exists:', !!metadata);
            if (metadata) {
                console.log('Metadata keys:', Object.keys(metadata));
                console.log('Has objects key:', !!metadata.objects);
                if (metadata.objects) {
                    console.log('Total in metadata:', Object.keys(metadata.objects).length);
                    console.log('Found in metadata:', !!metadata.objects[objectId]);
                }
            }

            // Look up in objects (new metadata structure)
            let objData = null;

            if (metadata && metadata.objects && metadata.objects[objectId]) {
                // Found in objects
                const obj = metadata.objects[objectId];
                objData = {
                    id: objectId,
                    element_type: obj.element_type || 'Unknown',
                    polygon_count: obj.polygon_count || 0,
                    metadata: obj.metadata || { name: objectId }
                };
            }

            if (objData) {
                selectObject(objectId, objData, clickedMesh);
                console.log('✅ Click successful!');
            } else {
                console.warn('❌ Clicked object not in metadata:', objectId);
            }
        } else {
            console.log('Clicked mesh has no objectId in userData');
        }
    }
}

// Mouse events for hover
renderer.domElement.addEventListener('mousemove', onMouseMove, false);
renderer.domElement.addEventListener('mousedown', () => { isMouseDown = true; }, false);
renderer.domElement.addEventListener('mouseup', () => { isMouseDown = false; }, false);
renderer.domElement.addEventListener('click', onCanvasClick, false);

// Current session management
let currentSession = null;
const BACKEND_URL = 'https://citygml-viewer-6qyvfku6xq-et.a.run.app';

// Upload Modal Functions
function openUploadModal() {
    document.getElementById('upload-modal').classList.add('active');
    document.getElementById('upload-status').innerHTML = '';
    document.getElementById('upload-status').className = 'upload-status';
    document.getElementById('drop-zone').style.display = 'block';
    document.getElementById('upload-progress').style.display = 'none';
}

function closeUploadModal() {
    document.getElementById('upload-modal').classList.remove('active');
    document.getElementById('file-input').value = '';
}

// Add event listeners for modal buttons
document.getElementById('close-upload').addEventListener('click', closeUploadModal);
document.getElementById('browse-files-btn').addEventListener('click', () => {
    document.getElementById('file-input').click();
});
document.getElementById('fly-btn').addEventListener('click', () => {
    window.flyToObject();
});

// Drag and drop handlers
const dropZone = document.getElementById('drop-zone');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

// File input handler
document.getElementById('file-input').addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileUpload(e.target.files[0]);
    }
});

// Handle file upload and conversion
async function handleFileUpload(file) {
    // Validate file
    if (!file.name.toLowerCase().endsWith('.gml') && !file.name.toLowerCase().endsWith('.xml')) {
        showUploadStatus('error', 'Invalid file type. Please upload a .gml or .xml file.');
        return;
    }

    // Show progress
    document.getElementById('drop-zone').style.display = 'none';
    document.getElementById('upload-progress').style.display = 'block';
    updateProgress(0, 'Uploading file...');

    try {
        // Create form data
        const formData = new FormData();
        formData.append('file', file);

        // Upload and convert
        updateProgress(30, 'Optimizing 3D Data...');

        const response = await fetch(`${BACKEND_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }

        const result = await response.json();
        updateProgress(80, 'Loading model...');

        // Cleanup previous session if exists
        if (currentSession) {
            await cleanupSession(currentSession);
        }

        // Store new session
        currentSession = result.session_id;

        updateProgress(90, 'Loading model...');

        // Unload current model first
        unloadModel();

        // Load the converted GLB model
        // Pass the result object directly - it contains files.glb and files.metadata
        await loadModel(result);

        updateProgress(100, 'Complete!');
        showUploadStatus('success', `✅ Successfully loaded: ${file.name}`);

        // Close modal after a delay
        setTimeout(() => {
            closeUploadModal();
        }, 2000);

    } catch (error) {
        console.error('Upload error:', error);
        showUploadStatus('error', `❌ Error: ${error.message}`);
        document.getElementById('upload-progress').style.display = 'none';
        document.getElementById('drop-zone').style.display = 'block';
    }
}

function updateProgress(percent, text) {
    const fill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    fill.style.width = percent + '%';
    progressText.textContent = text || `${percent}%`;
}

function showUploadStatus(type, message) {
    const status = document.getElementById('upload-status');
    status.className = `upload-status ${type}`;
    status.textContent = message;
}

// Cleanup session on backend
async function cleanupSession(sessionId) {
    if (!sessionId) return;

    try {
        await fetch(`${BACKEND_URL}/cleanup/${sessionId}`, {
            method: 'DELETE'
        });
        console.log('Session cleaned up:', sessionId);
    } catch (error) {
        console.error('Cleanup error:', error);
    }
}

// Export Functions
function downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
}

function exportAsGLB() {
    if (!modelGroup) {
        alert('No model loaded to export!');
        return;
    }

    const exporter = new GLTFExporter();
    exporter.parse(
        modelGroup,
        (result) => {
            const blob = new Blob([result], { type: 'application/octet-stream' });
            const filename = currentSession ? `model_${currentSession}.glb` : 'model.glb';
            downloadFile(blob, filename);
            console.log('✅ Exported as GLB');
        },
        (error) => {
            console.error('GLB export error:', error);
            alert('Export failed! Check console for details.');
        },
        { binary: true }
    );
}

function exportAsOBJ() {
    if (!modelGroup) {
        alert('No model loaded to export!');
        return;
    }

    const exporter = new OBJExporter();
    const result = exporter.parse(modelGroup);
    const blob = new Blob([result], { type: 'text/plain' });
    const filename = currentSession ? `model_${currentSession}.obj` : 'model.obj';
    downloadFile(blob, filename);
    console.log('✅ Exported as OBJ');
}

// DAE/Collada export not available in Three.js r160
// function exportAsDAE() {
//     if (!modelGroup) {
//         alert('No model loaded to export!');
//         return;
//     }
//     const exporter = new ColladaExporter();
//     const result = exporter.parse(modelGroup);
//     const blob = new Blob([result.data], { type: 'application/xml' });
//     const filename = currentSession ? `model_${currentSession}.dae` : 'model.dae';
//     downloadFile(blob, filename);
//     console.log('✅ Exported as DAE (Collada)');
// }

// Export dropdown toggle
const exportBtn = document.getElementById('export-btn');
const exportMenu = document.getElementById('export-menu');

exportBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    exportMenu.classList.toggle('show');
});

// Close dropdown when clicking outside
document.addEventListener('click', () => {
    exportMenu.classList.remove('show');
});

// Export button handlers
document.getElementById('export-glb').addEventListener('click', exportAsGLB);
document.getElementById('export-obj').addEventListener('click', exportAsOBJ);
// document.getElementById('export-dae').addEventListener('click', exportAsDAE); // Disabled - not available

// Event listeners
document.getElementById('upload-btn').addEventListener('click', openUploadModal);
document.getElementById('unload-model-btn').addEventListener('click', async () => {
    // Cleanup backend session
    if (currentSession) {
        await cleanupSession(currentSession);
        currentSession = null;
    }
    unloadModel();
});

// Unload current model
function unloadModel() {
    // Remove model from scene first
    if (modelGroup) {
        scene.remove(modelGroup);

        // Dispose geometry and materials
        modelGroup.traverse((obj) => {
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) {
                if (Array.isArray(obj.material)) {
                    obj.material.forEach(mat => mat.dispose());
                } else {
                    obj.material.dispose();
                }
            }
        });
    }

    // Clear state
    metadata = null;
    allObjects = [];
    objectMeshMap = {};
    selectedMesh = null;
    hoveredMesh = null;
    modelGroup = null;
    originalMaterials.clear();

    // Clear UI
    document.getElementById('attribute-panel').classList.remove('visible');
    document.getElementById('object-list').classList.remove('visible');
    document.getElementById('object-items').innerHTML = '';
    document.getElementById('list-count').textContent = '0';
    document.getElementById('search-box').value = '';
    document.getElementById('info').style.display = 'none';
    document.getElementById('loading').style.display = 'block';
    document.getElementById('loading').innerHTML = '<div class="spinner"></div><div>No model loaded</div>';

    console.log('Model unloaded successfully');
}

// Load model from selector
function loadSelectedModel() {
    const selector = document.getElementById('model-selector');
    const modelName = selector.value;

    if (!modelName) return;

    // Unload current model first
    unloadModel();

    // Update file paths
    const objPath = `./${modelName}.obj`;
    const mtlPath = `./${modelName}.mtl`;
    const metadataPath = `./${modelName}_metadata.json`;

    document.getElementById('loading').innerHTML = `<div class="spinner"></div><div>Loading ${modelName}...</div>`;

    // Load new model (reuse existing loading code)
    loadModel({
        files: {
            obj: objPath,
            mtl: mtlPath,
            metadata: metadataPath
        }
    });
}

// Load model function
async function loadModel(response) {
    try {
        const modelPath = BACKEND_URL + response.files.glb;
        const metadataPath = BACKEND_URL + response.files.metadata;

        console.log(`Loading GLB from ${modelPath}`);
        console.log(`Loading metadata from ${metadataPath}`);

        document.getElementById('loading').innerHTML = '<div>Loading model...</div>';

        // Load metadata first
        const metadataResponse = await fetch(metadataPath);
        metadata = await metadataResponse.json();
        console.log('Metadata loaded:', metadata);

        // Populate object list
        allObjects = Object.keys(metadata.objects).map(id => ({
            id: id,
            ...metadata.objects[id]
        }));
        populateObjectList(allObjects);

        // Load GLB model
        const gltfLoader = new GLTFLoader();
        gltfLoader.load(
            modelPath,
            (gltf) => {
                console.log('✅ GLB loaded successfully');
                const object = gltf.scene;
                modelGroup = object;

                let vertexCount = 0;
                let triangleCount = 0;
                let objectCount = 0;

                object.traverse((child) => {
                    if (child.isMesh) {
                        // Extract object ID from mesh/node name (Building ID)
                        const objectId = child.name || child.parent?.name;
                        child.userData.objectId = objectId;

                        // Make objects pickable
                        child.userData.pickable = true;

                        // Track mesh by object ID for click interaction
                        if (!objectMeshMap[objectId]) {
                            objectMeshMap[objectId] = [];
                        }
                        objectMeshMap[objectId].push(child);

                        // PERFORMANCE BOOST: Optimize geometry
                        if (child.geometry) {
                            child.geometry.computeVertexNormals();
                        }

                        // Color coding by type (from metadata)
                        if (metadata && metadata.objects && metadata.objects[objectId]) {
                            const obj = metadata.objects[objectId];
                            const elementType = obj.element_type;

                            // Use MeshLambertMaterial for better performance
                            if (elementType === 'Building') {
                                child.material = new THREE.MeshLambertMaterial({
                                    color: 0x4169E1,
                                    side: THREE.DoubleSide,
                                    flatShading: false
                                });
                            } else if (elementType === 'RoofSurface') {
                                child.material = new THREE.MeshLambertMaterial({
                                    color: 0x8B4513,
                                    side: THREE.DoubleSide,
                                    flatShading: false
                                });
                            } else if (elementType === 'WallSurface') {
                                child.material = new THREE.MeshLambertMaterial({
                                    color: 0xCCCCCC,
                                    side: THREE.DoubleSide,
                                    flatShading: false
                                });
                            } else if (elementType === 'GroundSurface') {
                                child.material = new THREE.MeshLambertMaterial({
                                    color: 0x228B22,
                                    side: THREE.DoubleSide,
                                    flatShading: false
                                });
                            }
                        }

                        // PERFORMANCE: Enable frustum culling
                        child.frustumCulled = true;

                        // Store original material for hover/selection
                        originalMaterials.set(child, child.material.clone());

                        vertexCount += child.geometry.attributes.position.count;
                        triangleCount += child.geometry.index ?
                            child.geometry.index.count / 3 :
                            child.geometry.attributes.position.count / 3;
                        objectCount++;
                    }
                });

                scene.add(object);

                document.getElementById('loading').style.display = 'none';
                document.getElementById('info').style.display = 'block';
                document.getElementById('object-count').textContent = objectCount;
                document.getElementById('vertex-count').textContent = vertexCount.toLocaleString();
                document.getElementById('triangle-count').textContent = Math.floor(triangleCount).toLocaleString();

                const box = new THREE.Box3().setFromObject(object);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);

                // Position camera to view the whole model
                const fov = camera.fov * (Math.PI / 180);
                let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
                cameraZ *= 1.5;

                camera.position.set(center.x + cameraZ, center.y + cameraZ, center.z + cameraZ);
                camera.lookAt(center);
                controls.target.copy(center);
                controls.update();

                console.log(`Model centered at: (${center.x.toFixed(2)}, ${center.y.toFixed(2)}, ${center.z.toFixed(2)})`);
                console.log(`Model loaded successfully!`);
                console.log(`Objects: ${objectCount}, Vertices: ${vertexCount}, Triangles: ${Math.floor(triangleCount)}`);
            },
            (progress) => {
                const percent = (progress.loaded / progress.total * 100).toFixed(0);
                document.getElementById('loading').innerHTML = `<div>Loading model... ${percent}%</div>`;
            },
            (error) => {
                console.error('Error loading GLB:', error);
                document.getElementById('loading').innerHTML = '<div>Error loading model</div>';
            }
        );
    } catch (err) {
        console.error('Error loading model:', err);
        document.getElementById('loading').innerHTML = '<div>Error loading model</div>';
    }
}

// Don't load default model - wait for user to upload GML file
// loadModel('./citymodel.obj', './citymodel.mtl', './citymodel_metadata.json');

// Handle window resize
window.addEventListener('resize', () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}
animate();
