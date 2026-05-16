import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import yt_dlp

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

def extract_info(url):
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'nocheckcertificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web'],
                'skip': ['hls', 'dash']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            
            # Format results
            formats = []
            for f in info.get('formats', []):
                # Filter for useful formats with direct URLs
                if f.get('url') and (f.get('ext') == 'mp4' or f.get('vcodec') != 'none'):
                    formats.append({
                        'format_id': f.get('format_id'),
                        'ext': f.get('ext'),
                        'resolution': f.get('resolution') or f.get('format_note'),
                        'url': f.get('url'),
                        'filesize': f.get('filesize')
                    })
            
            return {
                'success': True,
                'title': info.get('title'),
                'thumbnail': info.get('thumbnail'),
                'duration': info.get('duration'),
                'uploader': info.get('uploader'),
                'url': info.get('url'), # Best direct URL
                'formats': formats[:10] # Return top 10 formats
            }
        except Exception as e:
            error_msg = str(e)
            if 'Sign in' in error_msg or 'login' in error_msg.lower():
                return {'success': False, 'error': 'This video is restricted or requires login. Try another video!'}
            return {'success': False, 'error': error_msg}


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/extract', methods=['POST'])
def api_extract():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    result = extract_info(url)
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


# Export the Flask app for Vercel
app = app

if __name__ == '__main__':
    # Ensure templates and static folders exist locally
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    app.run(debug=True, port=5000)

