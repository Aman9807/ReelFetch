import os
import random
import re
import json
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, render_template, redirect
from flask_cors import CORS
import yt_dlp

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

try:
    from pytubefix import YouTube
except ImportError:
    YouTube = None

def get_working_cobalt_apis():
    req = urllib.request.Request('https://cobalt.directory/api/working?type=api', headers={'User-Agent': 'Mozilla/5.0'})
    try:
        res = urllib.request.urlopen(req, timeout=5)
        data = json.loads(res.read().decode())
        apis = set()
        for service, list_apis in data.get('data', {}).items():
            for api in list_apis:
                apis.add(api)
        return list(apis)
    except Exception as e:
        print(f"Error fetching cobalt list, using defaults: {e}")
        return [
            'https://api.dl.woof.monster/',
            'https://nuko-c.meowing.de/',
            'https://api.cobalt.blackcat.sweeux.org/',
            'https://cobaltapi.kittycat.boo/',
            'https://grapefruit.clxxped.lol/',
            'https://melon.clxxped.lol/',
            'https://dog.kittycat.boo/',
            'https://cobaltapi.squair.xyz/'
        ]

def extract_youtube_id(url):
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def cobalt_extract(url):
    apis = get_working_cobalt_apis()
    random.shuffle(apis)
    
    # Try a maximum of 4 instances to prevent Vercel timeout (Hobby limit is 10s)
    apis_to_try = apis[:4]
    
    for api in apis_to_try:
        if not api.endswith('/'):
            api += '/'
            
        print(f"Trying Cobalt endpoint: {api}")
        req = urllib.request.Request(
            api,
            data=json.dumps({
                'url': url,
                'videoQuality': '1080',
            }).encode(),
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0'
            }
        )
        try:
            res = urllib.request.urlopen(req, timeout=6)
            resp = json.loads(res.read().decode())
            status = resp.get('status')
            
            if status == 'error':
                print(f"Endpoint {api} returned error: {resp.get('error')}")
                continue
                
            title = resp.get('filename') or 'ReelFetch Video'
            if '.' in title:
                title = '.'.join(title.split('.')[:-1])
                
            thumbnail = 'https://via.placeholder.com/320x180?text=ReelFetch+Video'
            if 'youtube.com' in url or 'youtu.be' in url:
                yt_id = extract_youtube_id(url)
                if yt_id:
                    thumbnail = f'https://img.youtube.com/vi/{yt_id}/hqdefault.jpg'
                    
            if status in ('tunnel', 'redirect'):
                download_url = resp.get('url')
                if not download_url:
                    continue
                
                # Verify that this download URL actually serves bytes (isn't a 0kb blocked tunnel)
                try:
                    chk_req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(chk_req, timeout=4) as chk_res:
                        first_byte = chk_res.read(1)
                        if not first_byte:
                            print(f"Endpoint {api} returned 0-byte stream, skipping.")
                            continue
                        print(f"Verified working endpoint: {api}")
                except Exception as verify_err:
                    print(f"Endpoint {api} download verification failed: {verify_err}, skipping.")
                    continue

                formats = [{
                    'format_id': 'best',
                    'ext': 'mp4',
                    'resolution': 'Best Quality (Auto)',
                    'url': download_url,
                    'filesize': None
                }]
                return {
                    'success': True,
                    'title': title,
                    'thumbnail': thumbnail,
                    'duration': None,
                    'uploader': 'ReelFetch CDN',
                    'url': download_url,
                    'formats': formats
                }
                
            elif status == 'picker':
                picker_items = resp.get('picker', [])
                valid_formats = []
                for i, item in enumerate(picker_items):
                    item_url = item.get('url')
                    if item_url:
                        valid_formats.append({
                            'format_id': f'item_{i}',
                            'ext': item.get('type') or 'mp4',
                            'resolution': f'Item {i+1} ({item.get("type", "media")})',
                            'url': item_url,
                            'filesize': None
                        })
                        
                if valid_formats:
                    # Verify the first item to ensure instance is unblocked
                    try:
                        chk_req = urllib.request.Request(valid_formats[0]['url'], headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(chk_req, timeout=4) as chk_res:
                            first_byte = chk_res.read(1)
                            if not first_byte:
                                print(f"Endpoint {api} picker item 0 returned 0-byte stream, skipping.")
                                continue
                            print(f"Verified working picker endpoint: {api}")
                    except Exception as verify_err:
                        print(f"Endpoint {api} picker verification failed: {verify_err}, skipping.")
                        continue

                    return {
                        'success': True,
                        'title': title,
                        'thumbnail': picker_items[0].get('thumb') or thumbnail if picker_items else thumbnail,
                        'duration': None,
                        'uploader': 'ReelFetch Carousel',
                        'url': valid_formats[0]['url'],
                        'formats': valid_formats
                    }
                
        except Exception as e:
            print(f"Endpoint {api} failed: {e}")
            
    return None

def extract_info(url):
    # Try Cobalt first for robust, high-speed extraction bypassing bot blocks
    print(f"Attempting dynamic Cobalt extraction for: {url}")
    cobalt_res = cobalt_extract(url)
    if cobalt_res and cobalt_res.get('success'):
        print("Cobalt extraction succeeded!")
        return cobalt_res
        
    print("Cobalt extraction failed. Falling back to local extractors...")

    # Try PytubeFix first for YouTube
    if ('youtube.com' in url or 'youtu.be' in url) and YouTube:
        try:
            # Use the ANDROID client instead of WEB to bypass bot detection without needing a po_token
            yt = YouTube(url, client='WEB_CREATOR')
            # Filter for progressive streams (video + audio in one file)
            streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
            best_stream = streams.first()
            
            formats = []
            for s in streams[:10]:
                formats.append({
                    'format_id': s.itag,
                    'ext': 'mp4',
                    'resolution': s.resolution,
                    'url': s.url,
                    'filesize': s.filesize
                })
            
            return {
                'success': True,
                'title': yt.title,
                'thumbnail': yt.thumbnail_url,
                'duration': yt.length,
                'uploader': yt.author,
                'url': best_stream.url if best_stream else None,
                'formats': formats
            }
        except Exception as e:
            # Log the error and fall through to yt-dlp fallback
            print(f"PytubeFix extraction failed: {str(e)}. Falling back to yt-dlp...")
            pass

    # Default to yt-dlp for everything else (like Instagram)
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
                # 'tv' clients are currently blocked and trigger the "Sign in to confirm" bot error. 
                # Using android, ios, and web_creator clients bypasses this.
                'player_client': ['android', 'ios', 'web_creator'],
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
    
    # Bypass Vercel IP Block using cookies if provided
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            
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

@app.route('/about')
def about():
    return redirect('https://flynx.site/app-sites/reelfetch/about')

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

