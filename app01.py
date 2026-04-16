import os
import sys
import time
import socket
import signal
import subprocess
import threading
import http.server
import webbrowser
from flask import Flask, request, jsonify
from flask_cors import CORS

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
# In py2app bundle, resources are in Contents/Resources
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.join(os.path.dirname(sys.executable), '..', 'Resources')
    BASE_DIR = os.path.normpath(BASE_DIR)
API_PORT    = 5401
STATIC_PORT = 5402
INDEX_FILE  = "app01_index.html"

app = Flask(__name__)
CORS(app)

@app.route("/api/greet", methods=["POST"])
def greet():
    data = request.get_json()
    name = (data.get("name") or "").strip()
    return jsonify({"message": f"Hello app01? {name}"})

class StaticHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    def log_message(self, *args):
        pass

def start_static_server(port):
    server = http.server.HTTPServer(("localhost", port), StaticHandler)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.serve_forever()

if __name__ == "__main__":

    url = f"http://localhost:{STATIC_PORT}/{INDEX_FILE}"

    # If API server already running, just open browser and exit
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('localhost', API_PORT)) == 0:
            webbrowser.open(url)
            sys.exit(0)

    # Kill any stale processes on both ports
    for port in [API_PORT, STATIC_PORT]:
        result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
        for pid_str in result.stdout.strip().split('\n'):
            if pid_str:
                try:
                    os.kill(int(pid_str), signal.SIGKILL)
                except Exception:
                    pass
    time.sleep(0.5)

    # Start static file server
    t = threading.Thread(target=start_static_server, args=(STATIC_PORT,), daemon=True)
    t.start()
    time.sleep(0.3)

    print(f"\n  App01")
    print(f"  UI  → {url}")
    print(f"  API → http://localhost:{API_PORT}\n")

    threading.Thread(
        target=lambda: (time.sleep(1.5), webbrowser.open(url)),
        daemon=True
    ).start()

    from waitress import serve
    serve(app, host="0.0.0.0", port=API_PORT, threads=4)
