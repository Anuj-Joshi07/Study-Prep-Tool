# JEE Video to Notes & Practice Generator

A Gen AI project that converts YouTube lecture videos into textbook-style notes, fetches previous year questions (PYQs), and generates practice questions.

## Features

- **Transcript Extraction**: Uses faster-whisper to transcribe YouTube videos
- **Smart Summarization**: Converts transcripts into structured textbook-style notes
- **PYQ Database**: Fetches relevant previous year questions from local CSV
- **Practice Questions**: Generates custom practice questions using LLM

## Prerequisites

1. **Python 3.13+**
2. **LLM Backend** (choose one):
   - **Option A: Ollama** (local, free): Download from https://ollama.ai
   - **Option B: Google Gemini API** (cloud, requires API key): Get key from https://aistudio.google.com/apikey
3. **FFmpeg** (for audio processing): Download from https://ffmpeg.org

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Choose Your LLM Backend

#### Option A: Using Ollama (Local)

1. Download Ollama from https://ollama.ai
2. Install it on your system
3. Pull the llama3 model:
   ```bash
   ollama pull llama3
   ```
4. Start Ollama server (it usually runs automatically after installation)
5. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

#### Option B: Using Google Gemini (Cloud)

1. Get your API key from https://aistudio.google.com/apikey
2. Update the `.env` file with your Gemini API key:
   ```
   GEMINI_API_KEY="your-api-key-here"
   ```
3. Run the Gemini version:
   ```bash
   uvicorn main_gemini:app --reload
   ```

### 3. Configure Environment Variables

The `.env` file contains API keys:
- `HF_TOKEN`: Hugging Face token (for model downloads, optional)
- `GEMINI_API_KEY`: Google Gemini API key (required if using Gemini)

## Usage

1. Open your browser and go to `http://localhost:8000`
2. Paste a YouTube lecture URL
3. Select subject, chapter (optional), and mode:
   - **Fast mode**: Only generates transcript and notes
   - **Full mode**: Generates transcript, notes, and practice questions
4. Click "Analyze Video"

## Available Versions

- `main.py`: Uses Ollama (local LLM)
- `main_gemini.py`: Uses Google Gemini API (cloud LLM)

Run with:
```bash
# For Ollama version
uvicorn main:app --reload

# For Gemini version
uvicorn main_gemini:app --reload
```

## API Endpoints

### POST /analyze

Analyzes a YouTube video and returns notes, PYQs, and practice questions.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "subject": "Physics",
  "chapter": "Mechanics",
  "mode": "full"
}
```

**Response:**
```json
{
  "summary": "Textbook-style notes...",
  "pyqs": [...],
  "practice_questions": "Generated questions...",
  "mode": "full"
}
```

## Project Structure

```
.
├── agents/              # AI agents for different tasks
│   ├── transcript_agent.py    # YouTube transcription
│   ├── summarizer_agent.py    # Note generation
│   ├── pyq_agent.py           # PYQ fetching
│   └── practice_agent.py      # Practice question generation
├── data/
│   └── pyqs.csv        # Previous year questions database
├── frontend/
│   └── index.html      # Web UI
├── main.py             # FastAPI application
├── requirements.txt    # Python dependencies
└── .env               # Environment variables
```

## Troubleshooting

### Ollama Connection Error
- Make sure Ollama is installed and running
- Check if the service is accessible at `http://localhost:11434`
- Try: `ollama serve` to start the server manually

### Whisper Model Download
- First run will download the Whisper model (may take time)
- Models are cached for future use

### FFmpeg Not Found
- Install FFmpeg from https://ffmpeg.org
- Add FFmpeg to your system PATH

## Notes

- The first run will be slower as models are downloaded
- Transcription time depends on video length
- Full mode with practice questions takes longer due to LLM generation
