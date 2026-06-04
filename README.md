# ACOSXM Studio

ACOSXM Studio is a lightweight cellular automata sandbox focused on Moore-neighborhood rules. It provides an interactive 2D editor for a 512-bit rule matrix, real-time simulation, preset management, and a 3D history viewer.

## Features

- Interactive 2D simulation environment.
- Editable 512-bit rule matrix (16 × 32).
- Kernel helper for generating rule masks.
- Save and load presets.
- Save and load simulation states.
- 3D visualization of simulation history.
  - Metal backend on macOS.
  - OpenGL backend on Linux and Windows.
- UI components including buttons, sliders, text inputs, and color selectors.

## Requirements

- Python 3.9 or newer

## Installation

### Linux / Windows

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Linux:

```bash
source .venv/bin/activate
```

Windows:

```cmd
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### macOS

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements-macos.txt
```

The macOS version uses Apple's Metal API through PyObjC for 3D rendering.

## Running

Start the application with:

```bash
python main.py
```

## Controls

### 3D Viewer

| Key | Action |
|------|----------|
| W / A / S / D | Move camera |
| Space | Move up |
| Left Shift | Move down |
| ← / → | Rotate camera (yaw) |
| ↑ / ↓ | Tilt camera (pitch) |
| O / Numpad + | Increase visible generations |
| I / Numpad - | Decrease visible generations |
| R | Reset camera |

## Project Structure

```text
ACOSXM-Studio/
├── main.py
├── requirements.txt
├── requirements-macos.txt
├── saves/
├── presets/
└── assets/
```

## License

This project is licensed under the MIT License.