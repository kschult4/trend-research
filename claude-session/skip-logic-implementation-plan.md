# Skip Logic Implementation Plan
## Daily Recipe Delivery Workflow Modification

**Date:** 2026-02-07
**Roadmap:** Meal-Planner-Improvements.md
**Criterion:** 1 - Smart Skip Logic Implementation
**Workflow ID:** 54gNNDquW1NvWPGB

---

## Current Workflow (5 nodes)

```mermaid
Schedule → Get Day of Week → Fetch Meal from Firebase → Format Message → Post to Slack
```

**Node Details:**
1. **Schedule Trigger** - Cron: `0 16 * * 1-5` (Mon-Fri 4pm EST)
2. **Get Day of Week** - Code node returns `{ dayOfWeek: "Monday" }`
3. **Fetch Meal** - HTTP GET `firebase.../meals/{dayOfWeek}.json`
4. **Format Message** - Code node builds Slack message
5. **Post to Slack** - HTTP POST to Slack API (#dinner-tonight)

---

## New Workflow (12 nodes)

```mermaid
Schedule → Get Day of Week → Get Today's Date →
  ├─> Google Calendar (Query Events) ─┐
  └─> Google Sheets (Read Holidays) ──┤
                                       ↓
                              Skip Logic Evaluator
                                       ↓
                                   IF Node
                          ┌──────────┴──────────┐
                       SKIP                   SEND
                          ↓                      ↓
                  Format Skip Msg          Fetch Meal
                          ↓                      ↓
                  Post Skip to Slack      Format Meal Msg
                                               ↓
                                         Post Meal to Slack
```

---

## New Nodes to Add

### Node 3: Get Today's Date (Code Node)
**Position:** After "Get Day of Week"
**Purpose:** Generate today's date in multiple formats for calendar/holiday checks

```javascript
// Get today's date in various formats
const today = new Date();

// Format: YYYY-MM-DD (for holiday comparison)
const year = today.getFullYear();
const month = String(today.getMonth() + 1).padStart(2, '0');
const day = String(today.getDate()).padStart(2, '0');
const dateString = `${year}-${month}-${day}`;

// Start and end of day for calendar query (ISO format)
const startOfDay = new Date(today);
startOfDay.setHours(0, 0, 0, 0);

const endOfDay = new Date(today);
endOfDay.setHours(23, 59, 59, 999);

return {
  dateString: dateString,           // "2026-02-07"
  dayOfWeek: $input.first().json.dayOfWeek,  // Pass through from previous node
  startOfDay: startOfDay.toISOString(),      // ISO timestamp
  endOfDay: endOfDay.toISOString()           // ISO timestamp
};
```

**Output:**
```json
{
  "dateString": "2026-02-07",
  "dayOfWeek": "Friday",
  "startOfDay": "2026-02-07T05:00:00.000Z",
  "endOfDay": "2026-02-07T04:59:59.999Z"
}
```

---

### Node 4a: Google Calendar - Get Events
**Type:** Google Calendar node (native n8n)
**Operation:** Get Many
**Configuration:**
- **Calendar ID:** `andreaschultz1116@gmail.com`
- **Start Time:** `{{ $json.startOfDay }}`
- **End Time:** `{{ $json.endOfDay }}`
- **Return All:** Yes (get all events for today)

**Expected Output:** Array of calendar events
```json
[
  {
    "summary": "Andrea out of town",
    "start": { "dateTime": "2026-02-07T09:00:00-05:00" },
    "end": { "dateTime": "2026-02-07T17:00:00-05:00" },
    "isAllDay": false
  }
]
```

**Auth Required:** Google OAuth2 with Calendar Read scope
**Credential Name:** "Andrea's Google Calendar" (to be created)

---

### Node 4b: Google Sheets - Read Holiday List
**Type:** Google Sheets node (native n8n)
**Operation:** Read Sheet Data
**Configuration:**
- **Document:** "Meal Planning Data" (by ID or name)
- **Sheet Name:** "Holidays"
- **Range:** `A2:B50` (no headers, just data)
- **RAW Data:** No (parse as structured data)

**Expected Output:** Array of holiday objects
```json
[
  { "Date": "2026-01-01", "Holiday": "New Year's Day" },
  { "Date": "2026-12-25", "Holiday": "Christmas" },
  ...
]
```

**Auth Required:** Google Sheets API (likely already configured for Meal Planner)
**Credential Name:** Check existing credential from Meal Planner workflow

---

### Node 5: Skip Logic Evaluator (Code Node)
**Position:** After both Calendar and Sheets nodes (merge)
**Purpose:** Evaluate all skip conditions and determine whether to skip

```javascript
// Get inputs
const calendarEvents = $input.first().json; // From Google Calendar node
const holidays = $input.all()[1].json;      // From Google Sheets node
const todayDate = $input.first().json.dateString; // "2026-02-07"

// Initialize skip state
let shouldSkip = false;
let skipReason = "";

// SKIP CONDITION 1: Check holidays
const isHoliday = holidays.some(holiday => holiday.Date === todayDate);
if (isHoliday) {
  shouldSkip = true;
  const holidayName = holidays.find(h => h.Date === todayDate).Holiday;
  skipReason = `Holiday: ${holidayName}`;
}

// SKIP CONDITION 2: Check calendar events (only if not already skipping)
if (!shouldSkip && calendarEvents && calendarEvents.length > 0) {
  for (const event of calendarEvents) {
    const title = event.summary || "";

    // Check for all-day events
    if (event.start.date && !event.start.dateTime) {
      shouldSkip = true;
      skipReason = `All-day event: ${title}`;
      break;
    }

    // Check for "Andrea out of town" pattern
    if (title.toLowerCase().includes("andrea out of town")) {
      shouldSkip = true;
      skipReason = `Andrea out of town`;
      break;
    }

    // Check for "Andrea in [location]" pattern
    const inLocationMatch = title.match(/andrea in ([a-zA-Z\s]+)/i);
    if (inLocationMatch) {
      shouldSkip = true;
      skipReason = `Andrea in ${inLocationMatch[1]}`;
      break;
    }
  }
}

// FAIL-OPEN: If calendar check failed (no data), default to sending
if (!calendarEvents) {
  shouldSkip = false;
  skipReason = "Calendar check failed - defaulting to send";
}

return {
  shouldSkip: shouldSkip,
  skipReason: skipReason,
  dayOfWeek: $input.first().json.dayOfWeek,  // Pass through for meal fetch
  dateString: todayDate
};
```

**Output:**
```json
{
  "shouldSkip": true,
  "skipReason": "Andrea out of town",
  "dayOfWeek": "Friday",
  "dateString": "2026-02-07"
}
```

---

### Node 6: IF Node - Route Based on Skip Decision
**Type:** IF node (native n8n)
**Condition:**
- **Value 1:** `{{ $json.shouldSkip }}`
- **Operation:** `equals`
- **Value 2:** `true`

**Routing:**
- **True branch (output 0):** Skip notification path
- **False branch (output 1):** Continue to meal fetch (existing flow)

---

### Node 7 (True Branch): Format Skip Notification (Code Node)
**Position:** True branch from IF node
**Purpose:** Build skip notification message for Slack

```javascript
const reason = $input.first().json.skipReason;
const date = $input.first().json.dateString;

const message = `🚫 *No recipe today* (${date})\\n\\n` +
  `*Reason:* ${reason}\\n\\n` +
  `Enjoy your evening! 🌟`;

return {
  channel: '#dinner-tonight',
  text: message
};
```

**Output:**
```json
{
  "channel": "#dinner-tonight",
  "text": "🚫 *No recipe today* (2026-02-07)\n\n*Reason:* Andrea out of town\n\nEnjoy your evening! 🌟"
}
```

---

### Node 8 (True Branch): Post Skip to Slack (HTTP Request)
**Type:** HTTP Request node
**Method:** POST
**URL:** `https://slack.com/api/chat.postMessage`
**Authentication:** HTTP Header Auth (Slack Bot Token)
**Headers:**
- `Content-Type: application/json`

**Body Parameters:**
- `channel`: `{{ $json.channel }}`
- `text`: `{{ $json.text }}`

**Credentials:** Use existing "Slack Bot Token" credential

---

### Nodes 9-11 (False Branch): Existing Meal Flow
**No changes required** - these nodes remain as-is:
- Node 9: Fetch Today's Meal from Firebase
- Node 10: Format Slack Message
- Node 11: Post to Slack

---

## Implementation Steps

### Step 1: Access n8n Workflow Editor
```bash
# Open n8n UI in browser
open http://192.168.1.11:5678

# Navigate to: Daily Recipe Delivery workflow (ID: 54gNNDquW1NvWPGB)
```

### Step 2: Add Google Calendar Credential (if needed)
1. Go to Credentials → Add Credential
2. Select "Google Calendar OAuth2 API"
3. Name: "Andrea's Google Calendar"
4. Complete OAuth flow for andreaschultz1116@gmail.com
5. Scope: `https://www.googleapis.com/auth/calendar.readonly`

### Step 3: Verify Google Sheets Credential Exists
1. Check existing Meal Planner workflow for Google Sheets credential
2. Note credential ID/name
3. Reuse same credential for Holiday list reading

### Step 4: Add New Nodes (in order)
1. Insert "Get Today's Date" code node after "Get Day of Week"
2. Add "Google Calendar - Get Events" node (parallel path)
3. Add "Google Sheets - Read Holiday List" node (parallel path)
4. Add "Skip Logic Evaluator" code node (merge both paths)
5. Add "IF Node" for routing
6. Add "Format Skip Notification" code node (true branch)
7. Add "Post Skip to Slack" HTTP node (true branch)
8. Reconnect existing "Fetch Meal" node to false branch

### Step 5: Configure Node Connections
```
Schedule → Get Day of Week → Get Today's Date
                                    ↓
                              (splits to two paths)
                                    ↓
                  ┌─────────────────┴─────────────────┐
                  ↓                                   ↓
         Google Calendar Node              Google Sheets Node
                  ↓                                   ↓
                  └─────────────────┬─────────────────┘
                                    ↓
                          Skip Logic Evaluator
                                    ↓
                                IF Node
                        ┌───────────┴───────────┐
                        ↓ (true)                ↓ (false)
              Format Skip Msg          Fetch Meal (existing)
                        ↓                       ↓
              Post Skip to Slack      Format Meal Msg (existing)
                                               ↓
                                      Post Meal to Slack (existing)
```

### Step 6: Test with Manual Execution
1. Deactivate workflow (turn off schedule)
2. Click "Execute Workflow" manually
3. Verify calendar query works
4. Verify holiday list loads
5. Test skip logic with various scenarios
6. Verify messages post correctly to Slack

### Step 7: Activate Modified Workflow
1. Verify all tests pass
2. Re-activate workflow schedule
3. Monitor first scheduled execution (next Mon-Fri 4pm)

---

## Testing Scenarios

### Test 1: Normal Day (Should Send Recipe)
- **Setup:** No calendar events, no holiday
- **Expected:** Recipe fetched and posted to Slack
- **Verification:** Check #dinner-tonight for meal message

### Test 2: Holiday (Should Skip)
- **Setup:** Today's date matches entry in Holiday list
- **Expected:** Skip notification posted
- **Verification:** Message says "Holiday: [name]"

### Test 3: All-Day Calendar Event (Should Skip)
- **Setup:** Create all-day event in Andrea's calendar
- **Expected:** Skip notification posted
- **Verification:** Message says "All-day event: [title]"

### Test 4: Travel Event (Should Skip)
- **Setup:** Create event titled "Andrea out of town"
- **Expected:** Skip notification posted
- **Verification:** Message says "Andrea out of town"

### Test 5: Location Event (Should Skip)
- **Setup:** Create event titled "Andrea in Boston"
- **Expected:** Skip notification posted
- **Verification:** Message says "Andrea in Boston"

### Test 6: Calendar API Failure (Fail-Open, Should Send)
- **Setup:** Temporarily break calendar credential
- **Expected:** Recipe sent despite failure
- **Verification:** Recipe posted, no crash

---

## Rollback Procedure

If issues occur:

1. **Via n8n UI:**
   - Deactivate modified workflow
   - Import backup JSON: `Daily_Recipe_Delivery_backup_2026-02-07.json`
   - Activate restored workflow

2. **Via SSH (if UI inaccessible):**
   ```bash
   ssh root@192.168.1.200
   pct exec 111 -- n8n import:workflow --input=/path/to/backup.json
   ```

3. **Verification:**
   - Check workflow schedule is active
   - Manually execute to verify original flow works
   - Monitor next scheduled execution

---

## Success Criteria (From Roadmap)

- [x] Calendar check node added before Firebase read
- [ ] Skip conditions tested with actual calendar events
- [ ] No recipe sent when skip conditions are met
- [ ] Slack notification sent when recipe is skipped (stating reason)
- [ ] Ad-hoc skip mechanism (deferred to future session)

---

## Next Session Preparation

**Artifacts to capture:**
- Modified workflow JSON export
- Test results log
- Screenshots of skip notifications (optional)
- Any calendar API issues encountered

**Outstanding work:**
- Criterion 2: Shopping List Timing Fix
- Criterion 3: Recipe Repetition Tracking
- Future: Ad-hoc skip interface (Slack command or dashboard button)
