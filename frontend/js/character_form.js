/**
 * character_form.js
 * Handles the character definition form functionality
 */

// Add character form auto-save feature
(function() {
    // Elements
    const characterForm = document.getElementById('character-form');
    const nameInput = document.getElementById('name');
    const descriptionInput = document.getElementById('description');
    const personalityInput = document.getElementById('personality');
    
    // Debounce function for auto-save
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Auto-save function
    const autoSave = debounce(() => {
        const formData = {
            name: nameInput.value,
            description: descriptionInput.value,
            personality: personalityInput.value
        };
        
        // Don't auto-save if name is empty
        if (!formData.name) {
            return;
        }
        
        fetch(`${API_BASE_URL}/character`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (response.ok) {
                // Update the state
                state.characterData = formData;
                
                // Show a subtle indicator that save was successful
                const saveIndicator = document.createElement('span');
                saveIndicator.className = 'auto-save-indicator';
                saveIndicator.textContent = 'Auto-saved';
                
                // Append to the form
                const existingIndicator = characterForm.querySelector('.auto-save-indicator');
                if (existingIndicator) {
                    characterForm.removeChild(existingIndicator);
                }
                
                characterForm.appendChild(saveIndicator);
                
                // Remove after 2 seconds
                setTimeout(() => {
                    if (saveIndicator.parentNode === characterForm) {
                        characterForm.removeChild(saveIndicator);
                    }
                }, 2000);
            }
        })
        .catch(error => {
            console.error('Auto-save error:', error);
        });
    }, 2000); // Auto-save 2 seconds after typing stops
    
    // Add input event listeners for auto-save
    nameInput.addEventListener('input', autoSave);
    descriptionInput.addEventListener('input', autoSave);
    personalityInput.addEventListener('input', autoSave);
    
    // Helper function to validate character data
    window.validateCharacterData = function() {
        // Basic validation - just check if name is filled in
        if (!nameInput.value.trim()) {
            showNotification('Character name is required', 'error');
            return false;
        }
        return true;
    };
    
    // Add CSS for auto-save indicator
    const style = document.createElement('style');
    style.textContent = `
        .auto-save-indicator {
            position: absolute;
            bottom: 10px;
            right: 10px;
            background-color: #f0f0f0;
            color: #666;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            opacity: 0.8;
        }
    `;
    document.head.appendChild(style);
})();

// Add theme form auto-save feature
(function() {
    // Elements
    const themeForm = document.getElementById('theme-form');
    const themeNameInput = document.getElementById('theme-name');
    const themeDescriptionInput = document.getElementById('theme-description');
    const exampleMessageInput = document.getElementById('example-message');
    
    // Use the same debounce function defined in the character form IIFE
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Auto-save function for theme form
    const autoSaveTheme = debounce(() => {
        const formData = {
            theme_name: themeNameInput.value,
            theme_description: themeDescriptionInput.value,
            example_message: exampleMessageInput.value
        };
        
        // Don't auto-save if theme name is empty
        if (!formData.theme_name) {
            return;
        }
        
        fetch(`${API_BASE_URL}/theme`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        })
        .then(response => {
            if (response.ok) {
                // Update the state
                state.themeData = formData;
                
                // Show a subtle indicator that save was successful
                const saveIndicator = document.createElement('span');
                saveIndicator.className = 'auto-save-indicator';
                saveIndicator.textContent = 'Auto-saved';
                
                // Append to the form
                const existingIndicator = themeForm.querySelector('.auto-save-indicator');
                if (existingIndicator) {
                    themeForm.removeChild(existingIndicator);
                }
                
                themeForm.appendChild(saveIndicator);
                
                // Remove after 2 seconds
                setTimeout(() => {
                    if (saveIndicator.parentNode === themeForm) {
                        themeForm.removeChild(saveIndicator);
                    }
                }, 2000);
            }
        })
        .catch(error => {
            console.error('Auto-save error:', error);
        });
    }, 2000); // Auto-save 2 seconds after typing stops
    
    // Add input event listeners for auto-save
    themeNameInput.addEventListener('input', autoSaveTheme);
    themeDescriptionInput.addEventListener('input', autoSaveTheme);
    exampleMessageInput.addEventListener('input', autoSaveTheme);
    
    // Helper function to validate theme data
    window.validateThemeData = function() {
        // Basic validation - just check if theme name is filled in
        if (!themeNameInput.value.trim()) {
            showNotification('Theme name is required', 'error');
            return false;
        }
        return true;
    };
})();