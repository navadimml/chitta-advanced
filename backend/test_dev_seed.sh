#!/bin/bash

# Quick development seed script
# Use this to quickly populate test data without going through the full conversation

API_URL="http://localhost:8000/api"

echo "🌱 Chitta Development Seed Script"
echo "=================================="
echo ""

# Show available scenarios
echo "📋 Available scenarios:"
curl -s "$API_URL/dev/scenarios" | jq -r '.scenarios | to_entries[] | "  - \(.key): \(.value.description)"'
echo ""

# Prompt for scenario
echo "Which scenario do you want to seed?"
echo "1) early_conversation - Basic info, no guidelines yet"
echo "2) guidelines_ready - Rich data, guidelines will generate"
echo "3) videos_uploaded - Simulated uploaded videos"
echo ""
read -p "Enter number (1-3): " choice

case $choice in
  1) SCENARIO="early_conversation" ;;
  2) SCENARIO="guidelines_ready" ;;
  3) SCENARIO="videos_uploaded" ;;
  *) echo "Invalid choice"; exit 1 ;;
esac

# Optional: custom family ID
read -p "Family ID (default: dev_test_family): " FAMILY_ID
FAMILY_ID=${FAMILY_ID:-dev_test_family}

echo ""
echo "🚀 Seeding scenario: $SCENARIO"
echo "   Family ID: $FAMILY_ID"
echo ""

# Seed the scenario
RESPONSE=$(curl -s -X POST "$API_URL/dev/seed/$SCENARIO?family_id=$FAMILY_ID")

# Show result
echo "$RESPONSE" | jq '.'

# Extract key info
SUCCESS=$(echo "$RESPONSE" | jq -r '.success')
if [ "$SUCCESS" = "true" ]; then
    echo ""
    echo "✅ Success!"
    echo ""
    echo "📊 Session state:"
    echo "$RESPONSE" | jq -r '.session_state | "  Completeness: \(.completeness * 100)%\n  Messages: \(.message_count)\n  Artifacts: \(.artifacts | length)"'
    echo ""
    echo "🌐 Now open your app with family_id=$FAMILY_ID"
    echo "   Example: http://localhost:3000/?family=$FAMILY_ID"
else
    echo ""
    echo "❌ Failed to seed scenario"
fi
