# Deepgram Speech-to-Text for Home Assistant

A HACS custom integration that adds Deepgram's pre-recorded speech-to-text API
as a speech-to-text engine for Home Assistant Assist.

Russian (`ru`) is explicitly supported and tested, alongside the other languages
available in Deepgram's Nova models.

## Features

- Uses the Deepgram **pre-recorded** API: `POST https://api.deepgram.com/v1/listen`.
- Works as an Assist speech-to-text engine (`stt.deepgram_stt`).
- Russian support, including fully translated Russian setup UI.
- Nova-3 by default, with Nova-2 as a fallback.
- Language is selected per Assist pipeline and sent to Deepgram with every request.
- Optional smart formatting, punctuation, and numeral conversion.
- API-key validation during setup, plus a reauthentication flow.
- No third-party Python package: uses Home Assistant's existing `aiohttp` session.

## Requirements

- Home Assistant 2025.10 or newer.
- HACS 2.x (recommended) or manual installation.
- A Deepgram API key. Create one at
  [console.deepgram.com](https://console.deepgram.com/).
- Internet access from Home Assistant to `api.deepgram.com`.

## Installation with HACS

1. Open **HACS** in Home Assistant.
2. Open the three-dot menu and choose **Custom repositories**.
3. Add `https://github.com/devqcf/ha-deepgram-stt` with category **Integration**.
4. Search for **Deepgram Speech-to-Text** and install it.
5. Restart Home Assistant.

## Manual installation

Copy `custom_components/deepgram_stt` into your Home Assistant `config/custom_components`
directory and restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & services → Add integration**.
2. Search for **Deepgram Speech-to-Text**.
3. Enter your Deepgram API key.
4. Choose **Nova-3** (recommended) or **Nova-2**.
5. Finish the setup.

The key is stored only in the Home Assistant config entry. It is never written
to the repository or included in logs.

After setup, open the integration's **Configure** dialog to change the model or
formatting options.

## Voice assistant setup

1. Go to **Settings → Voice assistants**.
2. Create or edit a pipeline.
3. Under **Speech-to-text**, choose **Deepgram STT**.
4. Set the pipeline language. For Russian, choose **Russian** (`ru`).
5. Save the pipeline and make it the preferred one if desired.

The integration advertises the languages supported by the selected model. For
Russian, Deepgram accepts `ru`, which is advertised by both Nova-3 and Nova-2.

## Example: Russian pipeline

A typical Russian Assist pipeline looks like this:

- **Speech-to-text:** Deepgram STT, language `ru`
- **Conversation agent:** your preferred agent, language `ru`
- **Text-to-speech:** your preferred Russian voice

Both stages after STT are independent of this integration.

## Privacy

Deepgram is a cloud service. Recorded audio is uploaded to `api.deepgram.com`
for transcription. Do not use this integration if your audio must stay on the
local network. Review [Deepgram's privacy policy](https://deepgram.com/privacy)
before enabling it.

## Troubleshooting

### The key is rejected

Confirm the key is active in the Deepgram console and has access to the selected
model. Deepgram keys are shown only once, so create a new key if necessary.

### `stt.deepgram_stt` is missing

- Check that the integration is installed under
  `config/custom_components/deepgram_stt`.
- Restart Home Assistant after installing.
- Look for `deepgram_stt` errors in **Settings → System → Logs**.

### Assist does not use Deepgram

The preferred pipeline only applies to satellites that do not have an
explicitly selected pipeline. Open the satellite's settings and select the
pipeline that uses **Deepgram STT**.

### Russian transcription is inaccurate

Use Nova-3, set the pipeline and STT language to `ru`, and speak clearly. The
Deepgram request uses the pipeline language exactly as provided by Home
Assistant; a wrong pipeline language will produce poor results.

## Development

```bash
python3 -m unittest discover -v
python3 -m compileall custom_components/deepgram_stt
```

The repository also runs HACS and hassfest validation in GitHub Actions.

## License

MIT. See [LICENSE](LICENSE).
