# Handoff / Working State

This file is the recovery point if the working context is lost. Update it after
each major milestone. **Never put API keys, passwords, access tokens, or the
private test-host address in this file.**

## Current status

- Phase: complete — released, installed via HACS, and verified end to end
- Repository: `devqcf/ha-deepgram-stt` (public)
- Local path: `/Users/meowser/Projects/ha-deepgram-stt`
- Release: `1.0.0` published at
  https://github.com/devqcf/ha-deepgram-stt/releases/tag/1.0.0
- HA deployment: installed through HACS, config entry loaded, Russian STT
  verified through both the STT endpoint and the Assist pipeline
- CI: `Validate` workflow (unit tests, hassfest, HACS) passed on `10e0f79`

## Decisions

- Implement as a HACS custom integration, not an add-on.
- Use Deepgram pre-recorded REST (`/v1/listen`), not the live WebSocket API.
- Default model `nova-3`; Russian `ru` mandatory.
- Create a separate preferred pipeline named **Deepgram RU**; preserve existing
  pipelines.
- New repository, separate from the older `devqcf/deepgram-stt` experiment.

## Test environment

- Home Assistant 2026.10.4, Python 3.14.9.
- HACS 2.0.5.
- HA runs in Docker on a Raspberry Pi 5; Docker group access is available.
- Private connection details and credentials are held outside this repository.
- HA long-lived token is available on the test host at `~/.ha-token`.
- The HA container has `aiohttp` and `ffmpeg`, so WebSocket tests and audio
  conversion can run inside the container.

## Milestones

- [x] Discovery of HA/HACS/voice pipeline setup.
- [x] Deepgram key and Russian `nova-3` transcription verified with a live API
  request.
- [x] Write `plan.md`.
- [x] Write this handoff file.
- [x] Create GitHub repository and push bootstrap commit.
- [x] Implement integration, translations, README, tests, and CI.
- [x] Pass local unit tests, compilation, JSON validation, and HA import checks.
- [x] Publish release `1.0.0`.
- [x] Install and test through HACS.
- [x] Create preferred Deepgram RU pipeline.
- [x] Final verification and cleanup.

## Verification results (2026-10-31)

- HACS custom repository `devqcf/ha-deepgram-stt` added (category
  `integration`) and release `1.0.0` installed through the HACS websocket API.
- Config entry created through the real config flow (REST
  `/api/config/config_entries/flow`) with model `nova-3`; state `loaded`.
- `stt.deepgram_stt` advertises 62 languages including `ru` (formats `wav`,
  codec `pcm`, 16 kHz / 16-bit / mono).
- Direct STT endpoint test with a Russian WAV:
  `{"text":"Привет, это тест распознавания русской речи. Включи свет в гостиной.","result":"success"}`
- Real Assist pipeline test (`assist_pipeline/run`, start/end `stt`, raw PCM
  frames prefixed with the websocket binary handler id from `run-start`):
  `stt-end` returned the identical transcript.
- Pipeline **Deepgram RU** (`01m67zs8am5hzerxa2jtnhbkxh`) created as a clone of
  the **AI** pipeline with `stt_engine=stt.deepgram_stt`, `stt_language=ru`, and
  set as preferred. The **Home Assistant** and **AI** pipelines are unchanged.
- After a full Home Assistant restart: config entry `loaded`, entity present,
  preferred pipeline still Deepgram RU, and a repeat STT request returned the
  same transcript. No `deepgram` errors in `home-assistant.log`.
- Backups taken before changes:
  `/config/.storage-backups/20261031-pre-deepgram-stt/` on the HA host
  (`assist_pipeline.pipelines`, `core.config_entries`, `core.entity_registry`,
  `core.restore_state`).

## Implementation notes

- HA pipeline audio metadata is WAV/PCM, 16 kHz, 16-bit mono.
- The audio stream may or may not include a RIFF header; the integration must
  detect and wrap raw PCM when needed.
- Deepgram auth header format: `Authorization: Token <key>`.
- Use `results.channels[0].alternatives[0].transcript`.
- API-key validation: `GET https://api.deepgram.com/v1/auth/token`.
- Test phrase used for manual verification:
  «Привет, это тест распознавания русской речи. Включи свет в гостиной.»
- Existing pipeline to clone: `AI` (Russian, Google Translate TTS, faster-whisper
  STT). Do not delete it.
- Original preferred pipeline ID is stored in HA's
  `.storage/assist_pipeline.pipelines`; back it up before switching.

## Resume steps

1. Read `plan.md` and this file.
2. Check `git status` and `git log --oneline`.
3. Read `plan.md` checkboxes to find the next unfinished item. All items are
   complete as of 2026-10-31; new work starts below this line.
4. Verify the latest release with `gh release list -R devqcf/ha-deepgram-stt`.
5. To re-verify the deployment, check:
   - `stt.deepgram_stt` entity state
   - HACS installed version
   - HA logs for `deepgram_stt`
   - preferred pipeline ID

## Useful commands (placeholders only)

```bash
# Local validation
python3 -m unittest discover -v
python3 -m compileall custom_components/deepgram_stt

# Inspect HA container
docker exec <ha-container> python3 -c 'import homeassistant.const as c; print(c.__version__)'

# HA logs
docker exec <ha-container> sh -c 'grep -i deepgram /config/home-assistant.log'

# HACS state
docker exec <ha-container> python3 -c 'import json; print(json.load(open("/config/.storage/hacs.data")))'  # may be large

# Restart HA container
docker restart <ha-container>
```

## Known issues / risks

- The old integration experiment left stale restore-state entries for
  `stt.deepgram_stt`; these are harmless. The new config entry recreates the
  entity.
- Some Assist satellites may have an explicitly selected pipeline. If the
  preferred pipeline does not take effect, point the satellite at **Deepgram
  RU** or report that an ESPHome-side change is required.
- Deepgram is a cloud service: audio leaves the local network. Call this out in
  the README.
- The API key was supplied in a private chat. Recommend rotating it after the
  integration is verified.
