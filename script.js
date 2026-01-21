document.addEventListener('DOMContentLoaded', async function() {
    const appContainer = document.getElementById('app');

    // Initialize the template engine
    try {
        // Load the base template
        await window.templateEngine.loadTemplate('base', 'templates/base.html');
        console.log('Base template loaded successfully');

        // Render the base template initially
        appContainer.innerHTML = window.templateEngine.render('base', { content: '<div class="loading">Loading content...</div>' });

        // Now that the template is rendered, we can attach event listeners
        const tabs = document.querySelectorAll('.tab-button');
        const contentContainer = document.getElementById('content-container');

        if (!contentContainer) {
            console.error('Content container not found!');
            return;
        }

        async function loadContent(tabName) {
            console.log(`Loading content for tab: ${tabName}`);
            try {
                const url = `components/${tabName}.html`;
                console.log(`Fetching from URL: ${url}`);
                const response = await fetch(url);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const content = await response.text();
                console.log('Content loaded successfully');
                contentContainer.innerHTML = content;
            } catch (error) {
                console.error('Error loading content:', error);
                contentContainer.innerHTML = `<div class="error">Error loading content: ${error.message}</div>`;
            }
        }

        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                console.log(`Tab clicked: ${tab.getAttribute('data-tab')}`);
                // Remove active class from all tabs
                tabs.forEach(t => t.classList.remove('active'));

                // Add active class to clicked tab
                tab.classList.add('active');

                // Load the corresponding content
                const tabName = tab.getAttribute('data-tab');
                loadContent(tabName);
            });
        });

        // Load initial content
        console.log('Loading initial content...');
        loadContent('resume');

    } catch (error) {
        console.error('Error initializing template:', error);
        appContainer.innerHTML = `<div class="error">Error loading template: ${error.message}</div>`;
    }
});
