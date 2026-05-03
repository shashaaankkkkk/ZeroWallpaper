<div align="center">

  <pre>
█████ █████ ████   ███  █   █  ███  █     █     ████   ███  ████  █████ ████  
   █  █     █   █ █   █ █   █ █   █ █     █     █   █ █   █ █   █ █     █   █ 
  █   ████  ████  █   █ █ █ █ █████ █     █     ████  █████ ████  ████  ████  
 █    █     █  █  █   █ ██ ██ █   █ █     █     █     █   █ █     █     █  █  
█████ █████ █   █  ███  █   █ █   █ █████ █████ █     █   █ █     █████ █   █  
  </pre>
  <p align="center">
    <strong>The ultimate terminal-based aesthetic wallpaper engine.</strong>
  </p>

  <p align="center">
    <a href="https://github.com/shashaaankkkkk/zerowallpaper/stargazers"><img src="https://img.shields.io/github/stars/shashaaankkkkk/zerowallpaper?style=for-the-badge&color=2d1b69&logo=github" alt="Stars" /></a>
    <a href="https://pypi.org/project/zerowallpaper/"><img src="https://img.shields.io/pypi/v/zerowallpaper?style=for-the-badge&color=a855f7&logo=pypi&logoColor=white" alt="PyPI Version" /></a>
    <a href="https://github.com/shashaaankkkkk/zerowallpaper/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge&color=06b6d4" alt="License" /></a>
  </p>

  <p align="center">
    <a href="#✨-features">Features</a> •
    <a href="#📦-installation">Installation</a> •
    <a href="#⌨️-usage">Usage</a> •
    <a href="#⚙️-configuration">Configuration</a>
  </p>
</div>

<br />

---

## 🖼️ Gallery

<div align="center">
  <p><strong>Experience the fluid UI and high-fidelity rendering</strong></p>
  <img src="assets/app.png" alt="Main Interface" width="100%" style="border-radius: 10px; border: 2px solid #2d1b69;" />
  <br />
  <img src="assets/homescreen.png" alt="Splash Screen" width="100%" style="border-radius: 10px; border: 2px solid #2d1b69; margin-top: 10px;" />
</div>

---

## ✨ Features

- 🌌 **Aesthetic-First**: Curated wallpapers from the best sources on GitHub.
- 🚀 **Streamed, Not Cloned**: Zero local storage bloat. We stream only what you want to see.
- 🖥️ **High-Fidelity Rendering**: Native support for **Kitty**, **WezTerm**, and **iTerm2** with Chafa fallback.
- ⚡ **Turbo Filtering**: Instantly search by tags, name, or category with real-time updates.
- 💖 **Native Favorites**: Keep your favorite aesthetics just one keystroke away.
- 🔄 **Smart Auto-Changer**: A lightweight background daemon that keeps your desktop fresh.
- 🎹 **Keyboard Focused**: Designed for power users. No mouse required, but fully supported.

## 📦 Installation

ZeroWallpaper is just a pip command away:

```bash
pip install zerowallpaper
```

> [!TIP]
> For the best visual experience, install **chafa** on your system:
> `brew install chafa` (macOS) or `sudo apt install chafa` (Linux).

## ⌨️ Usage

Launch the engine:

```bash
zerowallpaper
```

### 🎮 Controls

| Key | Action |
| :--- | :--- |
| <kbd>↑</kbd> <kbd>↓</kbd> | Navigate wallpapers |
| <kbd>Enter</kbd> | Preview wallpaper |
| <kbd>s</kbd> | **Set wallpaper** |
| <kbd>Shift</kbd> + <kbd>E</kbd> | **Explore** All |
| <kbd>Shift</kbd> + <kbd>C</kbd> | View **Cached** |
| <kbd>Shift</kbd> + <kbd>F</kbd> | View **Favorites** |
| <kbd>f</kbd> | Toggle Favorite |
| <kbd>a</kbd> | Toggle Auto-changer |
| <kbd>/</kbd> | Search |
| <kbd>Tab</kbd> | Cycle panels |
| <kbd>q</kbd> | Exit |

## ⚙️ Configuration

ZeroWallpaper keeps things simple. Your config and cache live at `~/.zerowallpaper/`.

### 🔑 GitHub Token (Optional)

To avoid GitHub's unauthenticated rate limits, set a personal access token:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
  <p>Built with 💜 by <a href="https://github.com/shashaaankkkkk">@shashaaankkkkk</a></p>
  <p><i>Making the terminal beautiful, one wallpaper at a time.</i></p>
</div>
