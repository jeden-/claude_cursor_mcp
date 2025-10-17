#!/usr/bin/env python3
"""
Simple HTTP server to serve dashboard with real data from SQLite
"""
import json
import sqlite3
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.parse

# Import orchestrator config
import sys
sys.path.insert(0, str(Path(__file__).parent))
from cursor_orchestrator_advanced import Config

class DashboardHandler(SimpleHTTPRequestHandler):
    """Custom handler for dashboard API"""
    
    def do_GET(self):
        """Handle GET requests"""
        
        # Parse URL
        parsed = urllib.parse.urlparse(self.path)
        
        # API endpoint for stats
        if parsed.path == '/api/stats':
            self.send_json_response(self.get_stats())
            
        # API endpoint for tasks
        elif parsed.path == '/api/tasks':
            self.send_json_response(self.get_tasks())
            
        # API endpoint for watching
        elif parsed.path == '/api/watching':
            self.send_json_response(self.get_watching())
            
        # Serve static files
        else:
            super().do_GET()
    
    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def get_stats(self):
        """Get statistics from database"""
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            cursor = conn.cursor()
            
            # Get counts by status
            cursor.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status")
            status_counts = dict(cursor.fetchall())
            
            # Get total
            cursor.execute("SELECT COUNT(*) FROM tasks")
            total = cursor.fetchone()[0]
            
            # Get watching count (active file watchers)
            cursor.execute("SELECT COUNT(DISTINCT project_path) FROM tasks")
            watching = cursor.fetchone()[0]
            
            conn.close()
            
            completed = status_counts.get('completed', 0)
            running = status_counts.get('running', 0)
            failed = status_counts.get('failed', 0)
            
            success_rate = round((completed / total * 100) if total > 0 else 0, 1)
            
            return {
                'total': total,
                'completed': completed,
                'running': running,
                'failed': failed,
                'watching': watching,
                'success_rate': f'{success_rate}%'
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_tasks(self):
        """Get recent tasks"""
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, description, status, project_path, created_at
                FROM tasks 
                ORDER BY created_at DESC 
                LIMIT 20
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            tasks = []
            for row in rows:
                tasks.append({
                    'id': row[0],
                    'description': row[1],
                    'status': row[2],
                    'project_path': row[3],
                    'created_at': row[4]
                })
            
            return {'tasks': tasks}
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_watching(self):
        """Get watched projects"""
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT project_path 
                FROM tasks 
                ORDER BY project_path
            """)
            
            rows = cursor.fetchall()
            conn.close()
            
            projects = [row[0] + '/.cursor-tasks' for row in rows]
            
            return {'projects': projects}
            
        except Exception as e:
            return {'error': str(e)}

def run_server(port=8000):
    """Run HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║  🤖 Claude-Cursor Orchestrator Dashboard Server          ║
╚═══════════════════════════════════════════════════════════╝

🌐 Server running at: http://localhost:{port}
📊 Dashboard: http://localhost:{port}/dashboard.html
🔌 API endpoints:
   • http://localhost:{port}/api/stats
   • http://localhost:{port}/api/tasks
   • http://localhost:{port}/api/watching

Press Ctrl+C to stop
""")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
        httpd.server_close()

if __name__ == '__main__':
    run_server()

