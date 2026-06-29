import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import sys
import os
import base64

# Simple helper to load .env file if it exists
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

load_env()

PORT = 3000
if len(sys.argv) > 1:
    try:
        PORT = int(sys.argv[1])
    except ValueError:
        pass

class ProxyRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        
        # Check if the request is for the API proxy
        if parsed_url.path == '/api/proxy':
            query_params = urllib.parse.parse_qs(parsed_url.query)
            barcode = query_params.get('barcode', [''])[0]
            
            if not barcode:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Barcode parameter is required"}).encode('utf-8'))
                return

            # Target 1C API endpoint
            # We must urlencode the barcode value because it contains special characters like ';'
            target_url = f"https://1c.ubtech.pro/test-trk-gkolymp/hs/mwp/getrests?barcode={urllib.parse.quote(barcode)}"
            
            # Get authorization credentials from environment
            onec_auth = os.environ.get('ONEC_AUTH')
            if not onec_auth:
                user = os.environ.get('ONEC_USER')
                password = os.environ.get('ONEC_PASSWORD')
                if user and password:
                    credentials = f"{user}:{password}"
                    encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
                    onec_auth = f"Basic {encoded}"
                else:
                    onec_auth = ""
            
            # Create the request with required headers
            req = urllib.request.Request(target_url, method='GET')
            req.add_header('Content-Type', 'application/json')
            if onec_auth:
                req.add_header('Authorization', onec_auth)
            
            try:
                # Execute the GET request
                with urllib.request.urlopen(req, timeout=10) as response:
                    status_code = response.status
                    response_data = response.read()
                    
                    # Send response back to the client
                    self.send_response(status_code)
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(response_data)
            except urllib.error.HTTPError as e:
                # Handle target server HTTP errors
                error_data = e.read()
                self.send_response(e.code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(error_data if error_data else json.dumps({"error": str(e)}).encode('utf-8'))
            except Exception as e:
                # Handle general errors (timeouts, dns resolution, connection refused)
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Proxy error: {str(e)}"}).encode('utf-8'))
        else:
            # Fallback to standard static file serving
            super().do_GET()

# Threaded server: each request is handled in its own thread, so one slow
# request (e.g. a hanging 1C proxy call or a kept-alive browser connection)
# can no longer block the entire site for every other client.
class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


def run_server():
    with ThreadingHTTPServer(("", PORT), ProxyRequestHandler) as httpd:
        print(f"Proxy Server running on port {PORT}")
        print("Serving static files and proxying /api/proxy -> 1C API")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            sys.exit(0)

if __name__ == '__main__':
    run_server()
