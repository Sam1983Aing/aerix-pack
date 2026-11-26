"""Run the private local Three.js viewer. Optional positional port, default free port."""
import json
import re
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]


class ReviewHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = unquote(urlsplit(self.path).path)
        if path == '/versions.json':
            rows = [
                {"name":p.stem.removeprefix("drone-").upper(), "url":"/models/"+p.name}
                for p in sorted((ROOT/'exports').glob('drone-v*.glb'),reverse=True)
            ]
            payload = json.dumps(rows).encode()
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Content-Length",str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        super().do_GET()

    def translate_path(self, path):
        url = unquote(urlsplit(path).path)
        if url == '/app.js': return str(ROOT/'scripts/viewer.js')
        if re.fullmatch(r'/models/drone-v\d+[a-z]?\.glb',url):
            return str(ROOT/'exports'/Path(url).name)
        return super().translate_path(path)

    def list_directory(self,path):
        self.send_error(404)
        return None


if __name__ == '__main__':
    server=ThreadingHTTPServer(('127.0.0.1',int(sys.argv[1]) if len(sys.argv)>1 else 0),
                               partial(ReviewHandler,directory=str(ROOT/'viewer')))
    print(f'http://127.0.0.1:{server.server_port}/',flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()
