from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import threading
import time
from llm_interface import (
    generate_prompt_with_timing, 
    generate_countdown_number,
    generate_final_message
)
from storage import save_character, load_character, save_settings, load_settings, save_theme, load_theme

app = Flask(__name__, static_folder='../frontend')
CORS(app)  # Enable CORS for all routes

# Store active prompt sessions
active_sessions = {}

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('../frontend', path)

@app.route('/api/character', methods=['POST'])
def save_character_route():
    """Save character definition"""
    character_data = request.json
    save_character(character_data)
    return jsonify({"status": "success"})

@app.route('/api/character', methods=['GET'])
def get_character_route():
    """Get saved character definition"""
    character = load_character()
    return jsonify(character)

@app.route('/api/theme', methods=['POST'])
def save_theme_route():
    """Save theme data"""
    theme_data = request.json
    save_theme(theme_data)
    return jsonify({"status": "success"})

@app.route('/api/theme', methods=['GET'])
def get_theme_route():
    """Get saved theme data"""
    theme = load_theme()
    return jsonify(theme)

@app.route('/api/settings', methods=['POST'])
def save_settings_route():
    """Save prompt settings"""
    settings_data = request.json
    save_settings(settings_data)
    return jsonify({"status": "success"})

@app.route('/api/settings', methods=['GET'])
def get_settings_route():
    """Get saved prompt settings"""
    settings = load_settings()
    return jsonify(settings)

@app.route('/api/start_session', methods=['POST'])
def start_session():
    """Start a new prompt generation session"""
    session_config = request.json
    session_id = str(time.time())  # Simple unique ID
    
    # Get character and theme if not provided
    if 'character' not in session_config:
        session_config['character'] = load_character()
    
    if 'theme' not in session_config:
        session_config['theme'] = load_theme()
    
    # Store session config
    active_sessions[session_id] = {
        "config": session_config,
        "prompts": [],
        "active": True,
        "countdown_active": False,
        "countdown_current": None,
        "countdown_end": 3  # Stop countdown at this number or lower
    }
    
    # Start prompt generation in a background thread
    thread = threading.Thread(
        target=prompt_generation_loop,
        args=(session_id,)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({"session_id": session_id})

@app.route('/api/stop_session/<session_id>', methods=['POST'])
def stop_session(session_id):
    """Stop an active prompt generation session"""
    if session_id in active_sessions:
        # Mark the session as inactive - the loop will handle cleanup
        active_sessions[session_id]["active"] = False
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "Session not found"}), 404

@app.route('/api/prompts/<session_id>', methods=['GET'])
def get_prompts(session_id):
    """Get all prompts generated in a session"""
    if session_id in active_sessions:
        # Return only prompts that haven't been seen yet
        last_seen = int(request.args.get('last_seen', -1))
        new_prompts = active_sessions[session_id]["prompts"][last_seen+1:]
        
        return jsonify({
            "prompts": new_prompts,
            "complete": not active_sessions[session_id]["active"]
        })
    return jsonify({"status": "error", "message": "Session not found"}), 404

def add_prompt_to_session(session_id, prompt_text, timestamp=None, next_interval=None, is_countdown=False, is_final=False):
    """Helper function to add a prompt to the session with proper metadata"""
    if session_id not in active_sessions:
        return
        
    session = active_sessions[session_id]
    prompt_count = len(session["prompts"])
    
    if timestamp is None:
        timestamp = time.time()
    
    prompt_data = {
        "id": prompt_count,
        "text": prompt_text,
        "timestamp": timestamp,
        "is_countdown": is_countdown,
        "is_final": is_final
    }
    
    if next_interval is not None:
        prompt_data["next_interval"] = next_interval
        
    session["prompts"].append(prompt_data)
    return prompt_count

