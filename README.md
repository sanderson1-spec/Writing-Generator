# Creative Writing Prompt Generator

A web application that generates creative writing prompts based on user-defined characters and settings.

## Overview

This application allows users to:

1. Define character details using free-form text fields
2. Configure prompt generation settings (session duration and frequency)
3. Generate a series of creative writing prompts at short intervals (30s-1min)
4. Export generated prompts for later use

## Project Structure

The application follows a simple client-server architecture:

- **Frontend**: HTML, CSS, and JavaScript
- **Backend**: Python using Flask
- **LLM Integration**: Connects to locally hosted LLMs (LMStudio or Ollama)

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- LMStudio or Ollama installed locally

### Installation

1. Set up the Python virtual environment:

```bash
cd writing_prompt_generator
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
```

2. Start the LLM service:

**For LMStudio**:
- Open LMStudio
- Load your preferred model
- Start the local server (typically on port 1234)

**For Ollama**:
- Install Ollama from https://ollama.ai/
- Pull a model: `ollama pull mistral`
- Start the Ollama service

3. Configure environment variables (optional):

```bash
# For LMStudio (default)
export LLM_BACKEND=lmstudio
export LLM_HOST=http://localhost:1234

# For Ollama
export LLM_BACKEND=ollama
export LLM_HOST=http://localhost:11434
export LLM_MODEL=mistral
```

4. Start the backend server:

```bash
cd backend
python app.py
```

5. Open the application in your browser:

```
http://localhost:5000
```

## Usage Guide

### Defining a Character

1. Navigate to the "Setup" tab
2. Fill in the character details:
   - **Name**: Main identifier for your character
   - **Description**: Background, appearance, and other details
   - **Personality**: Character traits, quirks, and behaviors
   - **Theme**: Setting, genre, or thematic elements
3. Click "Save Character" (or let it auto-save)

### Configuring Prompt Settings

1. In the "Setup" tab, scroll to "Prompt Settings"
2. Set your preferred:
   - **Session Duration**: How long the prompt session will run (in minutes)
   - **Prompt Interval**: How frequently prompts will be generated (in seconds)
3. Click "Save Settings"

### Starting a Prompt Session

1. Click "Start Prompt Session"
2. The application will automatically switch to the "Prompts" tab
3. Watch as new prompts appear at your specified interval
4. Click "Stop Session" at any time to end the session early

### Exporting Prompts

1. After generating prompts, click the "Export Prompts" button
2. A Markdown file will be downloaded with all your prompts

## License

This project is provided for academic purposes only and is not intended for commercial use.
