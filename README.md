# ZeroWallpaper

A premium terminal wallpaper browser and manager built with [Textual](https://textual.textualize.io/).

Browse, preview, and apply aesthetic wallpapers from [D3Ext/aesthetic-wallpapers](https://github.com/D3Ext/aesthetic-wallpapers) — all from your terminal.

## Features

- **Remote-first**: Fetches wallpapers from GitHub without cloning the repo
- **Tag-based filtering**: Multi-tag search parsed from repository metadata
- **Terminal image preview**: See wallpapers rendered directly in your terminal
- **Cross-platform**: macOS, Linux (GNOME/KDE/XFCE), and Windows support
- **Auto-change**: Scheduled wallpaper rotation with configurable intervals
- **Favorites & History**: Track your favorite and recently applied wallpapers
- **Keyboard-driven**: Full keyboard navigation with intuitive shortcuts

## Installation

```bash
pip install  zerowallpaper
```

## Usage

```bash
zerowallpaper
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `↑↓` / `j k` | Navigate wallpapers |
| `Enter` | Preview wallpaper |
| `s` | Set wallpaper |
| `v` | View HD image popup |
| `/` | Focus search |
| `Tab` | Switch panels |
| `r` | Random wallpaper |
| `a` | Toggle auto-change |
| `f` | Toggle favorite |
| `R` | Refresh index |
| `q` | Quit |

## Configuration

Config is stored at `~/.zerowallpaper/config.json`. Set `GITHUB_TOKEN` environment variable for higher API rate limits.

