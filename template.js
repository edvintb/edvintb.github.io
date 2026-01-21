/**
 * Simple templating system
 */
class TemplateEngine {
    constructor() {
        this.templates = {};
    }

    /**
     * Load a template from a file
     * @param {string} name - Template name
     * @param {string} url - URL to load template from
     * @returns {Promise<string>} - The template content
     */
    async loadTemplate(name, url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Failed to load template: ${response.status}`);
            }
            const template = await response.text();
            this.templates[name] = template;
            return template;
        } catch (error) {
            console.error(`Error loading template ${name}:`, error);
            throw error;
        }
    }

    /**
     * Render a template with data
     * @param {string} name - Template name
     * @param {Object} data - Data to render template with
     * @returns {string} - Rendered template
     */
    render(name, data = {}) {
        if (!this.templates[name]) {
            throw new Error(`Template ${name} not found`);
        }
        
        // Simple variable replacement
        let rendered = this.templates[name];
        for (const key in data) {
            const regex = new RegExp(`{{\\s*${key}\\s*}}`, 'g');
            rendered = rendered.replace(regex, data[key]);
        }
        
        return rendered;
    }
}

// Create global template engine instance
window.templateEngine = new TemplateEngine();
