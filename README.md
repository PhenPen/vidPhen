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
- **What next + open** — after `Done: X ok, Y failed`:
  ```
  1) Download another
  2) Open download folder
  3) Open downloaded file
  4) Quit
  ```
  Single file opens directly; playlists/batches show a numbered pick list (`1) name … 0) Back`, first 50 shown)
- **Doctor + updates** — startup check for `Python / yt-dlp / ffmpeg` with install help or auto install; `Settings → Check for yt-dlp updates`; one update and retry offer per run on failure

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

First run asks for your default download folder and checks `yt-dlp` / `ffmpeg`.

## Usage

Main menu (`Pick 1-5`, shortcuts `V`ideos / `P`laylists / `D` or `T` subs / `S`ettings / `Q`uit):

```
What do you want to do?
1) Download videos
2) Download playlists
3) Download subtitles only
4) Check settings
5) Quit
```

**Videos:** `1 → How many? 1) One 2) Multiple → Enter URL(s) → preview → Download these N? → Quality (same/per) → Subtitles (same/per) → Save Default/Custom → Done → What next 1-4`

**Playlists:** `2 → one/many → preview title + count → Download these N? → Quality / Subtitles / Video range (same/per) → E/R/S scope when per-playlist → Done → What next 1-4`

**Subtitles only:** `3 → 1) Videos 2) Playlists → URLs → preview → language pick (no quality prompt) → Done → What next 1-4` (outputs `.vtt/.srt` via `--write-subs --skip-download`)

**Shortcuts:** video quality `1` = Best auto; audio path picks type next; `Advanced` accepts raw IDs (`250`, `247+250`).

## Settings

`4) Check settings`:

```
1) Change default download folder
2) Open config file location
3) Check for yt-dlp updates
4) Back
```

## Configuration

Stored at `~/.config/phenTube/config.json`:

```json
{ "download_dir": "C:/Users/You/Downloads" }
```

Old Windows `AppData/Roaming/yt-dlp/config.txt` installs are migrated automatically. To reset, use `Settings → Change default download folder`. Per run you can still pick `Save Default (D) or Custom once (C)`.

Output names: videos `%(title)s.%(ext)s`, playlists `%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s`, with `--no-overwrites --continue --windows-filenames`.

## Project Structure

```
vidPhen/
├── yT.py                        # Dev shim -> vidphen.cli:main
├── pyproject.toml               # Package vidphen 1.0, console script vidphen
├── requirements.txt             # yt-dlp>=2023.0.0 (mirrors pyproject)
├── test.py                      # Offline checks, no prompts: python test.py
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
```

Install with `pip install -e .` (pulls `yt-dlp`) plus `ffmpeg` separately:

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
