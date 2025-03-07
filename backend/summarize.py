import os
import openai
from typing import Optional

# Check if OpenAI API key is set
api_key = os.getenv("OPENAI_API_KEY")

def generate_minutes(transcript: str) -> str:
    """Generate meeting minutes from a transcript using OpenAI API"""
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    # Clean the transcript (remove timestamps if present)
    clean_transcript = ""
    for line in transcript.split("\n"):
        # Skip empty lines
        if not line.strip():
            continue
        # Remove timestamps if they exist (in format [00:00:00 - 00:00:00])
        if line.strip().startswith("[") and "]" in line:
            # Extract content after the timestamp
            parts = line.split("]")
            if len(parts) > 1:
                clean_transcript += parts[1].strip() + "\n"
        else:
            # Keep the line as is if no timestamp
            clean_transcript += line.strip() + "\n"
    
    # System prompt for meeting minutes generation
    system_prompt = """You are an expert assistant that creates concise and well-structured meeting minutes from transcripts. 
    Focus on extracting and organizing key discussion points, decisions, action items, and assignments.
    Format the minutes with clear sections for: 
    1. Meeting Overview
    2. Key Points Discussed
    3. Decisions Made
    4. Action Items (with assigned persons if mentioned)
    5. Next Steps
    
    Use professional language and be concise yet thorough."""
    
    # Call the OpenAI API to generate meeting minutes
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": clean_transcript}
        ]
    )
    
    # Extract and return the generated minutes
    if hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content
    else:
        return "Error: Failed to generate meeting minutes."
