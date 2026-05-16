# ReelFetch - Video Downloader

ReelFetch is a lightweight, premium web application that allows you to extract download links for YouTube and Instagram videos/reels.

## Features
- **Modern UI**: Glassmorphism design with smooth animations.
- **Fast Extraction**: Powered by `yt-dlp` for accurate metadata extraction.
- **Single Page App**: Clean, responsive, and intuitive interface.
- **No Server Storage**: Media links are extracted directly to your browser.

## Prerequisites
- Python 3.7+
- `pip` (Python package installer)

## Installation

1. **Navigate to the project directory**:
   ```bash
   cd ReelFetch
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Running the App

1. **Start the Flask server**:
   ```bash
   python app.py
   ```

2. **Open your browser**:
   Navigate to `http://127.0.0.1:5000` to start using ReelFetch.

## Project Structure
- `app.py`: Flask backend with API endpoints.
- `templates/`: HTML templates.
- `static/css/`: Premium styling.
- `static/js/`: Frontend logic.
- `requirements.txt`: Python dependencies.
