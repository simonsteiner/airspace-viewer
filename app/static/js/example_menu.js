// Handles the example file menu: populates dropdown, loads file, and triggers app logic

document.addEventListener('DOMContentLoaded', () => {
  const select = document.getElementById('example-select');
  const loadBtn = document.getElementById('load-example-btn');

  // Fetch and populate example files

  fetch('/examples/list')
    .then(r => r.json())
    .then(files => {
      select.innerHTML = '';
      files.forEach(f => {
        const opt = document.createElement('option');
        opt.value = f;
        opt.textContent = f;
        select.appendChild(opt);
      });
      // Select the current loaded airspace file if present
      const currentFile = select.getAttribute('data-current-file');
      if (currentFile) {
        for (let i = 0; i < select.options.length; i++) {
          if (select.options[i].value === currentFile) {
            select.selectedIndex = i;
            break;
          }
        }
      }
    });

  // Load selected example file and trigger app logic
  loadBtn.addEventListener('click', () => {
    const filename = select.value;
    if (!filename) return;
    fetch(`/examples/get/${encodeURIComponent(filename)}`)
      .then(r => {
        if (!r.ok) throw new Error('Failed to fetch example file');
        return r.text();
      })
      .then(text => {
        // Simulate file drop/upload logic
        if (window.handleExampleFileLoad) {
          window.handleExampleFileLoad(text, filename);
        } else if (window.handleFileContent) {
          window.handleFileContent(text, filename);
        } else {
          alert('No handler for loading example file.');
        }
      })
      .catch(e => alert('Error loading example: ' + e.message));
  });
});
