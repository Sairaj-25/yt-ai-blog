# Django shortcuts for rendering templates and redirecting users
from django.shortcuts import render, redirect

# Django authentication utilities
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# CSRF exemption for API-style POST requests (used for AJAX/fetch)
from django.views.decorators.csrf import csrf_exempt

# Used to send JSON responses instead of HTML
from django.http import JsonResponse

# Access Django settings (MEDIA_ROOT, etc.)
from django.conf import settings

# Standard libraries
import json              # Parse JSON request bodies
import os                # File handling + environment variables
import time              # (Optional) delays / retries

# YouTube audio download library
from yt_dlp import YoutubeDL

# AssemblyAI for speech-to-text
import assemblyai as aai

# OpenAI modern client (v1+)
from openai import OpenAI
from openai import OpenAIError, RateLimitError, AuthenticationError


# -----------------------------
# GLOBAL CLIENT CONFIGURATION
# -----------------------------

# Create OpenAI client using API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set AssemblyAI API key from environment variable
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")


# -----------------------------
# HOME PAGE VIEW
# -----------------------------

@login_required  # Ensures only logged-in users can access this page
def index(request):
    return render(request, "index.html")  # Renders the homepage template


# -----------------------------
# MAIN BLOG GENERATION API
# -----------------------------

@csrf_exempt  # Disable CSRF since this is an API-style POST request
def generate_blog(request):
    # Allow only POST requests
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        # Parse JSON body from frontend fetch request
        data = json.loads(request.body)

        # Extract YouTube link from request
        yt_link = data.get("link")

        # Validate input
        if not yt_link:
            return JsonResponse({"error": "YouTube link is required"}, status=400)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)

    # Fetch YouTube video title
    title = yt_title(yt_link)
    if not title:
        return JsonResponse({"error": "Failed to fetch YouTube title"}, status=500)

    # Convert YouTube audio → text transcript
    transcription = get_transcription(yt_link)
    if not transcription:
        return JsonResponse({"error": "Failed to get transcript"}, status=500)

    # Generate blog article from transcript using OpenAI
    blog_content = generate_blog_from_transcription(transcription)
    if not blog_content:
        return JsonResponse({"error": "Failed to generate blog article"}, status=500)

    # Return generated content as JSON (used by frontend)
    return JsonResponse({
        "title": title,
        "content": blog_content
    })


# -----------------------------
# YOUTUBE TITLE FETCHER
# -----------------------------

def yt_title(link):
    """
    Extracts the video title without downloading the video
    """
    try:
        # YoutubeDL fetches metadata only (download=False)
        with YoutubeDL() as ydl:
            info = ydl.extract_info(link, download=False)

            # Safely return title
            return info.get("title", "Unknown Title")

    except Exception as e:
        print(f"YouTube title error: {e}")
        return None


# -----------------------------
# AUDIO DOWNLOADER
# -----------------------------

def download_audio(link):
    """
    Downloads YouTube audio and converts it to MP3
    """
    try:
        ydl_opts = {
            "format": "bestaudio/best",  # Best available audio
            "outtmpl": os.path.join(settings.MEDIA_ROOT, "%(title)s.%(ext)s"),

            # Converts audio to MP3 using FFmpeg
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }

        # Download audio
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)

            # Construct final mp3 file path
            mp3_path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
            return mp3_path

    except Exception as e:
        print(f"Audio download error: {e}")
        return None


# -----------------------------
# TRANSCRIPTION USING ASSEMBLYAI
# -----------------------------

def get_transcription(link):
    """
    Converts YouTube audio into text using AssemblyAI
    """
    try:
        # Download audio from YouTube
        audio_file = download_audio(link)
        if not audio_file:
            return None

        # Create AssemblyAI transcriber
        transcriber = aai.Transcriber()

        # Perform speech-to-text
        transcript = transcriber.transcribe(audio_file)

        # Delete audio file after transcription (cleanup)
        os.remove(audio_file)

        # Return transcript text
        return transcript.text

    except Exception as e:
        print(f"Transcription error: {e}")
        return None


# -----------------------------
# BLOG GENERATION USING OPENAI
# -----------------------------

def generate_blog_from_transcription(transcription):
    """
    Uses OpenAI to generate a structured blog article
    """
    try:
        # Prompt sent to OpenAI
        prompt = f"""
Write a professional blog article using the following transcript.
The article must include:
- A catchy title
- Introduction
- Clear headings
- Conclusion

Transcript:
{transcription}
"""

        # Call OpenAI Chat Completion API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert blog writer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,   # Creativity level
            max_tokens=1500    # Response length
        )

        # Extract and return generated text
        return response.choices[0].message.content.strip()

    except RateLimitError:
        return "Rate limit exceeded. Please try again later."

    except AuthenticationError:
        return "Invalid OpenAI API key."

    except OpenAIError as e:
        return f"OpenAI error: {str(e)}"


# -----------------------------
# AUTH FUNCTIONS (NO COMMENTS)
# -----------------------------

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')
        return render(request, 'Login.html', {'error_message': 'Invalid credentials'})
    return render(request, 'Login.html')


def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

        if password == repeatPassword:
            user = User.objects.create_user(username, email, password)
            login(request, user)
            return redirect('/')
        return render(request, 'signup.html', {'error_message': 'Passwords do not match'})
    return render(request, 'signup.html')


def user_logout(request):
    logout(request)
    return redirect('/')
