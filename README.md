# Clearstate-Hack-The-Hill-2026-Project-

# ClearState

ClearState is a Windows desktop tool that puts a mindful pause in front of the apps that distract you. You pick the programs you want to guard. When you open one, ClearState minimizes it and asks you to pass a short camera check before it lets you back in.

Built at **Hack The Hill 2026** by Andrew Campbell, Liam Johnston, Reese Houston, and Gabriel Abdalla.

> **Status: hackathon prototype.** The menus and the app list work. The background monitor and the Presage camera integration are experimental. See [Known limitations](#known-limitations).

## Quick start

After [installing](#installation), **run `main.py` to start the app**:

```powershell
cd ClearState
python main.py
```

`main.py` opens the ClearState menu. Everything else (Setup, Help, and starting the background monitor) is launched from there.

## How it works

1. **Choose what to block.** In the Setup screen, add the names of the programs you want guarded (for example `discord`).
2. **Start the monitor.** From the main menu, press *Start Script*. A background script watches your open windows.
3. **Get stopped at the door.** When a guarded app opens, the monitor minimizes it and launches the ClearState check.
4. **Pass the check.** Face your webcam, stay still, and smile. The check uses the [Presage SmartSpectra](https://physiology.presagetech.com) SDK to read your facial expression. After a few consecutive happy readings, the check passes and the app is released.

## Requirements

- Windows 10 or 11 (the monitor uses the Windows API)
- Python 3.10 or newer
- Node.js 20 or newer
- A webcam
- A free Presage API key from [physiology.presagetech.com](https://physiology.presagetech.com) (verify your email after signing up)

## Installation

```powershell
git clone <your-repo-url>
cd <repo-folder>

# Python dependencies
pip install -r ClearState/requirements.txt

# Node dependencies (the Presage camera bridge)
cd ClearState
npm install
```

On PowerShell, if `npm` is blocked by the execution policy, use `npm.cmd install`, or run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

## Usage

Run everything from the `ClearState` folder.

**Launch the app**

```powershell
python main.py
```

Use *Setup* to add or remove blocked programs, *Help* for in-app instructions, and *Start Script* to turn on the monitor.

**Run only the camera check** (useful for testing your API key and webcam)

```powershell
python presage2.py --gui
```

Paste your API key into the window, or set it beforehand:

```powershell
$env:SMARTSPECTRA_API_KEY="your-key-here"
```

**Run only the monitor**

```powershell
python "../Script Tests/app_monitor.py"
```

Never commit your API key. The app reads it from the GUI field or the `SMARTSPECTRA_API_KEY` environment variable.

## Project structure

```
.
├── ClearState/
│   ├── main.py              # Entry point (pygame menu app)
│   ├── presage2.py          # Camera check launcher and GUI
│   ├── presage_bridge.mjs   # Node bridge to the SmartSpectra SDK
│   ├── locked_apps.txt      # Programs to guard (managed by the Setup screen)
│   ├── assets/              # Background images
│   ├── package.json
│   ├── requirements.txt
│   └── src/                 # Engine, screens, UI modules, settings
├── Script Tests/
│   └── app_monitor.py       # Background window monitor
└── Testing/                 # Experimental scripts
```

## Known limitations

- **The check is an expression gate, not identity verification.** It passes when the camera sees a sustained smile. It does not confirm who you are, and it does not measure stress. Treat it as a proof of concept for a "pause before you scroll" interaction.
- **Windows only.** The monitor depends on `pywin32`.
- **Requires a Presage API key and an internet connection** for the live camera check.
- **Experimental monitor.** App matching is based on process and window names, so some programs may not be detected reliably.

## Tech stack

Python, pygame, psutil, pywin32, pygetwindow, Node.js, Presage SmartSpectra SDK

## Team and contributions

ClearState was built by a team of four at Hack The Hill 2026.

**Gabriel Abdalla (me) : UI design**

- Designed the look and layout of the app's interface.
- Placed the buttons and labels across the app's screens, including the main menu, Setup, and Help.
- Designed the background artwork used across the app.

**Andrew Campbell: core framework and technical lead**

- Built the application framework (the engine, screen management, and the overall structure the rest of the app sits on).
- Did roughly 90% of the project's technical work.

**Liam Johnston: Presage integration**

- Built the Presage SmartSpectra integration that powers the camera check.

**Reese Houston: supporting development**

- Handled supporting tasks that kept the project moving.
