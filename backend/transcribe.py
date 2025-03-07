import os
import tempfile
import subprocess
from datetime import timedelta
from typing import Optional
import openai
from dotenv import load_dotenv

# Load environment variables
# Try different paths to find the .env file
try:
    # First try the current directory
    if os.path.exists(".env"):
        load_dotenv(".env")
    # Then try the backend directory
    elif os.path.exists("backend/.env"):
        load_dotenv("backend/.env")
    # Then try absolute path
    elif os.path.exists("/Users/siddharthchauhan/Work/Projects/Zoom transcripts to MoM/backend/.env"):
        load_dotenv("/Users/siddharthchauhan/Work/Projects/Zoom transcripts to MoM/backend/.env")
    else:
        print("Warning: .env file not found in any expected location")
except Exception as e:
    print(f"Error loading environment variables: {e}")


# Get OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=api_key)

def convert_to_mp3(input_file: str) -> str:
    """Convert video/audio file to MP3 format for Whisper API processing"""
    print(f"Converting {input_file} to MP3 format...")
    
    # Get file extension
    file_ext = input_file.split('.')[-1].lower() if '.' in input_file else ""
    print(f"File extension: {file_ext}")
    
    # Create a temporary file with .mp3 extension
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        temp_mp3 = temp_file.name
    
    # Try different ffmpeg paths
    ffmpeg_paths = [
        '/opt/homebrew/bin/ffmpeg',  # Homebrew on Apple Silicon
        '/usr/local/bin/ffmpeg',     # Homebrew on Intel Mac
        'ffmpeg'                     # System path
    ]
    
    # Additional options for different formats
    conversion_options = [
        '-vn',             # No video
        '-ar', '44100',    # Audio sample rate
        '-ac', '2',        # Stereo
        '-b:a', '128k'     # Bitrate
    ]
    
    # Add format-specific options if needed
    if file_ext in ['webm', 'm4a', 'mp4']:
        # These formats might need additional processing
        conversion_options.extend(['-q:a', '0'])  # Use variable bitrate with highest quality
    
    # Try different ffmpeg paths
    success = False
    last_error = None
    
    for ffmpeg_path in ffmpeg_paths:
        try:
            print(f"Trying ffmpeg at: {ffmpeg_path}")
            result = subprocess.run(
                [ffmpeg_path, '-i', input_file] + conversion_options + [temp_mp3],
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True  # Get text output for better error messages
            )
            success = True
            print(f"Conversion successful using {ffmpeg_path}")
            break
        except subprocess.CalledProcessError as e:
            last_error = e
            print(f"Error with {ffmpeg_path}: {e.stderr if hasattr(e, 'stderr') else str(e)}")
            continue
        except FileNotFoundError:
            print(f"ffmpeg not found at {ffmpeg_path}, trying next path...")
            continue
    
    if not success:
        error_msg = str(last_error) if last_error else "All ffmpeg paths failed"
        raise RuntimeError(f"Failed to convert file: {error_msg}")
    
    # Check if conversion was successful by verifying file exists and has size > 0
    if not os.path.exists(temp_mp3) or os.path.getsize(temp_mp3) == 0:
        raise RuntimeError("Conversion seemed to succeed but output file is empty or missing")
    
    return temp_mp3


def format_timestamp(seconds: float) -> str:
    """Format timestamp from seconds to HH:MM:SS"""
    td = timedelta(seconds=seconds)
    minutes, seconds = divmod(td.seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def transcribe_audio(file_path: str) -> str:
    """Transcribe audio using OpenAI's whisper-1 API and format with timestamps"""
    print(f"Transcribing file: {file_path}")
    
    try:
        # Check file size first - large files can cause slow processing
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        print(f"File size: {file_size_mb:.2f} MB")
        
        if file_size_mb > 25:
            print("Warning: File is large (>25MB), processing may take longer")
        
        # Adding a simple time tracker
        import time
        start_time = time.time()
        
        # Send to OpenAI Whisper API directly - no conversion needed
        print("Sending to OpenAI Whisper API...")
        with open(file_path, "rb") as audio_file:
            # Request timestamps and other options
            response = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",  # Get detailed response with timestamps
                temperature=0.0  # Lower temperature for more accuracy
            )
            
        print(f"API call completed in {time.time() - start_time:.2f} seconds")
        
        # Format transcript with timestamps if available
        if isinstance(response, dict) and 'segments' in response:
            formatted_transcript = ""
            for segment in response['segments']:
                if 'start' in segment and 'end' in segment:
                    start_time = format_timestamp(segment['start'])
                    end_time = format_timestamp(segment['end'])
                    text = segment['text']
                    formatted_transcript += f"[{start_time} - {end_time}] {text}\n"
                else:
                    # Fallback if segments don't have timing info
                    formatted_transcript += f"{segment['text']}\n"
            
            return formatted_transcript
        else:
            # Fallback to just the text if no segment info
            return response['text'] if isinstance(response, dict) and 'text' in response else str(response)
    
    finally:
        # No temporary files to clean up since we're using the original file directly
        pass
