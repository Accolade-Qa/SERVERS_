document.addEventListener('DOMContentLoaded', function() {

    if (typeof Alpine === 'undefined') {
        console.warn('Alpine.js not loaded');
        return;
    }

    // Alpine.js data for folder expansion
    Alpine.data('folderTree', () => ({
        expandedFolders: [],
        toggleFolder(folderId) {
            if (this.expandedFolders.includes(folderId)) {
                this.expandedFolders = this.expandedFolders.filter(id => id !== folderId);
            } else {
                this.expandedFolders.push(folderId);
            }
        }
    }));

    const uploadForm = document.querySelector('form[action="/upload/"]');
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            const fileInput = this.querySelector('input[name="file"]');
            const userInput = this.querySelector('input[name="user"]');

            if (!userInput.value.trim()) {
                alert('Please enter a RPi board username');
                e.preventDefault();
                return;
            }

            if (!fileInput.files[0]) {
                alert('Please select a log file to upload');
                e.preventDefault();
                return;
            }

            const file = fileInput.files[0];
            if (!file.name.endsWith('.log')) {
                alert('Only .log files are allowed');
                e.preventDefault();
                return;
            }

            if (file.size > 10 * 1024 * 1024) {
                alert('File size must be less than 10MB');
                e.preventDefault();
                return;
            }

            showUploadLoading(true);
        });
    }

    highlightLogContent();

    makeTableSortable();

    formatFileSizes();

    addCopyButtons();
});

function showUploadLoading(show) {
    const form = document.querySelector('form[action="/upload/"]');
    if (!form) return;

    let spinner = form.querySelector('.spinner');
    if (show) {
        if (!spinner) {
            spinner = document.createElement('div');
            spinner.className = 'spinner';
            form.appendChild(spinner);
        }
        spinner.style.display = 'block';

        const inputs = form.querySelectorAll('input, button');
        inputs.forEach(input => input.disabled = true);
    } else {
        if (spinner) spinner.style.display = 'none';
        const inputs = form.querySelectorAll('input, button');
        inputs.forEach(input => input.disabled = false);
    }
}

function highlightLogContent() {
    const logContent = document.querySelector('.log-content');
    if (!logContent) return;

    const text = logContent.textContent;
    const highlighted = text
        .replace(/(ERROR|ERR)/gi, '<span class="log-error">$1</span>')
        .replace(/(WARNING|WARN)/gi, '<span class="log-warn">$1</span>')
        .replace(/(INFO)/gi, '<span class="log-info">$1</span>')
        .replace(/(DEBUG)/gi, '<span class="log-debug">$1</span>');

    logContent.innerHTML = highlighted;
}

function makeTableSortable() {
    const table = document.querySelector('table');
    if (!table) return;

    const headers = table.querySelectorAll('th');
    headers.forEach((header, index) => {
        header.style.cursor = 'pointer';
        header.addEventListener('click', () => sortTable(table, index));
    });
}

function sortTable(table, column) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        const aVal = a.cells[column].textContent.trim();
        const bVal = b.cells[column].textContent.trim();

        const aNum = parseFloat(aVal);
        const bNum = parseFloat(bVal);

        if (!isNaN(aNum) && !isNaN(bNum)) {
            return aNum - bNum;
        }

        return aVal.localeCompare(bVal);
    });

    rows.forEach(row => tbody.appendChild(row));
}

function formatFileSizes() {
}

function addCopyButtons() {
    const logContent = document.querySelector('.log-content');
    if (!logContent) return;

    const copyButton = document.createElement('button');
    copyButton.textContent = '📋 Copy Log';
    copyButton.className = 'bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 mt-4';
    copyButton.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(logContent.textContent);
            copyButton.textContent = '✅ Copied!';
            setTimeout(() => {
                copyButton.textContent = '📋 Copy Log';
            }, 2000);
        } catch (err) {
            console.error('Failed to copy: ', err);
            alert('Failed to copy to clipboard');
        }
    });

    logContent.parentNode.insertBefore(copyButton, logContent);
}

function makeRequest(url, options = {}) {
    return fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    });
}

// Export to window for click handlers
window.LogDashboard = {
    highlightLogContent,
    makeTableSortable,
    showUploadLoading
};
