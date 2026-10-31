# Implementation Plan — Deepgram STT for Home Assistant

## Goal

Ship a HACS-installable Home Assistant custom integration that turns Deepgram's
pre-recorded speech-to-text REST API into an Assist STT engine.

Russian support is a hard requirement and must be verified end to end on a real
Home Assistant instance.

## Decisions

- **Packaging:** HACS custom integration, not a Home Assistant add-on. HACS does
  not install add-ons. The integration appears as `stt.deepgram_stt`.
- **API:** `POST https://api.deepgram.com/v1/listen` (pre-recorded audio), as
  specified by the project owner.
- **Model:** `nova-3` by default. `nova-2` is available as a fallback option.
- **Language:** taken from the Assist pipeline metadata per request. `ru` is
  explicitly supported and tested.
- **Repository:** new public repository `devqcf/ha-deepgram-stt`.
- **Voice pipeline:** create a separate **Deepgram RU** pipeline, clone the
  current "AI" pipeline settings (Google Translate TTS, Russian), point it at
  `stt.deepgram_stt`, and make it the preferred pipeline. Preserve the existing
  pipelines.
- **Secrets:** the Deepgram API key is stored only in the Home Assistant config
  entry. It must never be committed, logged, or written to this repository.

## Architecture

```text
Assist pipeline
  -> stt.deepgram_stt
     -> collect WAV/PCM audio stream from Home Assistant
     -> ensure a valid WAV container
     -> POST /v1/listen with model + language + formatting options
     -> extract results.channels[0].alternatives[0].transcript
     -> return SpeechResult to Assist
```

### Integration surface

- UI config flow with real API-key validation.
- Reauthentication flow for revoked keys.
- Options flow for model and formatting.
- One cloud STT entity.
- No third-party Python requirement; reuse Home Assistant's `aiohttp` session.
- Russian and English translations.

### Repository layout

```text
custom_components/deepgram_stt/
  __init__.py
  api.py
  config_flow.py
  const.py
  manifest.json
  stt.py
  strings.json
  translations/en.json
  translations/ru.json
  util.py
tests/
.github/workflows/
hacs.json
README.md
LICENSE
plan.md
handoff.md
```

## Implementation checklist

- [x] Create `plan.md` and `handoff.md`.
- [x] Create public GitHub repository `devqcf/ha-deepgram-stt`.
- [x] Add HACS metadata and integration scaffold.
- [x] Implement WAV normalization and response extraction helpers.
- [x] Implement Deepgram API client with timeout and error mapping.
- [x] Implement STT entity with per-request language and model options.
- [x] Implement config, reauth, and options flows.
- [x] Add English and Russian translations.
- [x] Add README with HACS install and Russian Assist setup.
- [x] Add unit tests and CI validation.
- [x] Publish release `1.0.0`.
- [x] Add the new repo to HACS on the test Home Assistant instance.
- [x] Install `1.0.0` through HACS and restart Home Assistant.
- [x] Create the Deepgram config entry using the supplied key.
- [x] Verify `stt.deepgram_stt` exposes `ru`.
- [x] Test the HA STT endpoint with Russian audio.
- [x] Test the real Assist pipeline with Russian PCM audio.
- [x] Create the preferred **Deepgram RU** pipeline.
- [x] Restart Home Assistant and confirm persistence.
- [x] Check logs and HACS version.
- [x] Record results in `handoff.md`.

## Test matrix

| Area | Test |
| --- | --- |
| Utility | WAV header wrapping, existing WAV passthrough, transcript extraction |
| API | Valid key, invalid key, HTTP error mapping, timeout |
| HA config | Config flow validation, entity creation, reauth, options reload |
| Russian STT | Direct `/api/stt/stt.deepgram_stt` request with a Russian phrase |
| Assist | `assist_pipeline/run` start/end at STT with Russian PCM |
| Persistence | HA restart preserves config entry and preferred pipeline |
| HACS | Custom repo install reports `1.0.0` and component loads |

## Rollout and rollback

1. Back up the current pipeline storage before changing the preferred pipeline.
2. Keep the existing "AI" and "Home Assistant" pipelines untouched.
3. If testing fails, set the preferred pipeline back to the original pipeline
   and remove the integration through HACS.
4. The API key can be revoked or rotated independently in the Deepgram console.

## Acceptance criteria

- HACS installs the integration from the new public repository.
- A valid Deepgram API key is accepted; an invalid key is rejected in the UI.
- `stt.deepgram_stt` appears in Home Assistant and advertises `ru`.
- A Russian phrase is transcribed correctly through both the STT endpoint and
  the Assist pipeline.
- The preferred pipeline uses Deepgram, while previous pipelines remain intact.
- No secrets are present in the repository or Home Assistant logs.
