# Sentry

**Security Operations Center Digital Watchtower**

An AI-assisted workflow solution designed to reduce alert fatigue, improve SOC response times, and provide actionable, contextual security intelligence.

---

## Problem Statement

SOC analysts face **thousands of daily alerts**, with 90% being false positives. This leads to:

- Burnout and analyst fatigue
- Slower response to real threats
- Poor communication between technical teams and leadership

Current SOC tools fail to provide **contextualized, prioritized, or plain-English explanations** of security events.

---

## Solution

**Project Sentry** is an AI-assisted workflow solution that:

1. **Ingests** Suricata IDS alerts (JSON logs, enterprise-grade & multi-threaded)
2. **Processes** alerts through n8n for normalization and enrichment (IP-API, NVD CVE feed)
3. **Analyzes** enriched alerts using a lightweight local LLM (via Ollama) or AI API service that:
   - Uses live data fetching for CVE data from NIST NVD databases and IP-API
   - Generates incident reports for both technical teams and non-technical leadership
   - Provides clear recommendations and prioritization

---

## Key Features

- **Reduces noise & alert fatigue** through intelligent filtering
- **Improves decision-making speed** with contextualized insights
- **Scales without retraining** LLMs or overcomplicating SOC stack
- **Integrates seamlessly** with existing SOC tools
- **Generates accurate reports** at least 75% of the time

---

## Tech Stack

| Component | Purpose | Notes |
|-----------|---------|-------|
| **Suricata IDS** | Detect suspicious activity | Outputs clean JSON logs |
| **n8n (Docker)** | Workflow automation | Normalizes & enriches alerts; interfaces with LLM |
| **Ollama LLM (local)** | Alert summarization & report generation | API key used for demo due to lack of compute. Local Ollama supports 7-70B parameter models in production |
| **CVE/NIST database** | Threat enrichment | Pulled dynamically for context |
| **Docker** | Containerization | Ensures reproducibility, internet access works out-of-the-box |

---

## Architecture Flow

```
Suricata → Detect suspicious activity → 
Python Microservice/Bash script aggregates logs → 
PostgreSQL DB → 
Postgres aggregates logs, groups into incident groups (by timestamp & similar info) → 
n8n enriches data using scripts/APIs (GeoIP, WHOIS, etc.) → 
LLM analyzes enriched data → 
Generates short report as JSON object → 
Exports to dashboard
```

---

## Demo

The demo showcases:

- Sample Suricata alerts fed through n8n → Ollama
- **Output:** Readable, plain-English incident reports in Markdown/HTML
- Optional small dashboard or terminal view showing:
  - Alerts
  - LLM-generated report
  - Prioritization and recommended next steps

**Note:** Demo uses API key due to compute limitations. Production deployments can scale up to 70B parameter models for enterprise use.

---

## Future Roadmap

- **Self-contained package** for ease of integration (single application or script)
- **Incident grouping** implementation
- **Parameter tuning** to increase accuracy beyond 75%
- **Secure dashboard hosting** for production-ready deployments

---

## Getting Started

*Coming soon: Installation and setup instructions*

---

## License

*Add license information here*

---

## Contributing

*Add contribution guidelines here*