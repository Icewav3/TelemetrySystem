from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import csv
import os
from datetime import datetime
from pathlib import Path
import threading

class TelemetryHandler(BaseHTTPRequestHandler):
    # Directory to store data files
    DATA_DIR = Path("telemetry_data")
    _write_lock = threading.Lock()
    
    def do_POST(self):
        if self.path == '/telemetry':
            try:
                # Read request body
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf-8'))
                
                # Extract machine identifier (or use IP as fallback)
                machine_id = data.get('machine_id', self.client_address[0])
                
                # Create data directory if it doesn't exist
                self.DATA_DIR.mkdir(exist_ok=True)
                
                # Write to machine-specific CSV file with thread lock
                filename = self.DATA_DIR / f"{machine_id}_telemetry.csv"
                
                # Flatten nested structure (player_pos)
                player_pos = data.get('player_pos', {})
                csv_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'machine_id': machine_id,
                    'frame': data.get('frame'),
                    'player_pos_x': player_pos.get('x'),
                    'player_pos_y': player_pos.get('y'),
                    'player_pos_z': player_pos.get('z'),
                    'fps': data.get('fps'),
                    'memory_mb': data.get('memory_mb'),
                    'active_enemies': data.get('active_enemies')
                }
                
                fieldnames = ['timestamp', 'machine_id', 'frame', 'player_pos_x', 'player_pos_y', 'player_pos_z', 'fps', 'memory_mb', 'active_enemies']
                
                # Thread-safe CSV writing
                file_exists = filename.exists()
                with self._write_lock:
                    with open(filename, 'a', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        if not file_exists:
                            writer.writeheader()
                        writer.writerow(csv_entry)
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode())
                
                print(f"Received data from {machine_id}")
                
            except Exception as e:
                print(f"Error: {e}")
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging to reduce console spam
        pass

def run_server(port=8080):
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, TelemetryHandler)
    print(f"Server running on port {port}")
    print(f"Data will be saved to: {TelemetryHandler.DATA_DIR.absolute()}")
    print("Press Ctrl+C to stop")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()