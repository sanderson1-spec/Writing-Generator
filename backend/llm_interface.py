import requests
import json
import os
import re
from typing import Dict, Any, Optional, Tuple, List

# Configuration variables for different LLM backends
LLM_BACKEND = os.environ.get("LLM_BACKEND", "lmstudio")  # Options: lmstudio, ollama
LLM_HOST = os.environ.get("LLM_HOST", "http://localhost:1234")  # Default for LMStudio
LLM_MODEL = os.environ.get("LLM_MODEL", "mistral")  # Default model name

def generate_prompt_with_timing(character: Dict[str, str], 
                                theme: Dict[str, str], 
                                prompt_number: int, 
                                time_elapsed: float, 
                                time_remaining: float,
                                total_prompts: int = None) -> Tuple[str, int, bool, Optional[int]]:
    """
    Generate a creative writing prompt with a suggested timing for the next prompt
    
    Args:
        character: Dictionary containing character definition fields
        theme: Dictionary containing theme information
        prompt_number: Current prompt number in the sequence
        time_elapsed: Time elapsed since session start in seconds
        time_remaining: Time remaining in session in seconds
        total_prompts: Optional estimate of total prompts in session
        
    Returns:
        Tuple of (prompt_text, next_interval_in_seconds, is_countdown, countdown_from)
        - prompt_text: The generated prompt
        - next_interval_in_seconds: Time until next prompt
        - is_countdown: Boolean indicating if this is part of a countdown
        - countdown_from: If starting a countdown, what number to count from (None otherwise)
    """
    # Check if we're near the end of the session (less than 45 seconds remaining)
    is_near_end = time_remaining <= 45
    
    # Create system prompt based on current context
    if is_near_end:
        system_prompt = f"""You are a creative writing prompt generator.

The writing session is about to end. You need to create a countdown sequence to conclude the session.

CHARACTER INFORMATION:
Name: {character.get('name', 'Unnamed Character')}
Description: {character.get('description', 'No description provided')}
Personality: {character.get('personality', 'No personality defined')}

THEME INFORMATION:
Theme: {theme.get('theme_name', 'No theme specified')}
Theme Description: {theme.get('theme_description', 'No theme description provided')}
Example Message: {theme.get('example_message', 'No example provided')}

Time remaining in session: {int(time_remaining)} seconds.

IMPORTANT INSTRUCTIONS:
1. You must initiate a countdown sequence that fits the character and theme
2. Choose a starting number between 10 and 20
3. The countdown will happen every second until it reaches 3 or lower
4. Your response should ONLY include one of the following:
   a) The countdown introduction and starting number
   b) The final message when the countdown ends

FORMAT YOUR RESPONSE LIKE THIS:
[PROMPT] Your actual text goes here.
[NEXT_INTERVAL] 1
[IS_COUNTDOWN] true
[COUNTDOWN_FROM] 15  (only include this line when starting a countdown, with your chosen number)
"""
    else:
        system_prompt = f"""You are a creative writing prompt generator.
    
You are helping generate a series of writing prompts based on:

CHARACTER INFORMATION:
Name: {character.get('name', 'Unnamed Character')}
Description: {character.get('description', 'No description provided')}
Personality: {character.get('personality', 'No personality defined')}

THEME INFORMATION:
Theme: {theme.get('theme_name', 'No theme specified')}
Theme Description: {theme.get('theme_description', 'No theme description provided')}
Example Message: {theme.get('example_message', 'No example provided')}

This is prompt #{prompt_number}.
Time elapsed in session: {int(time_elapsed/60)} minutes and {int(time_elapsed%60)} seconds.
Time remaining in session: {int(time_remaining/60)} minutes and {int(time_remaining%60)} seconds.

IMPORTANT INSTRUCTIONS:
1. Generate a SHORT, concise writing prompt (1-3 sentences maximum)
2. Stay consistent with the character and theme
3. Make the prompt interesting and thought-provoking
4. Your response should ONLY include the prompt text - nothing else
5. Additionally, you should determine how soon the next prompt should appear (in seconds)

The timing of the next prompt should be contextually appropriate. For example:
- For normal prompts: 30-60 seconds might be appropriate
- For urgent situations: 15-30 seconds
- For dramatic moments: as little as 5-10 seconds
- For reflection: 60-90 seconds

FORMAT YOUR RESPONSE LIKE THIS:
[PROMPT] Your actual prompt text goes here.
[NEXT_INTERVAL] 30
[IS_COUNTDOWN] false
"""

    # Create user prompt
    if is_near_end:
        user_prompt = f"Generate the countdown sequence to conclude the writing session."
    else:
        user_prompt = f"Generate writing prompt #{prompt_number} with appropriate timing."
    
    # Call appropriate LLM backend
    if LLM_BACKEND == "lmstudio":
        response = call_lmstudio(system_prompt, user_prompt)
    elif LLM_BACKEND == "ollama":
        response = call_ollama(system_prompt, user_prompt)
    else:
        raise ValueError(f"Unsupported LLM backend: {LLM_BACKEND}")
    
    # Parse response to extract prompt and timing
    prompt_text = "Failed to generate prompt."
    next_interval = 30  # Default interval
    is_countdown = False
    countdown_from = None
    
    try:
        # Try to extract the prompt and timing using regex
        prompt_match = re.search(r'\[PROMPT\](.*?)(?:\[NEXT_INTERVAL\]|$)', response, re.DOTALL)
        interval_match = re.search(r'\[NEXT_INTERVAL\](.*?)(?:\[IS_COUNTDOWN\]|$)', response, re.DOTALL)
        countdown_match = re.search(r'\[IS_COUNTDOWN\](.*?)(?:\[COUNTDOWN_FROM\]|$)', response, re.DOTALL)
        countdown_from_match = re.search(r'\[COUNTDOWN_FROM\](.*?)$', response, re.DOTALL)
        
        if prompt_match:
            prompt_text = prompt_match.group(1).strip()
        else:
            # If no explicit prompt tag, use the whole response
            prompt_text = response.strip()
        
        if interval_match:
            try:
                next_interval = int(interval_match.group(1).strip())
                # Ensure interval is reasonable (between 1 and 300 seconds)
                next_interval = max(1, min(300, next_interval))
            except ValueError:
                next_interval = 30
        
        if countdown_match:
            countdown_text = countdown_match.group(1).strip().lower()
            is_countdown = countdown_text == "true"
        
        if countdown_from_match and is_countdown:
            try:
                countdown_from = int(countdown_from_match.group(1).strip())
                # Ensure countdown is reasonable (between 5 and 30)
                countdown_from = max(5, min(30, countdown_from))
            except ValueError:
                countdown_from = None
        
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        # If everything fails, use the raw response and default interval
        prompt_text = response.strip()
    
    return prompt_text, next_interval, is_countdown, countdown_from

