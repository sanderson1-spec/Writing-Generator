/**
 * prompt_display.js
 * Handles the prompt display functionality
 */

(function() {
    // Elements
    const promptContainer = document.getElementById('prompt-container');
    
    // Add functionality to export prompts
    function setupPromptExport() {
        // Create export button
        const exportButton = document.createElement('button');
        exportButton.className = 'export-button';
        exportButton.innerHTML = '<span>Export Prompts</span>';
        exportButton.style.display = 'none'; // Hide initially
        
        // Add it to the DOM
        const sessionControls = document.querySelector('.session-controls');
        sessionControls.appendChild(exportButton);
        
        // Add click handler
        exportButton.addEventListener('click', exportPrompts);
        
        // Show/hide export button based on prompts
        const observer = new MutationObserver(mutations => {
            const promptCards = promptContainer.querySelectorAll('.prompt-card');
            exportButton.style.display = promptCards.length > 0 ? 'block' : 'none';
        });
        
        observer.observe(promptContainer, { childList: true });
    }
    
    // Export prompts to a text file
    function exportPrompts() {
        const promptCards = promptContainer.querySelectorAll('.prompt-card');
        
        if (promptCards.length === 0) {
            return;
        }
        
        let content = '# Creative Writing Prompts\n\n';
        content += `Generated on ${new Date().toLocaleString()}\n\n`;
        
        promptCards.forEach((card, index) => {
            const promptNumber = card.querySelector('.prompt-number').textContent;
            const promptText = card.querySelector('.prompt-text').textContent;
            
            content += `## ${promptNumber}\n\n`;
            content += `${promptText}\n\n`;
        });
        
        // Create a download link
        const element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
        element.setAttribute('download', `writing-prompts-${Date.now()}.md`);
        
        element.style.display = 'none';
        document.body.appendChild(element);
        
        element.click();
        
        document.body.removeChild(element);
    }
    
    // Add prompt copy functionality
    function setupPromptCopy() {
        // Delegate event listener for copy buttons
        promptContainer.addEventListener('click', event => {
            // Check if the clicked element is a copy button
            if (event.target.classList.contains('copy-prompt-button')) {
                const promptCard = event.target.closest('.prompt-card');
                const promptText = promptCard.querySelector('.prompt-text').textContent;
                
                // Copy to clipboard
                navigator.clipboard.writeText(promptText)
                    .then(() => {
                        // Temporarily change button text
                        const originalText = event.target.textContent;
                        event.target.textContent = 'Copied!';
                        
                        setTimeout(() => {
                            event.target.textContent = originalText;
                        }, 2000);
                    })
                    .catch(err => {
                        console.error('Could not copy text: ', err);
                    });
            }
        });
    }
    
    // Apply styling for prompt display enhancements
    function applyPromptStyling() {
        const style = document.createElement('style');
        style.textContent = `
            .export-button {
                background-color: #2ecc71;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
                display: none;
                margin-left: 10px;
            }
            
            .export-button:hover {
                background-color: #27ae60;
            }
            
            .copy-prompt-button {
                position: absolute;
                bottom: 10px;
                right: 10px;
                background-color: transparent;
                border: 1px solid #ddd;
                padding: 5px 10px;
                border-radius: 4px;
                font-size: 0.8rem;
                color: #777;
                cursor: pointer;
            }
            
            .copy-prompt-button:hover {
                background-color: #f0f0f0;
            }
            
            /* Override displayPrompts function to add copy button */
            .prompt-card {
                padding-bottom: 40px; /* Space for the copy button */
            }
        `;
        document.head.appendChild(style);
    }
    
    // Override the displayPrompts function to add copy buttons
    const originalDisplayPrompts = window.displayPrompts;
    
    window.displayPrompts = function(prompts) {
        // Call the original function
        originalDisplayPrompts(prompts);
        
        // Add copy buttons to new prompt cards
        const promptCards = promptContainer.querySelectorAll('.prompt-card:not(.has-copy-button)');
        
        promptCards.forEach(card => {
            const copyButton = document.createElement('button');
            copyButton.className = 'copy-prompt-button';
            copyButton.textContent = 'Copy';
            
            card.appendChild(copyButton);
            card.classList.add('has-copy-button');
        });
    };
    
    // Initialize
    document.addEventListener('DOMContentLoaded', () => {
        setupPromptExport();
        setupPromptCopy();
        applyPromptStyling();
    });
})();
