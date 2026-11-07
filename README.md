# Air Gestures - Zero-Calibration High-Precision Window Controller

Control macOS desktop application windows in the air with sub-pixel precision using your laptop's built-in webcam. **Zero calibration required.**

---

## What's New: Zero Calibration & High Precision
- **Instant Motion Tracking**: No 4-corner pointing setup. Launch the app and immediately start moving windows.
- **Ergonomic Virtual Air-Pad**: An ergonomic interaction zone in the center of the camera FOV (~15–20 cm hand movement) maps directly to your full display.
- **Pointer Ballistics & Dynamic Acceleration**: Micro-movements are heavily filtered for rock-solid stationary holding; fast flicks accelerate smoothly across the screen.
- **Pinch Centroid Anchoring**: When engaging the 3-finger pinch, the cursor locks onto the physical centroid of all three fingertips, eliminating cursor jumps when grabbing.
- **Sub-Pixel Jitter Suppression**: High-precision 1€ Filter tuning completely removes webcam tremor.

---

## Gestures Guide

| Action | Hand Gesture | Behavior |
| :--- | :--- | :--- |
| **Move Cursor / Hover** | **Index Finger Pointing** | Move your index finger in the air; macOS mouse pointer tracks your position in real-time. |
| **Grab & Drag Window** | **3-Finger Pinch** (Thumb + Index + Middle) | Bring thumb, index, and middle fingertips together over any window to grab and move it. |
| **Drop / Release** | **Open Fingers** | Release the 3-finger pinch to drop the window in place. |
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
