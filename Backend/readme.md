# 📝 YT-AI-Blog

**YT-AI-Blog** is a Django-powered web application that takes a YouTube video URL, extracts and transcribes the audio, and uses AI to generate a professional-style blog article based on the video content.

🎯 It combines:
- YouTube audio extraction via `yt-dlp`
- Speech-to-text transcription with AssemblyAI
- AI blog generation using OpenAI’s advanced models

---

## 🚀 Features

✔️ Accept a YouTube video link  
✔️ Download audio from the video  
✔️ Convert audio to text transcript  
✔️ Generate structured blog articles with AI  
✔️ User authentication (login/signup)  
✔️ JSON API for blog generation  

---

## 🧠 Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django |
| YouTube Extraction | yt-dlp |
| Transcription | AssemblyAI |
| AI Content | OpenAI API |
| Python Version | 3.9+ |
| Database | Django ORM (SQLite default) |

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/Sairaj-25/yt-ai-blog.git
cd yt-ai-blog
