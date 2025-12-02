import json
import os
import time
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.')

# --- CONFIGURATION ---
DB_FILE = 'server_reports.json'
PORT = 5000

# --- SEED DATA (Used if no DB file exists) ---
SEED_DATA = [
    {
        "id": 1700000001,
        "technical_report": {
            "title": "SQL Injection Attack Detected",
            "priority": "MEDIUM",
            "summary": "A SQL injection attempt was detected in a web application.",
            "attacker_ip": "185.220.101.47",
            "victim_ip": "10.0.50.22",
            "what_happened": "The attacker used an SQL Injection attack vector by sending malicious data through the application's input, specifically targeting the URI parameter 'id'.",
            "immediate_actions": [
                "Review and patch affected web application components",
                "Change default values for all input parameters"
            ]
        },
        "leadership_report": {
            "title": "Potential Web Application Vulnerability Exploited",
            "risk_level": "MEDIUM",
            "what_happened": "An attacker attempted to exploit a SQL injection vulnerability in our web application.",
            "business_impact": "Potential unauthorized viewing or modification of user information, leading to reputational harm and legal repercussions.",
            "what_we_are_doing": [
                "Investigating the attempted attack vector",
                "Monitoring for unauthorized access"
            ]
        }
    }
]

# --- HELPERS ---

def load_reports():
    """Loads reports from the JSON file. Creates file with seed data if missing."""
    if not os.path.exists(DB_FILE):
        save_reports(SEED_DATA)
        return SEED_DATA
    
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        # Fallback if file is corrupted
        return []

def save_reports(reports):
    """Saves the list of reports to the JSON file."""
    with open(DB_FILE, 'w') as f:
        json.dump(reports, f, indent=4)

# --- ROUTES ---

@app.route('/')
def serve_dashboard():
    """Serves the main HTML dashboard."""
    return send_from_directory('.', 'dashboard.html')

@app.route('/api/reports', methods=['GET'])
def get_reports():
    """API Endpoint: Get all reports."""
    reports = load_reports()
    return jsonify(reports)

@app.route('/api/reports', methods=['POST'])
def add_report():
    """
    API Endpoint: Accept a new JSON report.
    Handles standard JSON and wrapped JSON strings (common in n8n/webhooks).
    """
    raw_data = request.get_json(silent=True)
    
    if not raw_data:
        # Fallback: try parsing form data if JSON wasn't detected
        if request.form:
            raw_data = request.form.to_dict()
        else:
            return jsonify({"error": "Invalid JSON or empty body"}), 400

    data = raw_data

    # --- ADAPTER: Unwrap Nested/Stringified JSON ---
    # Many automation tools send the payload in { "body": { "log": "stringified_json" } }
    # or simply { "log": "stringified_json" }
    try:
        # Case 1: Nested in body.log (The error case you provided)
        if 'body' in data and isinstance(data['body'], dict) and 'log' in data['body']:
            log_content = data['body']['log']
            if isinstance(log_content, str):
                data = json.loads(log_content)
        
        # Case 2: Direct "log" key with stringified JSON
        elif 'log' in data and isinstance(data['log'], str):
            data = json.loads(data['log'])
            
    except (json.JSONDecodeError, TypeError) as e:
        print(f"[!] Failed to parse inner JSON string: {e}")
        # Continue with original data to see if it works anyway

    # Basic Validation
    if 'technical_report' not in data or 'leadership_report' not in data:
        print(f"[!] Schema Error. Keys found: {list(data.keys())}")
        return jsonify({
            "error": "Invalid schema. Must contain 'technical_report' and 'leadership_report'",
            "received_keys": list(data.keys())
        }), 400
    
    # Add an ID and Timestamp
    new_report = data.copy()
    new_report['id'] = int(time.time() * 1000) # Unique ID based on time
    new_report['received_at'] = time.ctime()

    # Save to DB
    reports = load_reports()
    reports.append(new_report)
    save_reports(reports)

    print(f"[+] Received new report: {new_report['technical_report'].get('title', 'Untitled')}")
    
    return jsonify({"message": "Report accepted", "id": new_report['id']}), 201

if __name__ == '__main__':
    # host='0.0.0.0' allows the server to be accessible externally (e.g., from 192.168.0.99)
    print(f"[*] Starting Sentry Server on http://192.168.0.99:{PORT}")
    print(f"[*] Send POST requests to http://192.168.0.99:{PORT}/api/reports")
    app.run(host='0.0.0.0', port=PORT, debug=True)