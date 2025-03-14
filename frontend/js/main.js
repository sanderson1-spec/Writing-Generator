// Base URL for API calls
const API_BASE_URL = 'http://localhost:5000/api';

// Global state
const state = {
    activeSession: null,
    lastSeenPromptId: -1,
    pollingInterval: null,
    characterData: null,
    themeData: null,
    settings: null
};

// DOM elements
const elements = {
    tabButtons: document.querySelectorAll('.tab-button'),
    tabPanes: document.querySelectorAll('.tab-pane'),
    sessionInfo: document.getElementById('session-info'),
    startSessionButton: document.getElementById('start-session'),
    stopSessionButton: document.getElementById('stop-session'),
    promptContainer: document.getElementById('prompt-container')
};

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    loadCharacterData();
    loadThemeData();
    loadSettings();
    setupEventListeners();
});

// Tab functionality
function setupTabs() {
    elements.tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            // Update active tab button
            elements.tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Update active tab pane
            elements.tabPanes.forEach(pane => pane.classList.remove('active'));
            document.getElementById(`${tabName}-tab`).classList.add('active');
        });
    });
}

// Load character data from the server
async function loadCharacterData() {
    try {
        const response = await fetch(`${API_BASE_URL}/character`);
        state.characterData = await response.json();
        
        // Populate form fields
        document.getElementById('name').value = state.characterData.name || '';
        document.getElementById('description').value = state.characterData.description || '';
        document.getElementById('personality').value = state.characterData.personality || '';
    } catch (error) {
        console.error('Error loading character data:', error);
    }
}

// Load theme data from the server
async function loadThemeData() {
    try {
        const response = await fetch(`${API_BASE_URL}/theme`);
        state.themeData = await response.json();
        
        // Populate form fields
        document.getElementById('theme-name').value = state.themeData.theme_name || '';
        document.getElementById('theme-description').value = state.themeData.theme_description || '';
        document.getElementById('example-message').value = state.themeData.example_message || '';
    } catch (error) {
        console.error('Error loading theme data:', error);
    }
}

// Load settings from the server
async function loadSettings() {
    try {
        const response = await fetch(`${API_BASE_URL}/settings`);
        state.settings = await response.json();
        
        // Populate form fields
        document.getElementById('session-duration').value = state.settings.session_duration || 15;
        document.getElementById('prompt-interval').value = state.settings.min_prompt_interval || 60;
    } catch (error) {
        console.error('Error loading settings:', error);
    }
}

