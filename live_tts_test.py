import asyncio
import json
import os
import sys
import wave
from pathlib import Path

from google import genai

MODEL = "gemini-3.1-flash-live-preview"
VOICE = os.getenv("GEMINI_VOICE", "Kore")
SAMPLE_RATE = 24_000

PERSONALITY = """A warm, modern English-learning studio. One Egyptian teacher speaks directly to the learner through the camera, as if teaching them personally. The setting is clean, comfortable, and visually simple. The teacher is friendly, confident, lightly humorous, and encouraging. This feels like a polished online lesson, not a podcast or formal classroom lecture. No background music plays beneath the explanation."""

SYSTEM_INSTRUCTION = f"""{PERSONALITY}

Act only as the voice renderer for the transcript the user provides.
Read the transcript in order and do not add commentary, introductions, conclusions, translations, or explanations.
Treat bracketed cues such as [WARM], [FRIENDLY], [AMUSED], [CLEAR], [CLEARLY], and [SLIGHTLY SLOWER] as delivery directions, not words to speak.
Treat the SSML-like <lang> and <phoneme> markup as pronunciation/language guidance, not literal words to speak. Speak the human-readable text inside the tags. When an IPA `ph` attribute is present, use it as pronunciation guidance for the enclosed text.
Preserve the Arabic/Egyptian Arabic and English wording and order exactly as much as the native-audio model allows.
Use a single Egyptian teacher voice throughout. No music or sound effects.
"""


def write_wav(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(pcm)


async def main() -> int:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is missing", file=sys.stderr)
        return 2

    transcript_path = Path("transcript.txt")
    transcript = transcript_path.read_text(encoding="utf-8")

    client = genai.Client(api_key=api_key)
    config = {
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {"voice_name": VOICE}
            }
        },
        "system_instruction": SYSTEM_INSTRUCTION,
        "output_audio_transcription": {},
        "thinking_config": {"thinking_level": "minimal"},
        "temperature": 0.5,
    }

    pcm_chunks: list[bytes] = []
    transcript_chunks: list[str] = []
    event_count = 0
    turn_complete = False

    print(f"Connecting to {MODEL} with voice={VOICE}")
    print(f"Input transcript chars: {len(transcript)}")

    try:
        async with client.aio.live.connect(model=MODEL, config=config) as session:
            await session.send_realtime_input(text=transcript)

            async for response in session.receive():
                event_count += 1
                server = response.server_content
                if not server:
                    continue

                if server.output_transcription and server.output_transcription.text:
                    transcript_chunks.append(server.output_transcription.text)

                if server.model_turn and server.model_turn.parts:
                    for part in server.model_turn.parts:
                        if part.inline_data and part.inline_data.data:
                            pcm_chunks.append(part.inline_data.data)

                if server.turn_complete:
                    turn_complete = True
                    break
    finally:
        await client.aio.aclose()

    pcm = b"".join(pcm_chunks)
    output_text = "".join(transcript_chunks)

    Path("output_transcription.txt").write_text(output_text, encoding="utf-8")
    Path("run_summary.json").write_text(
        json.dumps(
            {
                "model": MODEL,
                "voice": VOICE,
                "input_chars": len(transcript),
                "events": event_count,
                "turn_complete": turn_complete,
                "pcm_bytes": len(pcm),
                "seconds_at_24khz_pcm16_mono": round(len(pcm) / (SAMPLE_RATE * 2), 3),
                "output_transcription_chars": len(output_text),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    if not pcm:
        print("No audio bytes were returned by Gemini.", file=sys.stderr)
        print(Path("run_summary.json").read_text(encoding="utf-8"))
        return 1

    write_wav(Path("output.wav"), pcm)
    print(Path("run_summary.json").read_text(encoding="utf-8"))
    print("Wrote output.wav and output_transcription.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
