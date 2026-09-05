#!/usr/bin/env bash
# ==============================================================================
# Dispatches a test alert directly to Alertmanager to verify Telegram & Email routing
# ==============================================================================
set -e

ALERTMANAGER_URL="http://localhost:9093"
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "================================================================="
echo "🚨 Dispatches a Simulated High-Severity Alert to Alertmanager"
echo "================================================================="
echo "Target Alertmanager: $ALERTMANAGER_URL"

PAYLOAD='[
  {
    "labels": {
      "alertname": "TestHighCpuAndApiFailure",
      "severity": "critical",
      "category": "infrastructure",
      "service": "fastapi-service",
      "instance": "vps-master-node",
      "cluster": "primary-vps-cluster"
    },
    "annotations": {
      "summary": "Simulated Alert: Host CPU > 95% & API Error Rate Spike",
      "description": "This is a verified diagnostic test alert dispatched to test Telegram notifications and Alertmanager routing pipelines.",
      "runbook_url": "https://docs.local/runbooks/infra-high-cpu"
    },
    "startsAt": "'"$NOW"'"
  }
]'

echo -e "\nSending payload to $ALERTMANAGER_URL/api/v2/alerts..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$ALERTMANAGER_URL/api/v2/alerts" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD")

if [ "$HTTP_CODE" -eq 200 ]; then
  echo "✅ Test alert successfully accepted by Alertmanager (HTTP 200)."
  echo "👉 Check your Telegram channel/chat to confirm formatted alert receipt!"
else
  echo "❌ Failed to send alert (HTTP Status: $HTTP_CODE)."
fi
