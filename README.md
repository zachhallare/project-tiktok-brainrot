# Physics Battle Animation

A satisfying physics-based "Red vs Blue" battle animation optimized for TikTok vertical video format (1080x1920).

## Prerequisites

- Python 3.x
- FFmpeg (required for video export mode)

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Preview Mode (real-time window)
```bash
python main.py --preview
```
Press **ESC** to exit.

### Export Mode (creates MP4 video)
```bash
python main.py
```

## Configuration

Edit `config.py` to customize:
- Resolution and FPS
- Team sizes and colors
- Physics settings
- Output file name