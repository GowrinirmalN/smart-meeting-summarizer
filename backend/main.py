from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from faster_whisper import WhisperModel
import requests
import tempfile
import os
import json
import re

# ============================================================
# CONFIGURATION
# ============================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"

# Faster-Whisper model
# "base" is a good starting point for a normal laptop.
WHISPER_MODEL = "base"

# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="Smart Meeting Platform API",
    description="Meeting transcription and AI summarization API",
    version="1.0.0"
)

# Allow React frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# LOAD WHISPER
# ============================================================

print("Loading Faster-Whisper model...")

whisper_model = WhisperModel(
    WHISPER_MODEL,
    device="cpu",
    compute_type="int8"
)

print("Faster-Whisper loaded successfully.")


# ============================================================
# CHECK OLLAMA
# ============================================================

def check_ollama():
    try:
        response = requests.get(
            "http://localhost:11434/api/tags",
            timeout=5
        )

        if response.status_code == 200:
            return True

        return False

    except Exception:
        return False


# ============================================================
# TRANSCRIBE AUDIO
# ============================================================

def transcribe_audio(file_path):
    print("Starting transcription...")

    segments, info = whisper_model.transcribe(
        file_path,
        beam_size=5,
        vad_filter=True
    )

    transcript_parts = []

    for segment in segments:
        text = segment.text.strip()

        if text:
            transcript_parts.append(text)

    transcript = " ".join(transcript_parts)

    print("Transcription completed.")

    return transcript


# ============================================================
# ASK OLLAMA
# ============================================================

def ask_ollama(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2
                }
            },
            timeout=300
        )

        response.raise_for_status()

        data = response.json()

        return data.get("response", "").strip()

    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Ollama is not running. "
                "Open PowerShell and run: ollama serve"
            )
        )

    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Ollama took too long to respond."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ollama error: {str(e)}"
        )


# ============================================================
# CLEAN LLM RESPONSE
# ============================================================

def clean_json_response(text):
    """
    Removes markdown code fences if the LLM returns:

    ```json
    {...}
    ```
    """

    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


# ============================================================
# GENERATE MEETING ANALYSIS
# ============================================================

def generate_meeting_analysis(transcript):

    prompt = f"""
You are an AI meeting assistant.

Analyze the following meeting transcript.

Return ONLY valid JSON.
Do not use markdown.
Do not put the JSON inside ```.

Use exactly this structure:

{{
  "summary": "A clear natural-language summary of the meeting.",
  "key_decisions": [
    "Decision 1",
    "Decision 2"
  ],
  "action_items": [
    {{
      "task": "Task description",
      "assignee": "Person responsible or Unknown",
      "deadline": "Deadline if mentioned or Not specified"
    }}
  ]
}}

Important:
- Do not invent information.
- Only use information found in the transcript.
- If there are no decisions, return an empty list.
- If there are no action items, return an empty list.
- Keep the summary concise but useful.
- Identify names when they are clearly mentioned.
- Identify deadlines when they are clearly mentioned.

MEETING TRANSCRIPT:

{transcript}
"""

    llm_response = ask_ollama(prompt)

    cleaned = clean_json_response(llm_response)

    try:
        result = json.loads(cleaned)

        return {
            "summary": result.get("summary", ""),
            "key_decisions": result.get("key_decisions", []),
            "action_items": result.get("action_items", [])
        }

    except json.JSONDecodeError:

        # If the model does not return perfect JSON,
        # still provide the response to the frontend.

        return {
            "summary": llm_response,
            "key_decisions": [],
            "action_items": []
        }


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "Smart Meeting Platform API is running",
        "whisper_model": WHISPER_MODEL,
        "ollama_model": OLLAMA_MODEL
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    ollama_running = check_ollama()

    return {
        "status": "ok",
        "whisper": "ready",
        "ollama": "ready" if ollama_running else "not running",
        "model": OLLAMA_MODEL
    }


# ============================================================
# TRANSCRIBE ONLY
# ============================================================

@app.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    allowed_extensions = [
        ".mp3",
        ".wav",
        ".m4a",
        ".mp4",
        ".webm",
        ".mpeg",
        ".mpga"
    ]

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Use MP3, WAV, M4A, MP4, or WebM."
            )
        )

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp_file:

            content = await file.read()

            temp_file.write(content)

            temp_path = temp_file.name

        transcript = transcribe_audio(temp_path)

        return {
            "success": True,
            "filename": file.filename,
            "transcript": transcript
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

    finally:

        if temp_path and os.path.exists(temp_path):

            try:
                os.remove(temp_path)
            except Exception:
                pass


# ============================================================
# FULL MEETING SUMMARIZER
# ============================================================

@app.post("/summarize")
async def summarize(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    allowed_extensions = [
        ".mp3",
        ".wav",
        ".m4a",
        ".mp4",
        ".webm",
        ".mpeg",
        ".mpga"
    ]

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio/video file."
        )

    # Check Ollama before starting expensive transcription
    if not check_ollama():

        raise HTTPException(
            status_code=503,
            detail=(
                "Ollama is not running. "
                "Open another PowerShell window and run "
                "'ollama serve'."
            )
        )

    temp_path = None

    try:

        # ----------------------------------------------------
        # Save uploaded file temporarily
        # ----------------------------------------------------

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension
        ) as temp_file:

            content = await file.read()

            temp_file.write(content)

            temp_path = temp_file.name

        # ----------------------------------------------------
        # STEP 1: SPEECH → TEXT
        # ----------------------------------------------------

        transcript = transcribe_audio(temp_path)

        if not transcript.strip():

            raise HTTPException(
                status_code=400,
                detail="No speech was detected in the file."
            )

        # ----------------------------------------------------
        # STEP 2: TEXT → LLM
        # ----------------------------------------------------

        analysis = generate_meeting_analysis(transcript)

        # ----------------------------------------------------
        # RETURN EVERYTHING TO REACT
        # ----------------------------------------------------

        return {
            "success": True,
            "filename": file.filename,
            "transcript": transcript,
            "summary": analysis["summary"],
            "key_decisions": analysis["key_decisions"],
            "action_items": analysis["action_items"]
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Meeting processing failed: {str(e)}"
        )

    finally:

        if temp_path and os.path.exists(temp_path):

            try:
                os.remove(temp_path)
            except Exception:
                pass


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    import uvicorn

    print("")
    print("==============================================")
    print("     SMART MEETING PLATFORM BACKEND")
    print("==============================================")
    print("")
    print("Whisper model :", WHISPER_MODEL)
    print("Ollama model  :", OLLAMA_MODEL)
    print("")
    print("API running at:")
    print("http://127.0.0.1:8001")
    print("")
    print("==============================================")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001
    )