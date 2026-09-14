#!/bin/bash
echo "📊 PersonaVault Platform Dashboard"
echo "=================================="
echo ""

# Get trends for all domains
for domain in incident_response compliance_review contract_review procurement_decision underwriting_decision; do
    echo "🔹 $(echo $domain | tr '[:lower:]' '[:upper:]'):"
    curl -s "http://localhost:8000/api/v1/timeline/trends/$domain?days=30" -b cookies.txt | python -m json.tool | grep -E "total_events|average_confidence|trend|decision_distribution"
    echo ""
done