def prompt_generation_loop(session_id):
    """Background task to generate prompts at dynamic intervals"""
    session = active_sessions[session_id]
    config = session["config"]
    
    # Get settings
    session_duration = config.get("session_duration", 15) * 60  # minutes to seconds
    min_interval = config.get("min_prompt_interval", 60)  # minimum seconds between prompts
    
    start_time = time.time()
    end_time = start_time + session_duration
    last_prompt_time = start_time
    prompt_count = 0
    
    # Main prompt generation loop
    try:
        while time.time() < end_time and session["active"]:
            current_time = time.time()
            time_since_last = current_time - last_prompt_time
            time_remaining = max(0, end_time - current_time)
            
            # Handle countdown if active
            if session["countdown_active"]:
                if time_since_last >= 1:  # Countdown steps every second
                    current_number = session["countdown_current"]
                    
                    # Check if we've reached the end of the countdown
                    if current_number <= session["countdown_end"]:
                        # Generate final countdown message
                        final_text = generate_countdown_number(
                            config["character"], 
                            config["theme"], 
                            current_number,
                            is_final=True
                        )
                        add_prompt_to_session(
                            session_id, 
                            final_text, 
                            timestamp=current_time, 
                            is_countdown=True,
                            is_final=True
                        )
                        
                        # End the session
                        session["countdown_active"] = False
                        session["active"] = False
                        break
                    
                    # Generate the next countdown number
                    countdown_text = generate_countdown_number(
                        config["character"], 
                        config["theme"], 
                        current_number
                    )
                    
                    add_prompt_to_session(
                        session_id, 
                        countdown_text, 
                        timestamp=current_time, 
                        next_interval=1,
                        is_countdown=True
                    )
                    
                    # Update for next countdown step
                    session["countdown_current"] = current_number - 1
                    last_prompt_time = current_time
                
                # Short sleep to prevent CPU hogging during countdown
                time.sleep(0.1)
                continue
            
            # Only generate regular prompts if minimum time has passed
            if time_since_last >= min_interval:
                # Generate prompt using LLM with dynamic timing suggestion
                character = config["character"]
                theme = config["theme"]
                
                # Calculate time elapsed and remaining
                time_elapsed = current_time - start_time
                
                prompt_text, next_interval, is_countdown, countdown_from = generate_prompt_with_timing(
                    character=character,
                    theme=theme,
                    prompt_number=prompt_count+1,
                    time_elapsed=time_elapsed,
                    time_remaining=time_remaining
                )
                
                # Check if this starts a countdown
                if is_countdown and countdown_from is not None:
                    # Set up countdown state
                    session["countdown_active"] = True
                    session["countdown_current"] = countdown_from
                    
                    # Use very short interval for countdown
                    next_interval = 1
                else:
                    # Ensure next_interval respects minimum for regular prompts
                    next_interval = max(min_interval, next_interval)
                
                # Add to session prompts
                add_prompt_to_session(
                    session_id, 
                    prompt_text, 
                    timestamp=current_time, 
                    next_interval=next_interval,
                    is_countdown=is_countdown
                )
                
                prompt_count += 1
                last_prompt_time = current_time
                
                # Sleep for the dynamic interval (or until session ends)
                sleep_until = min(last_prompt_time + next_interval, end_time)
                sleep_duration = max(0, sleep_until - time.time())
                
                if sleep_duration > 0 and session["active"]:
                    time.sleep(sleep_duration)
            else:
                # Small sleep to prevent CPU hogging
                time.sleep(0.1)
        
        # If session ended without a proper countdown conclusion, 
        # add a final message anyway to ensure closure
        if session["active"]:  # Normal time expiration
            # Generate a final message
            final_message = generate_final_message(config["character"], config["theme"])
            add_prompt_to_session(
                session_id, 
                final_message, 
                timestamp=time.time(), 
                is_final=True
            )
        
        # Mark session as complete
        session["active"] = False
        
    except Exception as e:
        print(f"Error in prompt generation loop: {e}")
        # Add an error message to the prompts
        add_prompt_to_session(
            session_id,
            "Sorry, an error occurred during prompt generation.",
            timestamp=time.time()
        )
        # Mark session as complete
        session["active"] = False

if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Start server
    app.run(debug=True, port=5000)