def generate_countdown_number(character: Dict[str, str],
                             theme: Dict[str, str],
                             number: int,
                             is_final: bool = False) -> str:
    """
    Generate a countdown number with optional message
    
    Args:
        character: Dictionary containing character definition
        theme: Dictionary containing theme information
        number: The current countdown number
        is_final: Whether this is the final message (0 or chosen end number)
        
    Returns:
        String containing the countdown number and optional message
    """
    if is_final:
        system_prompt = f"""You are a creative writing prompt generator creating a final message for a countdown sequence.

CHARACTER INFORMATION:
Name: {character.get('name', 'Unnamed Character')}
Description: {character.get('description', 'No description provided')}
Personality: {character.get('personality', 'No personality defined')}

THEME INFORMATION:
Theme: {theme.get('theme_name', 'No theme specified')}
Theme Description: {theme.get('theme_description', 'No theme description provided')}

The countdown has reached {number}. This is the FINAL message of the writing session.

Create a dramatic, impactful final message that:
1. Is short (1-2 sentences)
2. Fits the character and theme
3. Provides a strong conclusion to the writing session
4. Mentions the number {number}

Your response should ONLY include the final message text.
"""
        user_prompt = f"Generate the final countdown message at number {number}."
    else:
        system_prompt = f"""You are a creative writing prompt generator creating a countdown number.

CHARACTER INFORMATION:
Name: {character.get('name', 'Unnamed Character')}
Description: {character.get('description', 'No description provided')}
Personality: {character.get('personality', 'No personality defined')}

THEME INFORMATION:
Theme: {theme.get('theme_name', 'No theme specified')}
Theme Description: {theme.get('theme_description', 'No theme description provided')}

You are counting down and the current number is {number}.

Create a very brief message that:
1. Is extremely short (just the number or the number with 5-10 words max)
2. Includes the number {number}
3. Maintains tension and urgency
4. Fits the character and theme

Your response should ONLY include the countdown message text.
"""
        user_prompt = f"Generate countdown text for number {number}."
    
    # Call appropriate LLM backend
    if LLM_BACKEND == "lmstudio":
        response = call_lmstudio(system_prompt, user_prompt)
    elif LLM_BACKEND == "ollama":
        response = call_ollama(system_prompt, user_prompt)
    else:
        raise ValueError(f"Unsupported LLM backend: {LLM_BACKEND}")
    
    return response.strip()

