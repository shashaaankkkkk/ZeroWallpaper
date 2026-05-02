<div align="center">
  <h1 align="center">ZeroWallpaper 🌌</h1>
  <p align="center">
    <strong>A premium, ultra-fast terminal wallpaper browser & manager built for modern aesthetics.</strong>
  </p>
  <p align="center">
    <a href="https://github.com/shashaaankkkkk/zerowallpaper/blob/main/LICENSE">
      <img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge&color=2d1b69" alt="License" />
    </a>
    <a href="https://pypi.org/project/zerowallpaper/">
      <img src="https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&color=a855f7&logo=python&logoColor=white" alt="Python Version" />
    </a>
    <a href="https://textual.textualize.io/">
      <img src="https://img.shields.io/badge/Built_with-Textual-blue.svg?style=for-the-badge&color=06b6d4" alt="Built with Textual" />
    </a>
  </p>
</div>

<br />

<div align="center">
  <img src="assets/app.png" alt="ZeroWallpaper Main Application" width="48%" style="border-radius: 8px; margin-right: 2%;" />
  <img src="assets/homescreen.png" alt="ZeroWallpaper Home Screen" width="48%" style="border-radius: 8px;" />
</div>

---

**ZeroWallpaper** brings the beauty of high-quality desktop customization directly into your terminal. Powered by the incredible aesthetic collections from [D3Ext/aesthetic-wallpapers](https://github.com/D3Ext/aesthetic-wallpapers), it allows you to instantly browse, preview, and apply wallpapers without ever leaving your command line.

## ✨ Features

- 🚀 **Remote-First Architecture**: Instantly streams wallpapers directly from GitHub without the need to clone massive repositories locally.
- 🎨 **High-Fidelity Terminal Rendering**: Uses a state-of-the-art fallback pipeline (`Sixel` → `Chafa` → `Half-Blocks`) to render ultra-high-definition image previews directly inside modern terminals (Kitty, WezTerm, iTerm2, VSCode).
- 🧠 **Smart Tag Navigation**: Explore wallpapers through an intuitive sidebar. Combine tags seamlessly to find exactly the aesthetic you want.
- ⚡ **Lightning Fast Interface**: Built entirely on [Textual](https://textual.textualize.io/), featuring fluid 60FPS animations, a gorgeous dark mode UI, and instant filtering.
- 🔄 **Auto-Changer**: Set it and forget it. Configurable background daemon to rotate your wallpapers automatically.
- 💖 **Favorites & Caching**: Save wallpapers to your favorites list and rely on the intelligent local cache for blazing fast repeat loads.

## 📦 Installation

ZeroWallpaper is available via `pip`. Ensure you are using Python 3.10 or newer.

```bash
pip install zerowallpaper
```

*(Optional but highly recommended)*: Install `chafa` on your system for drastically improved image rendering quality. 
- macOS: `brew install chafa`
- Linux: `sudo apt install chafa`

## ⌨️ Usage

Simply launch the interactive TUI from your terminal:

```bash
zerowallpaper
```

### Keyboard Navigation

ZeroWallpaper is designed to be completely keyboard-driven. Navigate fluidly without ever touching your mouse:

| Key | Action |
| :--- | :--- |
| <kbd>↑</kbd> / <kbd>↓</kbd> | Navigate wallpapers and menus |
| <kbd>Enter</kbd> | Select / Preview a wallpaper |
| <kbd>Double-Click</kbd> | View high-resolution image in standard image viewer |
| <kbd>s</kbd> | **Set wallpaper** as your current desktop background |
| <kbd>Shift</kbd> + <kbd>E</kbd> | Instantly jump to the **Explore** panel |
| <kbd>Shift</kbd> + <kbd>C</kbd> | Instantly jump to your **Cached** wallpapers |
| <kbd>Shift</kbd> + <kbd>F</kbd> | Instantly jump to your **Favorites** |
| <kbd>f</kbd> | Toggle Favorite status on the current wallpaper |
| <kbd>a</kbd> | Toggle auto-change wallpaper daemon |
| <kbd>/</kbd> | Focus the search bar |
| <kbd>Tab</kbd> | Cycle keyboard focus between UI panels |
| <kbd>q</kbd> | Quit the application |

## ⚙️ Configuration

ZeroWallpaper works perfectly out of the box. All local configurations and image caches are cleanly managed and stored at:
`~/.zerowallpaper/config.json`

**API Rate Limits**: Because ZeroWallpaper fetches directly from GitHub, heavy usage might hit GitHub's unauthenticated API rate limits. To prevent this, you can set a GitHub token:
```bash
export GITHUB_TOKEN="your_personal_access_token_here"
```

## 🤝 Contributing

Contributions, issues, and feature requests are always welcome! Feel free to check the [issues page](https://github.com/shashaaankkkkk/zerowallpaper/issues).

---
<div align="center">
  <i>Made with love by <a href="https://github.com/shashaaankkkkk">@shashaaankkkkk</a></i>
</div>
