# Daily Recipe Delivery Workflow Analysis

## Current Workflow Structure (ID: 54gNNDquW1NvWPGB)

### Node Flow
1. **Schedule Trigger** - Mon-Fri 4pm EST (cron: `0 16 * * 1-5`)
2. **Get Day of Week** - JavaScript code node that returns day name
3. **Fetch Today's Meal from Firebase** - HTTP request to Firebase RTDB
4. **Format Slack Message** - JavaScript code to build meal notification
5. **Post to Slack** - HTTP request to Slack API (#dinner-tonight channel)

### Current Data Flow
```
Schedule → Day Name → Firebase URL → Meal Object → Slack Message → Posted
```

### Firebase Structure Referenced
```
https://family-hub-dashboard-default-rtdb.firebaseio.com/meals/{dayOfWeek}.json
```

Expected meal object:
```json
{
  "name": "Chicken Tacos",
  "prepTime": "30 minutes",
  "url": "https://example.com/recipe"
}
```

---

## Required Modifications for Skip Logic

### New Workflow Structure

1. **Schedule Trigger** - (unchanged)
2. **Get Day of Week** - (unchanged)
3. **🆕 Check Google Calendar** - Query andreaschultz1116@gmail.com for today's events
4. **🆕 Read Holiday List** - Fetch holidays from Google Sheet
5. **🆕 Evaluate Skip Conditions** - Check all skip logic
6. **🆕 Branch: Skip or Send**
   - **IF SKIP:** Post skip notification to Slack → END
   - **IF SEND:** Continue to meal fetch
7. **Fetch Today's Meal from Firebase** - (unchanged)
8. **Format Slack Message** - (unchanged)
9. **Post to Slack** - (unchanged)

### Skip Conditions Logic

```javascript
// Skip if ANY of these are true:
1. Calendar has all-day event for today
2. Calendar event title contains "Andrea out of town"
3. Calendar event title contains "Andrea in [location]"
4. Today's date matches entry in Holiday list
5. (Future: Ad-hoc skip flag in Firebase)

// Default behavior: If calendar check fails → SEND (fail-open)
```

### New Nodes to Add

**Node A: Google Calendar - Get Events**
- Type: Google Calendar node (native n8n)
- Calendar: andreaschultz1116@gmail.com
- Query: Events for today (start of day to end of day)
- Output: Array of calendar events

**Node B: Google Sheets - Read Holiday List**
- Type: Google Sheets node (native n8n)
- Sheet: "Meal Planning Data"
- Tab: "Holidays"
- Range: A2:B50 (Date | Holiday Name)
- Output: Array of holiday objects

**Node C: Skip Logic Evaluator**
- Type: Code node (JavaScript)
- Inputs: Calendar events, Holiday list, today's date
- Logic: Evaluate all skip conditions
- Output: { shouldSkip: boolean, reason: string }

**Node D: IF Node - Route Based on Skip**
- Type: IF node (native n8n)
- Condition: `{{ $json.shouldSkip }} === true`
- True branch: Skip notification
- False branch: Continue to meal fetch

**Node E: Skip Notification**
- Type: Code node (JavaScript)
- Build skip message: "🚫 No recipe today - [reason]"
- Output: Slack message object

**Node F: Post Skip to Slack**
- Type: HTTP Request (same as current Post to Slack)
- Channel: #dinner-tonight (same channel)
- Message: Skip notification

---

## Implementation Strategy

### Phase 1: Google Sheet Holiday List
1. Create "Holidays" tab in "Meal Planning Data" Google Sheet
2. Add 2026 major US holidays
3. Format: Column A = Date (YYYY-MM-DD), Column B = Holiday Name

### Phase 2: Add Skip Logic Nodes (Before Firebase Fetch)
1. Insert Google Calendar node after "Get Day of Week"
2. Insert Google Sheets node (parallel or sequential)
3. Insert Skip Logic Evaluator code node
4. Insert IF node for branching
5. Insert Skip Notification nodes (true branch)
6. Connect false branch to existing "Fetch Today's Meal from Firebase"

### Phase 3: Testing
1. Test with real calendar event (all-day)
2. Test with travel event ("Andrea out of town")
3. Test with holiday date
4. Test normal day (should send recipe)
5. Test calendar API failure (should fail-open and send recipe)

---

## Risk Assessment

**Low Risk:**
- Reading Google Calendar (read-only)
- Reading Google Sheets (read-only)
- Adding code nodes (no external side effects)

**Medium Risk:**
- IF node branching (could break existing flow if misconfigured)
- Skip notification format (user-facing message)

**Mitigation:**
- Backup already complete
- Test with manual workflow execution before activating schedule
- Fail-open default (calendar failure → send recipe)

---

## Google Sheet Structure

### New "Holidays" Tab
| Date       | Holiday Name       |
|------------|--------------------|
| 2026-01-01 | New Year's Day     |
| 2026-05-25 | Memorial Day       |
| 2026-07-04 | Independence Day   |
| 2026-09-07 | Labor Day          |
| 2026-11-26 | Thanksgiving       |
| 2026-12-25 | Christmas          |

Format: Simple two-column table, no headers in row 1 (headers in visualization only)
Range: A2:B50 (allows for ~40 holidays)
