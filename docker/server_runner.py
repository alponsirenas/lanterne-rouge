import os
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Ensure database directory exists
Path("data/memory").mkdir(parents=True, exist_ok=True)
Path("data/logs").mkdir(parents=True, exist_ok=True)

from scripts.daily_run import run_daily_logic

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def root():
    """Root endpoint that returns a welcome page with API information"""
    return """
    <html>
        <head>
            <title>Lanterne Rouge Tour Coach API</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    line-height: 1.6;
                }
                h1 {
                    color: #d9534f;
                }
                .endpoint {
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 15px;
                }
            </style>
        </head>
        <body>
            <h1>Lanterne Rouge Tour Coach API</h1>
            <p>Welcome to the Tour Coach API server. The following endpoints are available:</p>
            
            <div class="endpoint">
                <h3>GET /health</h3>
                <p>Health check endpoint to verify the server is running.</p>
            </div>
            
            <div class="endpoint">
                <h3>POST /run</h3>
                <p>Trigger the daily run process. This endpoint is typically called by n8n once per day.</p>
            </div>
            
            <div class="endpoint">
                <h3>GET /db-status</h3>
                <p>Check the status of the SQLite database connection.</p>
            </div>
        </body>
    </html>
    """

@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok"}

@app.get("/db-status")
def db_status():
    """Database status endpoint to verify SQLite connectivity"""
    from lanterne_rouge.memory_bus import DB_FILE, _get_conn
    
    try:
        # Check if database file exists
        db_exists = DB_FILE.exists()
        
        # Test connection and basic query
        conn = _get_conn()
        cursor = conn.execute("SELECT count(*) FROM memory")
        memory_count = cursor.fetchone()[0]
        conn.close()
        
        # Get database file size and permissions
        db_size = DB_FILE.stat().st_size if db_exists else 0
        db_permissions = oct(DB_FILE.stat().st_mode)[-3:] if db_exists else "N/A"
        
        return {
            "status": "ok",
            "database": {
                "path": str(DB_FILE),
                "exists": db_exists,
                "size_bytes": db_size,
                "permissions": db_permissions,
                "memory_entries": memory_count
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "database_path": str(DB_FILE)
        }

@app.post("/run")
def run():
    """
    n8n hits POST /run once per day.
    We return the JSON payload (summary + log)
    that downstream Email / GitHub nodes will use.
    """
    summary, log = run_daily_logic()
    return {"summary": summary, "log": log}