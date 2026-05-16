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
        'youtube_include_dash_manifest': False,
        'youtube_include_hls_manifest': False,
        'extractor_args': {
            'youtube': {
                'player_client': ['tv', 'tv_embedded', 'android', 'ios'],
                'player_skip': ['webpage', 'configs']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (SMART-TV; Linux; Tizen 5.0) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/2.2 Chrome/63.0.3239.111 TV Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Origin': 'https://www.youtube.com',
            'Referer': 'https://www.youtube.com/',
        }
    }


    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            
            # Format results
            formats = []
            for f in info.get('formats', []):
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
                'url': info.get('url'),
                'formats': formats[:10]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}



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

