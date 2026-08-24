import requests
import json


OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:3b"


def generate_meeting_analysis(transcript: str):
    """
    Send the meeting transcript to the local Ollama LLM
    and generate Summary, Key Decisions, and Action Items.
    """

    prompt = f"""
You are a professional meeting assistant.

Analyze the following meeting transcript.

Return ONLY valid JSON in this exact format:

{{
  "summary": "A clear short summary of the meeting.",
  "key_decisions": [
    "Decision 1",
    "Decision 2"
  ],
  "action_items": [
    {{
      "task": "Task description",
      "assignee": "Person responsible or Not specified",
      "deadline": "Deadline or Not specified"
    }}
  ]
}}

Important:
- Do not invent information.
- Only use information present in the transcript.
- Keep the summary concise.
- Extract actual decisions from the meeting.
- Extract actual tasks that someone needs to do.
- Include the person responsible when mentioned.
- Include the deadline when mentioned.
- If an assignee or deadline is not mentioned, use "Not specified".

Meeting transcript:

{transcript}
"""

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )

    response.raise_for_status()

    result = response.json()

    llm_text = result.get("response", "").strip()

    # Remove markdown code fences if the model adds them
    if llm_text.startswith("```"):
        llm_text = llm_text.replace("```json", "")
        llm_text = llm_text.replace("```", "")
        llm_text = llm_text.strip()

    try:
        return json.loads(llm_text)

    except json.JSONDecodeError:
        return {
            "summary": llm_text,
            "key_decisions": [],
            "action_items": []
        }