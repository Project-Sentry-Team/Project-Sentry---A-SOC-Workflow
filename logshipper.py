import json
import psycopg2
from datetime import datetime, UTC
import time
import os
import traceback

EVE_FILE = "/var/log/suricata/eve.json"

DB_CONFIG = {
    "host": "192.168.50.2",
    "dbname": "sentry_db",
    "user": "admin",
    "password": "password",
    "port": 5432
}

TABLE_NAME = "suricata_logs"

def db_connect():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print("Could not connect to Postgres:")
        traceback.print_exc()
        exit(1)

def is_duplicate(cur, alert_id, timestamp, src_ip, dst_ip):
    """
    Checks if an incident with the same alert_id, timestamp, src_ip, and dst_ip
    already exists in the suricata_logs table.
    """
    check_query = f"""
        SELECT 1 FROM {TABLE_NAME}
        WHERE alert_id = %s
          AND timestamp = %s
          AND src_ip = %s
          AND dst_ip = %s
        LIMIT 1
    """
    # alert_id is now a string or None, matching a VARCHAR/TEXT column
    cur.execute(check_query, (alert_id, timestamp, src_ip, dst_ip))
    return cur.fetchone() is not None

def insert_event(event_json):
    conn = None
    cur = None
    try:
        conn = db_connect()
        cur = conn.cursor()

        # Extract and explicitly convert alert_id to string to match VARCHAR column type
        alert_id_int = event_json.get("alert", {}).get("signature_id")
        # Convert to string if not None. This fixes the "character varying = integer" error.
        alert_id = str(alert_id_int) if alert_id_int is not None else None

        src_ip = event_json.get("src_ip")
        dst_ip = event_json.get("dest_ip") or event_json.get("dst_ip")
        src_port = event_json.get("src_port")
        dst_port = event_json.get("dest_port") or event_json.get("dst_port")
        timestamp = event_json.get("timestamp")
        raw_json_str = json.dumps(event_json)
        
        # FIX for DeprecationWarning: use UTC timezone-aware datetime
        created_at = datetime.now(UTC) 

        # --- DUPLICATE CHECK ---
        if alert_id and timestamp and src_ip and dst_ip and is_duplicate(cur, alert_id, timestamp, src_ip, dst_ip):
            print(f"Skipping duplicate alert {alert_id} from {src_ip} -> {dst_ip} at {timestamp}")
            return
        # -----------------------

        # Insert record, including incident_group_id
        query = f"""
            INSERT INTO {TABLE_NAME} (
                alert_id, timestamp, src_ip, dst_ip,
                src_port, dst_port, raw_json, incident_group_id, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (
            alert_id,
            timestamp,
            src_ip,
            dst_ip,
            src_port,
            dst_port,
            raw_json_str,
            None, # Inserting NULL for incident_group_id
            created_at
        ))
        conn.commit()
        print(f"Inserted alert {alert_id} from {src_ip} -> {dst_ip}")
    except Exception as e:
        print("DB Insert Error:")
        traceback.print_exc()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def follow_file(filename):
    """Simple tail -F style follower"""
    with open(filename, "r") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.2)
                continue
            yield line

def main():
    print("Sentry ingest started, watching eve.json...")
    if not os.path.exists(EVE_FILE):
        print(f"ERROR: {EVE_FILE} does not exist or cannot be read.")
        exit(1)

    for line in follow_file(EVE_FILE):
        try:
            event_json = json.loads(line)
        except json.JSONDecodeError:
            continue

        if event_json.get("event_type") != "alert":
            continue

        insert_event(event_json)

if __name__ == "__main__":
    main()