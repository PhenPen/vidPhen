# Vidphen

An interactive terminal downloader for videos, playlists, and subtitles only. Thin wrapper over `yt-dlp` (+ `ffmpeg` for merges/converts).

YouTube first, but any public link is accepted (public Vimeo / LinkedIn posts etc. via `yt-dlp`). 

## Features

- **Videos, playlists, subtitles-only** — `1) Download videos 2) Download playlists 3) Download subtitles only`
- **One or many URLs** — paste one per line (empty line finishes); commas work too; invalid links reported, duplicates dropped
- **Preview before download** — titles + durations for videos, title + count for playlists, then `Download these N? (y/n)`
- **Dynamic quality menu** — built from the video's actual formats: `Best (auto, MP4 if possible)`, `2160p / 1440p / 1080p / 720p / 480p / 360p / tiny`, `Audio only (mp3 / m4a / opus / wav / flac / original)`, `8K (rare)`, `Advanced -type ID yourself (eg 247+250)`
- **Dynamic subtitle menu** — built from manual + auto generated captions; `1) No subtitles 2) Video + subtitles` (video/playlist flows); subs only flow picks language only; auto captions fallback offered
- **Batch control** — `Same for all` vs `Pick per video` for quality/subs (and video range for playlists); picked quality fallback `Auto use best below / Ask me / Skip`
- **Playlist scope** — `E) Everything R) Range (eg 2-19) S) Specific (eg 1,4,6)`
- **What next + open** — after the download summary:
  ```
  1) Main menu
  2) Open download folder
  3) Open downloaded file
  4) Quit
  ```
  Single file opens directly; playlists/batches show a numbered pick list (`1) name … 0) Back`, first 50 shown)
- **Doctor + updates** — Settings check for `Python / yt-dlp / ffmpeg` with install help or auto install; `Settings → Check for yt-dlp updates`; one update and retry offer per run on failure

## Prerequisites

- Python `>= 3.9`
- Internet connection
- `ffmpeg` for video+audio merges (`1080p+`) and audio converts (`mp3/m4a/opus/wav/flac`). `Best` and audio original often work without it — the app warns before downloading a broken file.

## Installation

```bash
git clone https://github.com/PhenPen/vidPhen.git
cd vidPhen
pip install -e .
```

Run (primary):

```bash
vidphen
```

Alternatives:

```bash
python -m vidphen   # same app, no console script needed
python yT.py        # local-dev shim, calls vidphen.cli:main
```

No clone (install from GitHub directly):

```bash
pip install git+https://github.com/PhenPen/vidPhen.git
vidphen
```

The first download asks for your default download folder. Dependency checks are available in Settings.

## Usage

Main menu (`Pick 1-5`, shortcuts `V`ideos / `P`laylists / `D` or `T` subs / `S`ettings / `Q`uit):

```
What do you want to do?
1) Download videos
2) Download playlists
3) Download subtitles
4) Settings
5) Quit
```

- **Videos:** paste one or more links, preview them, choose quality and subtitles, then choose a folder.
- **Playlists:** paste playlist links and choose Everything, a range, or specific entries.
- **Subtitles only:** choose Videos or Playlists, paste links, then select a language. A playlist language preference applies to every selected entry.
- For batches, settings apply to every item by default. Choose **Customize** to set options per item.
- VidPhen starts checking each link as you paste it. Press Enter on an empty line to finish entering links. Type `:back` at a workflow prompt to return to the main menu.
- VidPhen uses Rich in interactive terminals. Set `NO_COLOR` for plain output.

**Shortcuts:** video quality `1` = Best auto; audio path picks type next; `Advanced` accepts raw IDs (`250`, `247+250`).

## Settings

`4) Settings`:

```
1) Change default download folder
2) Open config file location
3) Check for yt-dlp updates
4) Back
5) Check dependencies
```

## Configuration

Stored at `~/.config/vidphen/config.json`:

```json
{ "download_dir": "C:/Users/You/Downloads" }
```

Existing `~/.config/phenTube/config.json` settings carry over if the new file does not exist.

Old Windows `AppData/Roaming/yt-dlp/config.txt` installs are migrated automatically. To reset, use `Settings → Change default download folder`. Per run you can still pick `Save Default (D) or Custom once (C)`.

Output names: videos `%(title)s.%(ext)s`, playlists `%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s`, with `--no-overwrites --continue --windows-filenames`.

## Project Structure

```
vidPhen/
├── yT.py                        # Dev shim -> vidphen.cli:main
├── pyproject.toml               # Package metadata and vidphen console script
├── requirements.txt             # Runtime dependencies (mirrors pyproject)
├── test.py                      # Offline checks: python test.py
├── test_cli.py                  # CLI regression checks: python -m unittest test_cli
├── vidphen/
│   ├── __init__.py  __main__.py  cli.py  doctor.py
│   ├── contentSelect/   # ui, validators, quality, video, playlist, tableShort
│   ├── downloadSelect/  # runner (capture + open), downloaderVideo, downloaderPlaylist
│   ├── subtitleSelect/  # sub_langs (dynamic menus, resolve_lang/default)
│   ├── configSelect/    # config (JSON path + legacy migration)
│   ├── metaDataSelect/  # metaData (preview fetch, format_duration)
│   └── extractors/      # base + ytdlp_extractor (yt-dlp CLI wrapper)
```

## Requirements

```
yt-dlp>=2023.0.0
rich>=13.7
```

Install with `pip install -e .` (pulls `yt-dlp` and `rich`) plus `ffmpeg` separately:

- Windows: `winget install Gyan.FFmpeg` (then open a NEW terminal)
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

Check health: `python test.py` (offline, no prompts).

## License

MIT License — see [LICENSE](LICENSE).

## Contributing

Issues and pull requests welcome via GitHub. No separate contributing guide yet.

---

**Note:** For personal use. Always respect copyright and usage rights when downloading.
