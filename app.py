import os
import time
import psycopg2
from fastapi import FastAPI, Response, status

app = FastAPI(title="Fleet Management Health API", version="1.0.0")

START_TIME = time.time()

DB_HOST = os.getenv("DB_HOST", "db")
DB_NAME = os.getenv("DB_NAME", "fleet_db")
DB_USER = os.getenv("DB_USER", "fleet_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "fleet_secure_pass")
DB_PORT = os.getenv("DB_PORT", "5432")

def check_db_connection():
    """Verify live connectivity to PostgreSQL database"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
            connect_timeout=3
        )
        conn.close()
        return True, "connected"
    except Exception as e:
        return False, str(e)

@app.get("/healthz", status_code=status.HTTP_200_OK)
def health_check(response: Response):
    """Liveness & Readiness probe endpoint for orchestrators"""
    uptime = time.time() - START_TIME
    db_healthy, db_message = check_db_connection()
    
    overall_status = "healthy" if db_healthy else "degraded"
    if not db_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": overall_status,
        "uptime_seconds": round(uptime, 2),
        "database": {
            "status": "up" if db_healthy else "down",
            "details": db_message
        },
        "environment": os.getenv("APP_ENV", "development"),
        "worker_pid": os.getpid()
    }

@app.get("/api/v1/info")
def service_info():
    """Service metadata endpoint"""
    return {
        "service": "fleet-telemetry-service",
        "version": "1.0.0",
        "maintainer": "DevOps Engineering Team"
    }