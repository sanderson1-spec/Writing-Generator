import json
import os
from typing import Dict, Any, Optional

# Data directory for persistence
DATA_DIR = "data"
CHARACTER_FILE = os.path.join(DATA_DIR, "character.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
THEME_FILE = os.path.join(DATA_DIR, "theme.json")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

def save_character(character_data: Dict[str, Any]) -> None:
    """
    Save character definition to disk
    
    Args:
        character_data: Dictionary containing character definition
    """
    with open(CHARACTER_FILE, 'w') as f:
        json.dump(character_data, f, indent=2)

def load_character() -> Dict[str, Any]:
    """
    Load character definition from disk
    
    Returns:
        Dictionary containing character definition or default if not found
    """
    try:
        if os.path.exists(CHARACTER_FILE):
            with open(CHARACTER_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading character: {e}")
    
    # Return default character if no saved data
    return {
        "name": "",
        "description": "",
        "personality": ""
    }

def save_theme(theme_data: Dict[str, Any]) -> None:
    """
    Save theme data to disk
    
    Args:
        theme_data: Dictionary containing theme data
    """
    with open(THEME_FILE, 'w') as f:
        json.dump(theme_data, f, indent=2)

def load_theme() -> Dict[str, Any]:
    """
    Load theme data from disk
    
    Returns:
        Dictionary containing theme data or default if not found
    """
    try:
        if os.path.exists(THEME_FILE):
            with open(THEME_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading theme: {e}")
    
    # Return default theme if no saved data
    return {
        "theme_name": "",
        "theme_description": "",
        "example_message": ""
    }

def save_settings(settings_data: Dict[str, Any]) -> None:
    """
    Save prompt settings to disk
    
    Args:
        settings_data: Dictionary containing prompt settings
    """
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings_data, f, indent=2)

def load_settings() -> Dict[str, Any]:
    """
    Load prompt settings from disk
    
    Returns:
        Dictionary containing prompt settings or default if not found
    """
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading settings: {e}")
    
    # Return default settings if no saved data
    return {
        "session_duration": 15,  # minutes
        "min_prompt_interval": 60  # seconds
    }