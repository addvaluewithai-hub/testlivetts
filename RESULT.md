# Gemini 3.1 Flash Live TTS test result

Tested on 2026-08-10 with GitHub Actions using the repository `GEMINI_API_KEY` secret.

- Model: `gemini-3.1-flash-live-preview`
- Google Gen AI Python SDK: `2.17.0`
- Voice: `Kore`
- Input transcript characters: `1346`
- Server events: `184`
- Turn complete: `true`
- PCM bytes returned: `2,784,002`
- Output format: mono 16-bit PCM WAV at 24 kHz
- Generated duration: `58.0` seconds
- Output audio transcription characters: `0`
- GitHub Actions run: `31368906762`
- GitHub Actions job: `93393252963`
- Artifact ID: `9055270479` (`gemini-live-tts-test`)
- Result: **SUCCESS** — Gemini returned native audio and the workflow wrote a valid WAV file.

The temporary PR used to make the test run observable through the GitHub connector was closed without merging. The permanent workflow remains on `main` and can also be run manually from GitHub Actions.
