document.addEventListener('DOMContentLoaded', async function() {
    const appContainer = document.getElementById('app');

    try {
        await window.templateEngine.loadTemplate('base', 'templates/base.html');
        appContainer.innerHTML = window.templateEngine.render('base', {});
    } catch (error) {
        console.error('Error initializing template:', error);
        appContainer.innerHTML = `<div class="error">Error loading template: ${error.message}</div>`;
    }
});