// Set up event listeners
function setupEventListeners() {
    // Character form submission
    document.getElementById('character-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('name').value,
            description: document.getElementById('description').value,
            personality: document.getElementById('personality').value
        };
        
        try {
            const response = await fetch(`${API_BASE_URL}/character`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                state.characterData = formData;
                showNotification('Character saved successfully!');
            } else {
                showNotification('Error saving character', 'error');
            }
        } catch (error) {
            console.error('Error saving character:', error);
            showNotification('Error saving character', 'error');
        }
    });
    
    // Theme form submission
    document.getElementById('theme-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            theme_name: document.getElementById('theme-name').value,
            theme_description: document.getElementById('theme-description').value,
            example_message: document.getElementById('example-message').value
        };
        
        try {
            const response = await fetch(`${API_BASE_URL}/theme`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                state.themeData = formData;
                showNotification('Theme saved successfully!');
            } else {
                showNotification('Error saving theme', 'error');
            }
        } catch (error) {
            console.error('Error saving theme:', error);
            showNotification('Error saving theme', 'error');
        }
    });
    
    // Settings form submission
    document.getElementById('settings-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = {
            session_duration: parseInt(document.getElementById('session-duration').value),
            min_prompt_interval: parseInt(document.getElementById('prompt-interval').value)
        };
        
        try {
            const response = await fetch(`${API_BASE_URL}/settings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            if (response.ok) {
                state.settings = formData;
                showNotification('Settings saved successfully!');
            } else {
                showNotification('Error saving settings', 'error');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            showNotification('Error saving settings', 'error');
        }
    });
    
    // Start session button
    elements.startSessionButton.addEventListener('click', startSession);
    
    // Stop session button
    elements.stopSessionButton.addEventListener('click', stopSession);
}

// Simple notification system
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.classList.add('fadeout');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 500);
    }, 3000);
}

// Start a new prompt session
async function startSession() {
    // Validate character data
    if (!state.characterData || !state.characterData.name) {
        showNotification('Please define a character first', 'error');
        return;
    }
    
    // Validate theme data
    if (!state.themeData || !state.themeData.theme_name) {
        showNotification('Please define a theme first', 'error');
        return;
    }
    
    // Prevent starting multiple sessions
    if (state.activeSession) {
        showNotification('A session is already running', 'error');
        return;
    }
    
    try {
        // Create session configuration with character and theme
        const sessionConfig = {
            ...state.settings,
            character: state.characterData,
            theme: state.themeData
        };
        
        const response = await fetch(`${API_BASE_URL}/start_session`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(sessionConfig)
        });
        
        if (response.ok) {
            const data = await response.json();
            state.activeSession = data.session_id;
            state.lastSeenPromptId = -1;
            
            // Update UI
            updateSessionUI(true);
            
            // Switch to prompts tab
            document.querySelector('[data-tab="prompts"]').click();
            
            // Start polling for prompts
            startPromptPolling();
            
            showNotification('Prompt session started!');
        } else {
            showNotification('Error starting session', 'error');
        }
    } catch (error) {
        console.error('Error starting session:', error);
        showNotification('Error starting session', 'error');
    }
}

// Stop the current prompt session
async function stopSession() {
    if (!state.activeSession) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/stop_session/${state.activeSession}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            // Final poll to get any remaining prompts
            await pollForPrompts();
            
            // Clear the session
            clearPromptPolling();
            state.activeSession = null;
            
            // Update UI
            updateSessionUI(false);
            
            showNotification('Session ended');
        } else {
            showNotification('Error stopping session', 'error');
        }
    } catch (error) {
        console.error('Error stopping session:', error);
        showNotification('Error stopping session', 'error');
    }
}

// Start polling for new prompts
function startPromptPolling() {
    // Stop any existing polling
    clearPromptPolling();
    
    // Initial poll
    pollForPrompts();
    
    // Set up regular polling (every second for countdowns)
    state.pollingInterval = setInterval(pollForPrompts, 1000);
}

// Clear prompt polling
function clearPromptPolling() {
    if (state.pollingInterval) {
        clearInterval(state.pollingInterval);
        state.pollingInterval = null;
    }
}

// Poll the server for new prompts
async function pollForPrompts() {
    if (!state.activeSession) {
        return;
    }
    
    try {
        const response = await fetch(
            `${API_BASE_URL}/prompts/${state.activeSession}?last_seen=${state.lastSeenPromptId}`
        );
        
        if (response.ok) {
            const data = await response.json();
            
            // Add new prompts to the display
            if (data.prompts && data.prompts.length > 0) {
                displayPrompts(data.prompts);
                state.lastSeenPromptId = data.prompts[data.prompts.length - 1].id;
            }
            
            // If session is complete, stop polling
            if (data.complete) {
                clearPromptPolling();
                state.activeSession = null;
                updateSessionUI(false);
            }
        } else {
            console.error('Error polling for prompts');
        }
    } catch (error) {
        console.error('Error polling for prompts:', error);
    }
}

// Display prompts in the UI
function displayPrompts(prompts) {
    // Clear empty state if needed
    const emptyState = elements.promptContainer.querySelector('.prompt-empty-state');
    if (emptyState) {
        elements.promptContainer.removeChild(emptyState);
    }
    
    // Add each new prompt
    prompts.forEach(prompt => {
        const promptElement = document.createElement('div');
        
        // Add special classes for countdown and final messages
        let promptClass = 'prompt-card';
        if (prompt.is_countdown) {
            promptClass += ' countdown-prompt';
        }
        if (prompt.is_final) {
            promptClass += ' final-prompt';
        }
        
        promptElement.className = promptClass;
        
        // Create prompt content
        promptElement.innerHTML = `
            <div class="prompt-number">Prompt #${prompt.id + 1}</div>
            <div class="prompt-text">${prompt.text}</div>
            <div class="prompt-timestamp">
                ${formatTimestamp(prompt.timestamp)}
                ${prompt.next_interval ? `<span class="next-interval">(Next in ${prompt.next_interval}s)</span>` : ''}
            </div>
        `;
        
        elements.promptContainer.appendChild(promptElement);
        
        // Scroll to the bottom
        elements.promptContainer.scrollTop = elements.promptContainer.scrollHeight;
        
        // Add special animation for countdown prompts
        if (prompt.is_countdown) {
            promptElement.classList.add('pulse-animation');
        }
        
        // Add special styling for final message
        if (prompt.is_final) {
            promptElement.classList.add('highlight-animation');
        }
    });
}

// Format timestamp to readable time
function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString();
}

// Update the session UI based on active state
function updateSessionUI(isActive) {
    elements.startSessionButton.disabled = isActive;
    elements.stopSessionButton.disabled = !isActive;
    
    if (isActive) {
        elements.sessionInfo.innerHTML = `
            <span class="session-active">Session Active</span>
            <p>Minimum interval: ${state.settings.min_prompt_interval} seconds (may adapt based on context)</p>
        `;
        
        // Clear existing prompts
        elements.promptContainer.innerHTML = `
            <div class="prompt-empty-state">
                <p>Waiting for first prompt...</p>
            </div>
        `;
    } else {
        elements.sessionInfo.innerHTML = `
            <p>Session not active</p>
        `;
    }
}