// DOM elements
const dropzone = document.getElementById("dropzone");

// Drag and drop functionality
function initDragAndDrop() {
    let dragCounter = 0;
    let isDragging = false;

    // Prevent default drag behaviors on the entire document
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        document.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Track drag state on document level to avoid flashing
    document.addEventListener('dragenter', function (e) {
        if (e.dataTransfer.types.includes('Files')) {
            dragCounter++;
            if (!isDragging) {
                isDragging = true;
                dropzone.classList.add('active');
            }
        }
    });

    document.addEventListener('dragleave', function (e) {
        dragCounter--;
        // Use a small delay to prevent flickering when moving between elements
        setTimeout(() => {
            if (dragCounter <= 0) {
                dragCounter = 0;
                isDragging = false;
                dropzone.classList.remove('active');
            }
        }, 50);
    });

    document.addEventListener('drop', function (e) {
        dragCounter = 0;
        isDragging = false;
        dropzone.classList.remove('active');
    });

    // Handle dropped files
    document.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        if (!e.dataTransfer.types.includes('Files')) return;

        dragCounter = 0;
        isDragging = false;
        dropzone.classList.remove('active');

        const files = e.dataTransfer.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            console.log('Loading file...', file.name);

            // Check file type
            const allowedExtensions = ['txt', 'air', 'openair'];
            const fileExtension = file.name.split('.').pop().toLowerCase();

            if (!allowedExtensions.includes(fileExtension)) {
                alert('Invalid file type. Please upload .txt, .air, or .openair files.');
                return;
            }

            // Create form data and submit
            const formData = new FormData();
            formData.append('file', file);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
                .then(response => {
                    if (response.ok) {
                        // Reload page to show new data
                        window.location.reload();
                    } else {
                        alert('Error uploading file');
                    }
                })
                .catch(error => {
                    console.error('Upload error:', error);
                    alert('Error uploading file');
                });
        }
    }
}
