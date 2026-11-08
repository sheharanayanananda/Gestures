# Air Gestures - Zero-Calibration High-Precision Window Controller

Control macOS desktop application windows in the air with sub-pixel precision using your laptop's built-in webcam. **Zero calibration required.**

---

## Features
- **Real-Time Fluid Snapping (9 Placements)**: As you drag a window toward screen edges or corners, it **instantly snaps and morphs in real time** into that placement. Pulling away smoothly un-snaps it back to floating.
- **Minimizable Preview Window**: The camera preview window can be minimized to the Dock via the macOS yellow title bar button or shortcut key `m`. Gesture tracking continues smoothly in the background!
- **Instant Motion Tracking**: No 4-corner pointing setup. Launch the app and immediately start moving windows.
- **Geometric Window Auto-Grab**: Identifies windows directly underneath your air cursor via `CGWindowListCopyWindowInfo` and moves them via `AXUIElement` without sending simulated mouse clicks.
- **Zero Mouse Hijacking**: Your physical mouse pointer is never taken over while hovering.
- **Pointer Ballistics & Dynamic Acceleration**: Heavy 1€ Filter tremor attenuation for rock-solid stationary holding; fast flicks accelerate smoothly across the screen.

---

## 9 Window Snapping Placements

| Snap Placement | Target Geometry | How to Trigger |
| :--- | :--- | :--- |
| **Upper Left** | Top-Left Quadrant ($50\%$ width, $50\%$ height) | Drag window to top-left corner |
| **Upper Right** | Top-Right Quadrant ($50\%$ width, $50\%$ height) | Drag window to top-right corner |
| **Lower Left** | Bottom-Left Quadrant ($50\%$ width, $50\%$ height) | Drag window to bottom-left corner |
| **Lower Right** | Bottom-Right Quadrant ($50\%$ width, $50\%$ height) | Drag window to bottom-right corner |
| **Left Half** | Left $50\%$ width, full height | Drag window to left screen edge |
| **Right Half** | Right $50\%$ width, full height | Drag window to right screen edge |
| **Upper Half** | Top $100\%$ width, $50\%$ height | Drag window to top edge (outer sections) |
| **Lower Half** | Bottom $100\%$ width, $50\%$ height | Drag window to bottom screen edge |
| **Full Screen** | Full display width & height beneath Menubar | Drag window to top edge center |
| **Un-Snap / Float** | Restores original pre-snap floating dimensions | Pull window $\ge 110\text{px}$ away from edge |

---

## Gestures & Controls

| Action | Hand Gesture / Key | Behavior |
| :--- | :--- | :--- |
| **Move Cursor / Hover** | **Index Finger Pointing** | Move your index finger in the air; HUD shows window under finger. |
| **Grab & Move Window** | **3-Finger Pinch** (Thumb + Index + Middle) | Bring thumb, index, and middle fingertips together over any window. |
| **Fluid Snap** | **Drag to Edge / Corner** | Window instantly snaps to tile while dragging. |
| **Drop / Release** | **Open Fingers** | Release the 3-finger pinch to commit the window in place. |
| **Minimize / Restore** | Key `m` or Yellow Titlebar Button | Minimizes preview to Dock while tracking continues in background. |
| **Quit** | Key `q` or `ESC` | Exits the application. |

---

## Setup & Running

1. **Activate Environment**:
   ```bash
   source .venv/bin/activate
   ```

2. **macOS Accessibility Permissions**:
   Make sure your terminal (e.g. `Terminal`, `iTerm2`, or `Cursor` / `VS Code`) is toggled **ON** under:
   `System Settings` > `Privacy & Security` > `Accessibility`.

3. **Start the Application**:
   ```bash
   ./.venv/bin/python main.py
   ```

---

## Automated Tests
```bash
./.venv/bin/pytest tests
```
