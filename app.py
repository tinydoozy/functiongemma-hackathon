import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone

import streamlit as st

sys.path.insert(0, "cactus/python/src")

from cactus import cactus_destroy, cactus_init, cactus_transcribe
from boredbro.system_prompt import SYSTEM_PROMPT
from boredbro.tools_calendar import TOOLS_CALENDAR
from main import generate_cactus, generate_hybrid


WHISPER_MODEL_PATH = os.environ.get("WHISPER_MODEL_PATH", "cactus/weights/whisper-small")
WHISPER_PROMPT = "<|startoftranscript|><|en|><|transcribe|><|notimestamps|>"


def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """Transcribe WAV audio bytes with Cactus whisper model."""
    whisper = cactus_init(WHISPER_MODEL_PATH)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_bytes)
            tmp_path = f.name

        raw = cactus_transcribe(whisper, tmp_path, prompt=WHISPER_PROMPT)
        parsed = json.loads(raw)
        transcript = parsed.get("response", "")
        return transcript.strip()
    finally:
        cactus_destroy(whisper)
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


def run_agent(command_text: str, cloud_fallback: bool):
    """Run the tool-calling pipeline with either on-device-only or hybrid fallback."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": command_text},
    ]

    if cloud_fallback:
        result = generate_hybrid(messages, TOOLS_CALENDAR)
    else:
        result = generate_cactus(messages, TOOLS_CALENDAR)
        result["source"] = "on-device"

    if "function_calls" not in result:
        result["function_calls"] = []
    if "total_time_ms" not in result:
        result["total_time_ms"] = 0

    return result


def mock_execute(function_calls):
    """Demo-safe mock execution of calendar function calls."""
    if not function_calls:
        return {"ok": False, "message": "No function calls to execute."}, None

    call = function_calls[0]
    name = call.get("name")
    args = call.get("arguments", {})

    if name == "noop":
        return {"ok": True, "message": "No action needed."}, None

    if name == "ask_clarifying_question":
        q = args.get("question", "Can you clarify?")
        return {"ok": True, "message": f"Clarification requested: {q}"}, None

    if name == "create_event":
        title = args.get("title", "(untitled)")
        when_text = args.get("when_text", "(unspecified)")
        duration = args.get("duration_minutes", 60)
        location = args.get("location", "")
        msg = f"Would create event '{title}' at {when_text} for {duration} min"
        if location:
            msg += f" at {location}"
        ics_bytes = build_demo_ics(title=title, when_text=when_text, duration_minutes=duration, location=location)
        return {"ok": True, "message": msg}, ics_bytes

    if name == "find_event":
        return {
            "ok": True,
            "message": (
                "Would search calendar for "
                f"query='{args.get('query', '')}' in range "
                f"{args.get('start_when_text', '')} -> {args.get('end_when_text', '')}."
            ),
            "mock_results": [
                {"event_id": "evt_demo_1", "title": args.get("query", "Matched event")}
            ],
        }, None

    if name == "move_event":
        return {
            "ok": True,
            "message": f"Would move event {args.get('event_id', '(missing id)')} to {args.get('new_when_text', '(missing time)')}.",
        }, None

    if name == "cancel_event":
        return {
            "ok": True,
            "message": f"Would cancel event {args.get('event_id', '(missing id)')}.",
        }, None

    return {"ok": False, "message": f"Unknown tool: {name}"}, None


def build_demo_ics(title: str, when_text: str, duration_minutes: int = 60, location: str = "") -> bytes:
    """Build a simple .ics payload with synthetic timing and natural-language note."""
    start = datetime.now(timezone.utc).replace(microsecond=0)
    end = start + timedelta(minutes=int(duration_minutes or 60))
    uid = f"{uuid.uuid4()}@boredbro.local"
    description = f"Requested time: {when_text}"

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//BoredBro//Calendar Demo//EN",
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{start.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{start.strftime('%Y%m%dT%H%M%SZ')}",
        f"DTEND:{end.strftime('%Y%m%dT%H%M%SZ')}",
        f"SUMMARY:{title}",
        f"DESCRIPTION:{description}",
    ]

    if location:
        lines.append(f"LOCATION:{location}")

    lines.extend(["END:VEVENT", "END:VCALENDAR", ""])
    return "\r\n".join(lines).encode("utf-8")


def get_input_audio_bytes():
    """Try in-browser recording first, with uploader fallback."""
    audio_bytes = None

    if hasattr(st, "audio_input"):
        recording = st.audio_input("Record a voice command")
        if recording is not None:
            audio_bytes = recording.read()

    uploaded = st.file_uploader("Or upload a WAV/MP3/M4A file", type=["wav", "mp3", "m4a"])
    if uploaded is not None:
        audio_bytes = uploaded.read()

    return audio_bytes


def build_command_text(transcript: str, typed: str):
    source_text = transcript.strip() if transcript else ""
    if typed and typed.strip():
        source_text = typed.strip()

    pending_intent = st.session_state.get("pending_intent")
    if pending_intent:
        return (
            "STATE: pending_intent="
            + json.dumps(pending_intent)
            + "\nUSER_ANSWER: "
            + source_text
        )
    return source_text


def main():
    st.set_page_config(page_title="BoredBro Calendar Demo", layout="wide")
    st.title("BoredBro: Voice → Calendar Actions")

    st.session_state.setdefault("pending_intent", None)

    cloud_fallback = st.toggle("Cloud fallback (Gemini)", value=False)
    st.caption("When OFF: on-device only. When ON: use `generate_hybrid` with cloud fallback.")

    audio_bytes = get_input_audio_bytes()

    transcript = ""
    if st.button("Transcribe audio"):
        if not audio_bytes:
            st.warning("No audio provided yet. Record or upload audio first.")
        else:
            with st.spinner("Transcribing with Cactus..."):
                try:
                    transcript = transcribe_audio_bytes(audio_bytes)
                    st.session_state["latest_transcript"] = transcript
                except Exception as e:
                    st.error(f"Transcription failed: {e}")

    transcript = st.session_state.get("latest_transcript", "")
    st.subheader("Transcript")
    st.text_area("Transcript text", value=transcript, height=100, disabled=True)

    typed_command = st.text_input("Or type a command")

    if st.session_state.get("pending_intent"):
        st.info("Pending clarification in progress.")
        clarification = st.text_input("Answer the clarifying question", key="clarification_answer")
    else:
        clarification = ""

    run_clicked = st.button("Run pipeline", type="primary")

    if run_clicked:
        try:
            if clarification.strip():
                command_text = clarification.strip()
            else:
                command_text = build_command_text(transcript, typed_command)

            if not command_text.strip():
                st.warning("Please provide audio or type a command.")
                return

            with st.spinner("Running tool-calling pipeline..."):
                result = run_agent(command_text, cloud_fallback=cloud_fallback)

            function_calls = result.get("function_calls", [])
            execution_result, ics_bytes = mock_execute(function_calls)

            if function_calls and function_calls[0].get("name") == "ask_clarifying_question":
                st.session_state["pending_intent"] = {
                    "original_command": typed_command or transcript,
                    "question": function_calls[0].get("arguments", {}).get("question", "Can you clarify?"),
                }
                st.warning(f"Clarification: {st.session_state['pending_intent']['question']}")
            else:
                st.session_state["pending_intent"] = None

            st.subheader("Trace")
            c1, c2, c3 = st.columns(3)
            c1.metric("Source", result.get("source", "unknown"))
            confidence = result.get("confidence")
            c2.metric("Confidence", f"{confidence:.4f}" if isinstance(confidence, (int, float)) else "n/a")
            c3.metric("Total Time (ms)", f"{result.get('total_time_ms', 0):.2f}")

            st.markdown("**Function Calls JSON**")
            st.code(json.dumps(function_calls, indent=2), language="json")

            st.markdown("**Execution Result**")
            st.code(json.dumps(execution_result, indent=2), language="json")

            if ics_bytes is not None:
                default_name = "boredbro_event.ics"
                st.download_button(
                    "Export .ics",
                    data=ics_bytes,
                    file_name=default_name,
                    mime="text/calendar",
                )

        except Exception as e:
            st.error(f"Pipeline failed: {e}")

    with st.expander("Debug: tools + system prompt"):
        st.code(SYSTEM_PROMPT)
        st.code(json.dumps(TOOLS_CALENDAR, indent=2), language="json")


if __name__ == "__main__":
    main()
