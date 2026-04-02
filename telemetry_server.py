import json
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# IP: http://10.20.5.27:8080/telemetry


class TelemetryHandler(BaseHTTPRequestHandler):
    """
    Telemetry server for UE5 Playtest Data Collection
    Receives JSON events from multiple clients and writes to single JSONL file
    """

    DATA_FILE = Path("data") / "telemetry.jsonl"
    _write_lock = threading.Lock()
    _event_count = 0

    def do_POST(self):
        if self.path == "/telemetry":
            try:
                # Read request body
                content_length = int(self.headers["Content-Length"])
                body = self.rfile.read(content_length)
                data = json.loads(body.decode("utf-8"))

                # Add server-side timestamp for verification
                data["server_timestamp"] = datetime.now().isoformat()

                # Ensure data directory exists
                self.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

                # Thread-safe write to single JSONL file (one JSON object per line)
                with self._write_lock:
                    with open(self.DATA_FILE, "a") as f:
                        f.write(json.dumps(data) + "\n")
                        f.flush()  # Ensure immediate write to disk

                    # Increment event counter
                    TelemetryHandler._event_count += 1

                # Send success response
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())

                # Periodic logging (every 50 events to reduce spam)
                event_type = data.get("event_type", "unknown")
                if TelemetryHandler._event_count % 10 == 0:
                    print(
                        f"[{TelemetryHandler._event_count}] Received {event_type} from "
                        f"{data.get('machine_id', 'unknown')} session {data.get('session_id', 'unknown')}"
                    )

                # Log important events immediately
                if event_type in ["session_start", "session_end", "death"]:
                    print(
                        f"[{event_type.upper()}] {data.get('machine_id')} - {data.get('session_id')}"
                    )

            except json.JSONDecodeError as e:
                print(f"JSON Error: {e}")
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(
                    json.dumps({"status": "error", "message": "Invalid JSON"}).encode()
                )
            except Exception as e:
                print(f"Server Error: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress default HTTP logging to reduce console spam
        pass


def run_server(port=8080):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, TelemetryHandler)

    print("=" * 60)
    print("UE5 TELEMETRY SERVER")
    print("=" * 60)
    print(f"Server running on port {port}")
    print(f"Data file: {TelemetryHandler.DATA_FILE.absolute()}")
    print("Listening for events from UE5 clients...")
    print("Press Ctrl+C to stop\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(
            f"\n\nServer stopped. Total events received: {TelemetryHandler._event_count}"
        )
        print(f"Data saved to: {TelemetryHandler.DATA_FILE.absolute()}")


if __name__ == "__main__":
    run_server()
