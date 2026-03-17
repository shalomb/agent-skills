#!/bin/bash

# Team Description Script for TargetProcess using tpcli
# Usage: TP_TOKEN=xxx TP_URL=yyy ./scripts/describe-team.sh [TEAM_ID]
# Example: TP_TOKEN=xxx TP_URL=yyy ./scripts/describe-team.sh 1001

TEAM_ID=${1:-1001}
TP_URL=${TP_URL:-https://example.tpondemand.com}
TP_TOKEN=${TP_TOKEN:-}

if [ -z "$TP_TOKEN" ]; then
  echo "Error: TP_TOKEN environment variable not set"
  exit 1
fi

TPCLI="${TPCLI:-tpcli}"

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                    TEAM PROFILE: $TEAM_ID                           ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Get team details
echo "=== TEAM INFORMATION ==="
TP_URL="$TP_URL" TP_TOKEN="$TP_TOKEN" $TPCLI get Teams $TEAM_ID 2>/dev/null | jq '{
  Name,
  Owner: .Owner.FirstName,
  Status: (if .IsActive then "Active" else "Inactive" end),
  PeopleCount: (.CustomFields[] | select(.Name == "People Count") | .Value),
  ART: .AgileReleaseTrain.Name,
  JIRA_Project: (.CustomFields[] | select(.Name == "JIRA Project Key") | .Value)
}'
echo ""

# Get features assigned to team
echo "=== FEATURES ASSIGNED TO TEAM ==="
FEATURES=$(TP_URL="$TP_URL" TP_TOKEN="$TP_TOKEN" $TPCLI list Features --where "Team.Id eq $TEAM_ID" --take 100 2>/dev/null)
FEATURE_COUNT=$(echo "$FEATURES" | jq 'length')
echo "Total Features: $FEATURE_COUNT"
echo ""

if [ "$FEATURE_COUNT" -gt 0 ]; then
  echo "Features:"
  echo "$FEATURES" | jq -r '.[] | "  \(.Id): \(.Name) [\(.EntityState.Name)] - Priority: \(.Priority.Name)"' | head -10
  echo ""
fi

# Get user stories assigned to team
echo "=== USER STORIES ASSIGNED TO TEAM ==="
STORIES=$(TP_URL="$TP_URL" TP_TOKEN="$TP_TOKEN" $TPCLI list UserStories --where "Team.Id eq $TEAM_ID" --take 100 2>/dev/null)
STORY_COUNT=$(echo "$STORIES" | jq 'length')
echo "Total Stories: $STORY_COUNT"

if [ "$STORY_COUNT" -gt 0 ]; then
  TOTAL_EFFORT=$(echo "$STORIES" | jq '[.[].Effort] | add // 0')
  OPEN_COUNT=$(echo "$STORIES" | jq '[.[] | select(.EntityState.Name != "Done")] | length')
  DONE_COUNT=$(echo "$STORIES" | jq '[.[] | select(.EntityState.Name == "Done")] | length')

  echo "Total Effort: $TOTAL_EFFORT points"
  echo "Status: $OPEN_COUNT open, $DONE_COUNT done"
  echo ""

  echo "By Status:"
  echo "$STORIES" | jq -r '[group_by(.EntityState.Name)[] | {status: .[0].EntityState.Name, count: length, effort: map(.Effort) | add}] | .[] | "  \(.status): \(.count) stories, \(.effort) effort"'
  echo ""

  echo "First 5 Stories:"
  echo "$STORIES" | jq -r '.[:5] | .[] | "  \(.Id): \(.Name) [\(.EntityState.Name)] - \(.Effort) effort"'
  echo ""
fi

# Get bugs assigned to team
echo "=== BUGS ASSIGNED TO TEAM ==="
BUGS=$(TP_URL="$TP_URL" TP_TOKEN="$TP_TOKEN" $TPCLI list Bugs --where "Team.Id eq $TEAM_ID" --take 100 2>/dev/null)
BUG_COUNT=$(echo "$BUGS" | jq 'length')
echo "Total Bugs: $BUG_COUNT"

if [ "$BUG_COUNT" -gt 0 ]; then
  echo ""
  echo "Bug Summary:"
  echo "$BUGS" | jq -r '[group_by(.EntityState.Name)[] | {status: .[0].EntityState.Name, count: length}] | .[] | "  \(.status): \(.count) bugs"'
  echo ""
fi

# Get tasks assigned to team
echo "=== TASKS ASSIGNED TO TEAM ==="
TASKS=$(TP_URL="$TP_URL" TP_TOKEN="$TP_TOKEN" $TPCLI list Tasks --where "Team.Id eq $TEAM_ID" --take 100 2>/dev/null)
TASK_COUNT=$(echo "$TASKS" | jq 'length')
echo "Total Tasks: $TASK_COUNT"

if [ "$TASK_COUNT" -gt 0 ]; then
  echo ""
  echo "Task Summary:"
  echo "$TASKS" | jq -r '[group_by(.EntityState.Name)[] | {status: .[0].EntityState.Name, count: length, timeSpent: map(.TimeSpent // 0) | add, timeRemain: map(.TimeRemain // 0) | add}] | .[] | "  \(.status): \(.count) tasks, \(.timeSpent) spent, \(.timeRemain) remaining"'
  echo ""
fi

# Summary
echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                         WORKLOAD SUMMARY                              ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""
TOTAL_ITEMS=$((FEATURE_COUNT + STORY_COUNT + BUG_COUNT + TASK_COUNT))
echo "Total Work Items: $TOTAL_ITEMS"
echo "  • Features:  $FEATURE_COUNT"
echo "  • Stories:   $STORY_COUNT"
echo "  • Bugs:      $BUG_COUNT"
echo "  • Tasks:     $TASK_COUNT"
echo ""
echo "View in UI: $TP_URL/RestUI/Board.aspx#boardPopup=team/$TEAM_ID/silent"
echo ""
