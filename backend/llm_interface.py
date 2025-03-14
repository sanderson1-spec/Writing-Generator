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

The writing session is about to end. You need to INITIATE a countdown sequence to conclude the session.

CHARACTER INFORMATION:
Name: {character.get('name', 'Unnamed Character')}
Description: {character.get('description', 'No description provided')}
Personality: {character.get('personality', 'No personality defined')}

THEME INFORMATION:
Theme: {theme.get('theme_name', 'No theme specified')}
Theme Description: {theme.get('theme_description', 'No theme description provided')}
Example Message: {theme.get('example_message', 'No example provided')}

Time remaining in session: {int(time_remaining)} seconds.

EXTREMELY IMPORTANT INSTRUCTIONS:
1. You are ONLY creating the INITIAL announcement that a countdown will begin
2. Choose a starting number between 10 and 20
3. DO NOT list any of the actual countdown numbers - the system will handle that part
4. Only write a brief message announcing that the countdown is starting
5. Your response must STRICTLY follow this exact format with square brackets:

[PROMPT] Time is running out! The countdown begins from 15.
[NEXT_INTERVAL] 1
[IS_COUNTDOWN] true
[COUNTDOWN_FROM] 15

CRITICAL: DO NOT include the actual countdown sequence. The application will generate each number separately.
DO NOT include ANY other text or explanations in your response.
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
4. Your response must STRICTLY follow this exact format with square brackets:

[PROMPT] Your actual prompt text goes here.
[NEXT_INTERVAL] 30
[IS_COUNTDOWN] false

