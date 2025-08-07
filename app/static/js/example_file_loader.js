// This function is called by example_menu.js when an example file is loaded
// It uploads the file content to the backend as if it was dropped/uploaded
window.handleExampleFileLoad = function(fileContent, filename) {
  // Create a Blob and FormData to simulate file upload
  const ext = filename.split('.').pop().toLowerCase();
  const allowed = ['txt', 'air', 'openair'];
  if (!allowed.includes(ext)) {
    alert('Invalid file type.');
    return;
  }
  const blob = new Blob([fileContent], { type: 'text/plain' });
  const file = new File([blob], filename, { type: 'text/plain' });
  const formData = new FormData();
  formData.append('file', file);

  fetch('/upload', {
    method: 'POST',
    body: formData
  })
    .then(response => {
      if (response.ok) {
        window.location.reload();
      } else {
        alert('Error loading example file');
      }
    })
    .catch(error => {
      alert('Error loading example file: ' + error.message);
    });
};
