import os
import subprocess
import streamlit as st
from faster_whisper import WhisperModel
import json
from lecture_rag_pipeline import LectureRAGPipeline

# --- Directories ---
os.makedirs("uploads", exist_ok=True)
os.makedirs("audio", exist_ok=True)
os.makedirs("transcripts", exist_ok=True)

# --- Audio extraction using FFmpeg ---
def extract_audio_ffmpeg(video_path: str, output_audio_path: str):
    command = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1", output_audio_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise Exception(result.stderr.decode())

# --- Whisper Model Loader ---
@st.cache_resource
def load_model():
    return WhisperModel("tiny", device="cuda", compute_type="float16")

# --- Transcribe ---
def transcribe_audio(model, audio_path):
    segments, info = model.transcribe(audio_path, beam_size=5, language="en")
    transcript_segments = []
    full_text = ""
    for seg in segments:
        text = seg.text.strip()
        start = round(seg.start, 2)
        end = round(seg.end, 2)
        transcript_segments.append({"start": start, "end": end, "text": text})
        full_text += f"[{start}s - {end}s] {text}\n"
    return full_text, transcript_segments

# --- Save Transcript JSON ---
def save_transcript(segments, video_id):
    path = f"transcripts/{video_id}.json"
    enriched = [{"video_id": video_id, **s} for s in segments]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)
    return path

# --- Main UI ---
st.title("🎓 Lecture Intelligence Assistant")

# --- Video Upload ---
uploaded_file = st.file_uploader("📤 Upload Lecture Video (.mp4)", type=["mp4"])
if uploaded_file:
    video_path = f"uploads/{uploaded_file.name}"
    with open(video_path, "wb") as f:
        f.write(uploaded_file.read())
    st.success(f"Video saved at: {video_path}")

    audio_path = f"audio/{uploaded_file.name.replace('.mp4', '.wav')}"

    st.info("🔊 Extracting audio...")
    try:
        extract_audio_ffmpeg(video_path, audio_path)
        st.success(f"Audio extracted at: {audio_path}")
    except Exception as e:
        st.error(f"❌ Audio extraction failed: {e}")

    st.info("🧠 Transcribing with Whisper...")
    try:
        model = load_model()
        full_text, segments = transcribe_audio(model, audio_path)
        st.success("✅ Transcription complete!")

        with st.expander("📄 Transcript Preview"):
            st.text(full_text)

        with st.expander("📋 Timestamped Segments"):
            for s in segments:
                st.markdown(f"**[{s['start']}s - {s['end']}s]**: {s['text']}")

        video_id = uploaded_file.name.replace(".mp4", "")
        save_transcript(segments, video_id)
        st.success("📁 Transcript saved!")

    except Exception as e:
        st.error(f"❌ Transcription failed: {e}")

st.markdown("---")

# --- Lecture Selection UI ---
video_files = [f for f in os.listdir("uploads") if f.endswith(".mp4")]
selected_video = st.selectbox("🎬 Select a Lecture to Explore", video_files)

if selected_video:
    video_path = f"uploads/{selected_video}"
    video_id = selected_video.replace(".mp4", "")

    col1, col2 = st.columns([1, 1.5])
    with col1:
        st.video(video_path)

    with col2:
        st.markdown("### 📝 Transcript Segments")
        transcript_path = f"transcripts/{video_id}.json"
        if os.path.exists(transcript_path):
            with open(transcript_path, "r", encoding="utf-8") as f:
                segments = json.load(f)
            for i, s in enumerate(segments):
                start = s["start"]
                end = s["end"]
                text = s["text"]
                st.markdown(f"**[{start}s - {end}s]**: {text}")
                if st.button(f"▶ Jump to {start}s", key=f"jump-{i}"):
                    st.session_state["jump_to"] = start      
        else:
            st.warning("Transcript not found. Run transcription first.")

    st.markdown("---")
    st.subheader("💬 Ask a question from this lecture")

    query = st.text_input("Your Question")
    if query:
        rag = LectureRAGPipeline()
        rag.run_pipeline(video_id)
        result = rag.qa_chain({"query": query}, return_source_documents=True)

        st.markdown("**🧠 Answer:**")
        st.write(result["result"])

        st.markdown("### 🔗 Matched Transcript Segments")