Do not include ANY other text, explanations, or preambles in your response.
"""

    # Create user prompt
    if is_near_end:
        user_prompt = f"INITIATE a countdown for the conclusion of the writing session. ONLY create the starting announcement, not the whole countdown. Remember to use the exact format with square brackets."
    else:
        user_prompt = f"Generate writing prompt #{prompt_number} with appropriate timing. Remember to use the exact format with square brackets."
    
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
        # First try to extract using the standard bracket format
        prompt_match = re.search(r'\[PROMPT\](.*?)(?:\[NEXT_INTERVAL\]|$)', response, re.DOTALL)
        interval_match = re.search(r'\[NEXT_INTERVAL\](.*?)(?:\[IS_COUNTDOWN\]|$)', response, re.DOTALL)
        countdown_match = re.search(r'\[IS_COUNTDOWN\](.*?)(?:\[COUNTDOWN_FROM\]|$)', response, re.DOTALL)
        countdown_from_match = re.search(r'\[COUNTDOWN_FROM\](.*?)$', response, re.DOTALL)
        
        # If standard format found, parse it
        if prompt_match:
            prompt_text = prompt_match.group(1).strip()
            
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
        else:
            # Try alternate formats (natural language)
            # Extract potential prompt text by removing metadata phrases
            clean_text = response
            
            # Remove common metadata phrases
            metadata_patterns = [
                r'(?i)Here is (?:the|a|the \w+) (?:prompt|writing prompt):?\s*["""]?(.*?)["""]?(?:\s*\(.*?\)|\s*NEXT_INTERVAL|\s*Next interval|\s*\[|\s*$)',
                r'(?i)NEXT_INTERVAL:?\s*(\d+)(?:\s*seconds?)?',
                r'(?i)IS_COUNTDOWN:?\s*(true|false)',
                r'(?i)COUNTDOWN_FROM:?\s*(\d+)',
                r'(?i)Your (?:actual )?(?:prompt )?text:?\s*["""]?(.*?)["""]?(?:\s*NEXT_INTERVAL|\s*Next interval|\s*$)',
                r'(?i)Prompt:?\s*["""]?(.*?)["""]?(?:\s*\(.*?\)|\s*NEXT_INTERVAL|\s*Next interval|\s*\[|\s*$)',
                r'(?i)["""]?(.*?)["""]?(?:\s*\(\d+\s*(?:minute|second)s?(?:\s+\d+\s+(?:minute|second)s?)?\))'
            ]
            
            # Try to extract prompt text
            for pattern in metadata_patterns:
                if 'NEXT_INTERVAL' not in pattern and 'Next interval' not in pattern:
                    match = re.search(pattern, response, re.DOTALL)
                    if match:
                        clean_text = match.group(1).strip()
                        break
            
            # Try to extract interval
            interval_natural = re.search(r'(?i)NEXT_INTERVAL:?\s*(\d+)(?:\s*seconds?)?', response)
            if interval_natural:
                try:
                    next_interval = int(interval_natural.group(1).strip())
                    next_interval = max(1, min(300, next_interval))
                except ValueError:
                    pass
            
            # Try to extract countdown flag
            countdown_natural = re.search(r'(?i)IS_COUNTDOWN:?\s*(true|false)', response)
            if countdown_natural:
                is_countdown = countdown_natural.group(1).strip().lower() == "true"
            
            # Try to extract countdown_from
            countdown_from_natural = re.search(r'(?i)COUNTDOWN_FROM:?\s*(\d+)', response)
            if countdown_from_natural and is_countdown:
                try:
                    countdown_from = int(countdown_from_natural.group(1).strip())
                    countdown_from = max(5, min(30, countdown_from))
                except ValueError:
                    pass
            
            prompt_text = clean_text
        
    except Exception as e:
        print(f"Error parsing LLM response: {e}")
        # If everything fails, try to clean the response as much as possible
        clean_text = response
        
        # Last-resort cleanup: remove common metadata indicators
        clean_text = re.sub(r'(?i)NEXT_INTERVAL:?\s*\d+(?:\s*seconds?)?', '', clean_text)
        clean_text = re.sub(r'(?i)IS_COUNTDOWN:?\s*(?:true|false)', '', clean_text)
        clean_text = re.sub(r'(?i)COUNTDOWN_FROM:?\s*\d+', '', clean_text)
        clean_text = re.sub(r'(?i)Here is (?:the|a|the \w+) (?:prompt|writing prompt):?\s*', '', clean_text)
        clean_text = re.sub(r'(?i)(?:\(.*?(?:second|minute)s?.*?\))', '', clean_text)
        clean_text = re.sub(r'(?i)next(?: interval)?:?\s*\d+(?:\s*seconds?)?', '', clean_text)
        clean_text = re.sub(r'(?i)wait\s+(?:for|time):?\s*\d+(?:\s*seconds?)?', '', clean_text)
        clean_text = re.sub(r'^\s*["\']|["\'](?:\s*$|\s*\[)', '', clean_text)
        
        prompt_text = clean_text.strip()
    
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
1. Is short (1-2 sentences maximum)
2. Fits the character and theme
3. Provides a strong conclusion to the writing session
4. Mentions the number {number}

IMPORTANT: Your response should ONLY include the final message text.
DO NOT include any explanatory text, additional countdown numbers, or labels.
DO NOT list multiple numbers. Only mention the number {number}.
"""
        user_prompt = f"Generate ONLY the final countdown message at number {number}. Return ONLY the message itself with no additional numbers or explanation."
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
1. Is extremely short (just the number or the number with 5-10 words maximum)
2. Includes ONLY the number {number} - do not list other numbers
3. Maintains tension and urgency
4. Fits the character and theme

IMPORTANT: Your response should ONLY include the countdown text for number {number}.
DO NOT include any explanatory text, additional countdown numbers, or labels.
DO NOT continue the countdown - ONLY provide text for number {number}.
"""
        user_prompt = f"Generate ONLY the countdown text for the number {number}. Return ONLY the message with no other numbers or explanation."
    
    # Call appropriate LLM backend
    if LLM_BACKEND == "lmstudio":
        response = call_lmstudio(system_prompt, user_prompt)
    elif LLM_BACKEND == "ollama":
        response = call_ollama(system_prompt, user_prompt)
    else:
        raise ValueError(f"Unsupported LLM backend: {LLM_BACKEND}")
    
    # Clean up the response - remove any explanatory text
    clean_response = re.sub(r'(?i)^.*?(?:here is|countdown message:|final message:|countdown number:|message:|text:)\s*', '', response, flags=re.DOTALL)
    
    # Extract only the current number if it contains a sequence of numbers
    number_str = str(number)
    number_pattern = r'(?<!\d)' + re.escape(number_str) + r'(?!\d)' # Match exact number with word boundaries
    
    number_match = re.search(number_pattern + r'[^\d]*?(?=\d|$)', clean_response)
    if number_match:
        # Try to extract just the part with the current number
        clean_response = number_match.group(0).strip()
    else:
        # Remove any numbers that aren't the current number
        numbers_to_remove = r'\b(?:' + '|'.join([str(n) for n in range(1, 31) if n != number]) + r')\b'
        clean_response = re.sub(numbers_to_remove, '', clean_response)
    
    # Remove any ranges or sequences like "10, 9, 8..."
    clean_response = re.sub(r'\d+\s*[,\-\.\…]+\s*\d+(?:\s*[,\-\.\…]+\s*\d+)*', '', clean_response)
    
    # If there are quotes around the response, remove them
    clean_response = re.sub(r'^["\']|["\']$', '', clean_response.strip())
    
    # Ensure the number is present in the output
    if number_str not in clean_response:
        clean_response = f"{number_str}: {clean_response}"
    
    return clean_response.strip()

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
DO NOT include any explanatory text or labels before or after the message.
"""
    user_prompt = "Generate the final message to conclude the writing session. Only include the message itself."
    
    # Call appropriate LLM backend
    if LLM_BACKEND == "lmstudio":
        response = call_lmstudio(system_prompt, user_prompt)
    elif LLM_BACKEND == "ollama":
        response = call_ollama(system_prompt, user_prompt)
    else:
        raise ValueError(f"Unsupported LLM backend: {LLM_BACKEND}")
    
    # Clean up the response - remove any explanatory text
    clean_response = re.sub(r'(?i)^.*?(?:here is|final message:|message:|text:)\s*', '', response, flags=re.DOTALL)
    
    # If there are quotes around the response, remove them
    clean_response = re.sub(r'^["\']|["\']$', '', clean_response.strip())
    
    return clean_response.strip()

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