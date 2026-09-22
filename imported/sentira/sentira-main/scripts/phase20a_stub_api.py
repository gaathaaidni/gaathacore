import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CAMERAS = {
    'camera-a': {
        'id': 'camera-a', 'organizationId': 'org-a', 'siteId': 'site-a',
        'streamUrl': 'rtsp://127.0.0.1:8555/live-a', 'isEnabled': True,
    },
    'camera-b': {
        'id': 'camera-b', 'organizationId': 'org-b', 'siteId': 'site-b',
        'streamUrl': 'rtsp://127.0.0.1:8556/live-b', 'isEnabled': True,
    },
}
FRAME_COUNT = 0


class Handler(BaseHTTPRequestHandler):
    def _write(self, status, body=None):
        payload = b'' if body is None else json.dumps(body).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        if payload:
            self.wfile.write(payload)

    def do_GET(self):
        if self.path == '/health':
            self._write(200, {'status': 'ok', 'frames': FRAME_COUNT})
            return
        if self.path == '/api/cameras/internal/all':
            self._write(200, list(CAMERAS.values()))
            return
        prefix = '/api/cameras/internal/'
        if self.path.startswith(prefix):
            camera = CAMERAS.get(self.path[len(prefix):])
            self._write(200 if camera else 404, camera)
            return
        self._write(404, {'error': 'not found'})

    def do_POST(self):
        global FRAME_COUNT
        if self.path == '/frames':
            FRAME_COUNT += 1
            self._write(204)
            return
        if self.path == '/control/disable-a':
            CAMERAS['camera-a']['isEnabled'] = False
            self._write(200, CAMERAS['camera-a'])
            return
        if self.path == '/control/enable-a':
            CAMERAS['camera-a']['isEnabled'] = True
            self._write(200, CAMERAS['camera-a'])
            return
        self._write(404, {'error': 'not found'})

    def log_message(self, format, *args):
        return


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 4000), Handler).serve_forever()
