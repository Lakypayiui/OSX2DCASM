# ACOSXM Studio

ACOSXM Studio is a lightweight cellular automata sandbox focused on Moore-neighborhood rules. It provides an interactive 2D editor for a 512-bit rule matrix, real-time simulation, preset management, live time‑series graphs, and a 3D history viewer.

## Features

- Interactive 2D simulation environment with camera pan and zoom.
- Editable 512‑bit rule matrix (16 × 32) via `RulePanel`.
- 3×3 Moore neighborhood kernel editor with toggle buttons (`KernelWidget`).
- Collapsible accordion panels for rule, population, evolution, colour, info, and graph controls.
- Live time‑series graphs: Population, Global Entropy, and Block Entropy.
- Save and load rule presets (JSON).
- Save and load simulation states (plain text).
- 3D visualisation of simulation history (instanced cubes with frustum culling).
  - Metal backend on macOS (`scenes/renderer_metal.py`).
  - OpenGL 4.1 backend on Linux and Windows (`scenes/renderer_opengl.py`).
- Widget system: `BaseWidget` ABC with `Button`, `Slider`, `InputBox`, `RGBSelector`, `Label`, `GraphWidget`, `KernelWidget`, and `Accordion`.
- Popup dialogs for loading/saving/confirming (separate class hierarchy).
- Resizable window with scrollable control panel.

## Requirements

- Python 3.9 or newer
- `pygame`, `numpy`, `PyOpenGL` (see `requirements.txt` / `requirements-macos.txt`)

## Installation

```bash
python -m venv .venv
source .venv/bin/activate          # Linux / macOS
pip install -r requirements.txt    # add -macos suffix on macOS
```

## Running

```bash
python main.py
```

## Controls

### Simulation View

| Action | Control |
|--------|---------|
| Paint / erase cells | Left click / drag |
| Pan camera | Right click + drag |
| Zoom | Mouse wheel |

### 3D Viewer

| Key | Action |
|-----|--------|
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
├── main.py                       # Entry point
├── core/                         # Domain logic
│   ├── acosxm.py                 # App controller
│   ├── config.py                 # Constants, colour themes, helpers
│   ├── kernel.py                 # 3×3 Moore neighbourhood kernel model
│   ├── life2dm.py                # 2D cellular automaton (numpy)
│   └── rule_matrix.py            # 512-bit rule matrix model
├── scenes/                       # Top-level screens & 3D view
│   ├── menuscene.py              # Main menu (grid size input)
│   ├── simulationscene.py        # Simulation orchestrator
│   ├── display3dscene.py         # 3D viewer (math + geometry shared)
│   ├── renderer_metal.py         # Metal backend (macOS)
│   └── renderer_opengl.py        # OpenGL backend (Linux / Windows)
├── controllers/                  # Input handling & event routing
│   ├── camera_controller.py      # Pan / zoom logic
│   ├── simulation_controller.py  # Mouse painting, panel, popup dispatch
│   └── popup_controller.py       # Popup stack with typed results
├── ui/                           # Visual components
│   ├── panels/                   # Control-panel sub-panels
│   │   ├── simulation_panel.py   # Parent panel, layout orchestration
│   │   ├── rule_controls.py      # Rule matrix, kernel, rule buttons
│   │   ├── rule_panel.py         # 16×32 clickable rule matrix
│   │   ├── population_controls.py# Random config, clear, density
│   │   ├── evolution_controls.py # Start/stop, step, pause, save/load
│   │   ├── color_controls.py     # RGB colour selectors
│   │   ├── info_controls.py      # Live automaton state display
│   │   └── graph_controls.py     # Three time-series graphs in accordions
│   └── dialogs/                  # Popup dialogs (load/save rule/state, confirm)
├── widgets/                      # Reusable BaseWidget hierarchy
│   ├── base_widget.py            # ABC: rect, visible, enabled, draw, handle_event
│   ├── button.py                 # Clickable button (toggle / momentary)
│   ├── slider.py                 # Draggable horizontal slider
│   ├── inputbox.py               # Single-line text / number input
│   ├── rgbselector.py            # Three-channel colour picker
│   ├── label.py                  # Read-only text label
│   ├── graph.py                  # Time-series line chart with export
│   ├── kernel_widget.py          # 3×3 Moore kernel toggle grid
│   ├── accordion.py              # Collapsible container (enables/disables children)
│   └── popup.py                  # Modal overlay base (separate from BaseWidget)
├── assets/                       # Static resources (sounds, icons)
├── presets/                      # Rule preset JSON files
└── saves/                        # Simulation state saves
```

## License

This project is licensed under the MIT License.
