import urllib.request, json, urllib.error
req = urllib.request.Request('https://api.cobalt.tools/api/json', data=json.dumps({'url': 'https://youtu.be/oDUa1Bw-hok?si=9wcCsdS30bB4K6Yc'}).encode(), headers={'Accept': 'application/json', 'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'})
try:
    res = urllib.request.urlopen(req)
    print(res.read().decode())
except urllib.error.HTTPError as e:
    print(e.read().decode())
