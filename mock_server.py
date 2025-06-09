from http.server import HTTPServer, BaseHTTPRequestHandler

class FastMockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # send HTTP 200 OK immediately
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        # close log for each request to prevent stdout slow
        return

if __name__ == "__main__":
    HOST = "0.0.0.0"
    PORT = 8080
    print(f"🚀 Mock server listening on http://{HOST}:{PORT} (CTRL+C to stop)")
    server = HTTPServer((HOST, PORT), FastMockHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")