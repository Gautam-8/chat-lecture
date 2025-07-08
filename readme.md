A Streamlit-based tool that lets you upload lecture videos, transcribe them using AI, and ask questions about the content using RAG (Retrieval-Augmented Generation).

---

## 🔧 Features

- 📤 Upload lecture videos (MP4)
- 🔊 Extract audio using FFmpeg
- 🧠 Transcribe using Whisper AI (via faster-whisper)
- ✂️ Chunk and store transcript into vector DB (Chroma)
- 🤖 Ask questions and get answers using local LLM
- 🗂 View video and timestamped transcript side-by-side

---

## 🧠 AI Models Used

| Task           | Model                   | Source                                                                   |
| -------------- | ----------------------- | ------------------------------------------------------------------------ |
| Transcription  | `Whisper-tiny`          | [faster-whisper](https://github.com/guillaumekln/faster-whisper) (local) |
| Embeddings     | `nomic-embed-text-v1.5` | via [LM Studio](https://lmstudio.ai)                                     |
| Chat/Answering | `google/gemma-3-4b`     | via [LM Studio](https://lmstudio.ai)                                     |

> ✅ All models are used **offline** via LM Studio for full local control.

---

## 📦 Dependencies

Make sure these are installed in your virtual environment:

### 🐍 Python Packages

- `streamlit`
- `faster-whisper`
- `langchain`
- `langchain-community`
- `ffmpeg-python`

Install with:

````bash
pip install -r requirements.txt


```run
streamlite run app.py
````