def generate_final_message(character: Dict[str, str], theme: Dict[str, str]) -> str:
    """Generate a final message for the session"""
    system_prompt = f"""You are a creative writing prompt generator creating a final message to conclude a writing session.

CHARACTER INFORMATION:
Name: {character.get('name', 'Unnamed Character')}
Description: {character.get('description', 'No description provided')}
Personality: {character.get('personality', 'No personality defined')}

THEME INFORMATION:
Theme: {theme.get('theme_name', 'No theme specified')}
Theme Description: {theme.get('theme_description', 'No theme description provided')}

Create a conclusive final message that:
1. Is short (1-2 sentences)
2. Fits the character and theme
3. Clearly signals the end of the writing session
4. Provides a sense of closure

Your response should ONLY include the final message text.
"""
    user_prompt = "Generate the final message to conclude the writing session."
    
    # Call appropriate LLM backend
    if LLM_BACKEND == "lmstudio":
        response = call_lmstudio(system_prompt, user_prompt)
    elif LLM_BACKEND == "ollama":
        response = call_ollama(system_prompt, user_prompt)
    else:
        raise ValueError(f"Unsupported LLM backend: {LLM_BACKEND}")
    
    return response.strip()

def call_lmstudio(system_prompt: str, user_prompt: str) -> str:
    """Call LMStudio API to generate a prompt"""
    url = f"{LLM_HOST}/v1/chat/completions"
    
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 250,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error calling LMStudio: {e}")
        return "Sorry, I couldn't generate a prompt at this time."

def call_ollama(system_prompt: str, user_prompt: str) -> str:
    """Call Ollama API to generate a prompt"""
    url = f"{LLM_HOST}/api/generate"
    
    # Combine system and user prompts for Ollama
    combined_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
    
    payload = {
        "model": LLM_MODEL,
        "prompt": combined_prompt,
        "temperature": 0.7,
        "max_tokens": 250
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["response"]
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return "Sorry, I couldn't generate a prompt at this time."

# Simple test function
if __name__ == "__main__":
    test_character = {
        "name": "Detective Sarah Chen",
        "description": "A brilliant detective with a troubled past",
        "personality": "Analytical, persistent, and slightly cynical"
    }
    
    test_theme = {
        "theme_name": "Mystery and noir in a futuristic setting",
        "theme_description": "A dark, rainy cyberpunk world where technology and crime intersect",
        "example_message": "The neon signs flickered through the rain-streaked window as Sarah examined the strange device. Something about this case felt... different."
    }
    
    # Test regular prompt generation
    prompt, interval, is_countdown, countdown_from = generate_prompt_with_timing(
        test_character, test_theme, 1, 60, 840
    )
    print(f"Generated prompt: {prompt}")
    print(f"Suggested interval: {interval} seconds")
    print(f"Is countdown: {is_countdown}")
    print(f"Countdown from: {countdown_from}")
    
    # Test countdown number generation
    countdown_text = generate_countdown_number(test_character, test_theme, 10)
    print(f"Countdown text: {countdown_text}")
    
    # Test final message
    final_text = generate_final_message(test_character, test_theme)
    print(f"Final message: {final_text}")