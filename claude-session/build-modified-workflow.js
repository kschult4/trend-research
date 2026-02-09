// Modified Daily Recipe Delivery Workflow with Skip Logic
// This script builds the complete modified workflow structure

const crypto = require('crypto');

// Generate unique node IDs
function generateNodeId() {
  return crypto.randomUUID();
}

// Original nodes (keeping existing IDs)
const scheduleNode = {
  parameters: {
    rule: {
      interval: [{
        field: "cronExpression",
        expression: "0 16 * * 1-5"
      }]
    }
  },
  id: "ca36ce9b-483a-44b9-8251-ffa991266ad2",
  name: "Schedule: Mon-Fri 4pm EST",
  type: "n8n-nodes-base.scheduleTrigger",
  typeVersion: 1.2,
  position: [-208, -144],
  notes: "Runs Monday-Friday at 4pm EST"
};

const getDayNode = {
  parameters: {
    jsCode: `// Get today's day of week
const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const today = new Date();
const dayName = days[today.getDay()];

return {
  dayOfWeek: dayName
};`
  },
  id: "c2a3b46e-7f6b-45d7-bbd4-20ee476dfbe2",
  name: "Get Day of Week",
  type: "n8n-nodes-base.code",
  typeVersion: 2,
  position: [-16, -144]
};

// NEW NODE 1: Get Today's Date
const getTodayDateNode = {
  parameters: {
    jsCode: `// Get today's date in various formats
const today = new Date();

// Format: YYYY-MM-DD (for holiday comparison)
const year = today.getFullYear();
const month = String(today.getMonth() + 1).padStart(2, '0');
const day = String(today.getDate()).padStart(2, '0');
const dateString = \`\${year}-\${month}-\${day}\`;

// Start and end of day for calendar query (ISO format)
const startOfDay = new Date(today);
startOfDay.setHours(0, 0, 0, 0);

const endOfDay = new Date(today);
endOfDay.setHours(23, 59, 59, 999);

return {
  dateString: dateString,
  dayOfWeek: $input.first().json.dayOfWeek,
  startOfDay: startOfDay.toISOString(),
  endOfDay: endOfDay.toISOString()
};`
  },
  id: generateNodeId(),
  name: "Get Today's Date",
  type: "n8n-nodes-base.code",
  typeVersion: 2,
  position: [184, -144],
  notes: "Generate date formats for calendar and holiday checks"
};

// NEW NODE 2: Google Calendar - Get Events
const googleCalendarNode = {
  parameters: {
    operation: "getAll",
    calendar: "andreaschultz1116@gmail.com",
    start: "={{$json.startOfDay}}",
    end: "={{$json.endOfDay}}",
    options: {
      maxResults: 50
    }
  },
  id: generateNodeId(),
  name: "Google Calendar - Check Andrea's Schedule",
  type: "n8n-nodes-base.googleCalendar",
  typeVersion: 1,
  position: [384, -240],
  notes: "Query Andrea's calendar for today's events",
  credentials: {
    googleCalendarOAuth2Api: {
      // NOTE: Will need to be configured manually or provide credential ID
      id: "GOOGLE_CALENDAR_CREDENTIAL_ID",
      name: "Andrea's Google Calendar"
    }
  }
};

// NEW NODE 3: Google Sheets - Read Holiday List
const googleSheetsNode = {
  parameters: {
    operation: "read",
    sheetId: "MEAL_PLANNING_DATA_SHEET_ID", // Will need to be provided
    range: "Holidays!A2:B50",
    options: {}
  },
  id: generateNodeId(),
  name: "Google Sheets - Read Holiday List",
  type: "n8n-nodes-base.googleSheets",
  typeVersion: 4,
  position: [384, -48],
  notes: "Fetch holiday list from Meal Planning Data sheet",
  credentials: {
    googleSheetsOAuth2Api: {
      // NOTE: May need to use existing credential from Meal Planner workflow
      id: "GOOGLE_SHEETS_CREDENTIAL_ID",
      name: "Google Sheets API"
    }
  }
};

// NEW NODE 4: Skip Logic Evaluator
const skipLogicNode = {
  parameters: {
    jsCode: `// Get inputs from calendar and holiday sheet
const calendarData = $input.all().find(item => item.json.summary !== undefined);
const holidayData = $input.all().find(item => item.json.Date !== undefined);
const dateInfo = $input.first().json;

// Extract arrays
const calendarEvents = calendarData ? [calendarData.json] : [];
const holidays = holidayData ? (Array.isArray(holidayData.json) ? holidayData.json : [holidayData.json]) : [];
const todayDate = dateInfo.dateString;

// Initialize skip state
let shouldSkip = false;
let skipReason = "";

// SKIP CONDITION 1: Check holidays
const isHoliday = holidays.some(holiday => holiday.Date === todayDate);
if (isHoliday) {
  shouldSkip = true;
  const holidayName = holidays.find(h => h.Date === todayDate).Holiday;
  skipReason = \`Holiday: \${holidayName}\`;
}

// SKIP CONDITION 2: Check calendar events (only if not already skipping)
if (!shouldSkip && calendarEvents && calendarEvents.length > 0) {
  for (const event of calendarEvents) {
    const title = event.summary || "";

    // Check for all-day events
    if (event.start && event.start.date && !event.start.dateTime) {
      shouldSkip = true;
      skipReason = \`All-day event: \${title}\`;
      break;
    }

    // Check for "Andrea out of town" pattern (case insensitive)
    if (title.toLowerCase().includes("andrea out of town")) {
      shouldSkip = true;
      skipReason = "Andrea out of town";
      break;
    }

    // Check for "Andrea in [location]" pattern
    const inLocationMatch = title.match(/andrea in ([a-zA-Z\\s]+)/i);
    if (inLocationMatch) {
      shouldSkip = true;
      skipReason = \`Andrea in \${inLocationMatch[1]}\`;
      break;
    }
  }
}

// FAIL-OPEN: If calendar check failed (no data), default to sending
if (!calendarEvents || calendarEvents.length === 0) {
  // Check if this is truly a failure or just no events
  // If we got empty array, it's fine. If we got undefined, it's a failure.
  if (calendarData === undefined) {
    // Calendar check failed - default to send (fail-open)
    shouldSkip = false;
    skipReason = "Calendar unavailable - sending recipe";
  }
}

return {
  shouldSkip: shouldSkip,
  skipReason: skipReason,
  dayOfWeek: dateInfo.dayOfWeek,
  dateString: todayDate
};`
  },
  id: generateNodeId(),
  name: "Skip Logic Evaluator",
  type: "n8n-nodes-base.code",
  typeVersion: 2,
  position: [584, -144],
  notes: "Evaluate all skip conditions and determine action"
};

// NEW NODE 5: IF Node - Route Based on Skip Decision
const ifNode = {
  parameters: {
    conditions: {
      boolean: [
        {
          value1: "={{$json.shouldSkip}}",
          value2: true
        }
      ]
    }
  },
  id: generateNodeId(),
  name: "Should Skip Recipe?",
  type: "n8n-nodes-base.if",
  typeVersion: 2,
  position: [784, -144],
  notes: "Route to skip notification or continue to meal delivery"
};

// NEW NODE 6: Format Skip Notification
const formatSkipNode = {
  parameters: {
    jsCode: `const reason = $input.first().json.skipReason;
const date = $input.first().json.dateString;

const message = \`🚫 *No recipe today* (\${date})\\n\\n*Reason:* \${reason}\\n\\nEnjoy your evening! 🌟\`;

return {
  channel: '#dinner-tonight',
  text: message
};`
  },
  id: generateNodeId(),
  name: "Format Skip Notification",
  type: "n8n-nodes-base.code",
  typeVersion: 2,
  position: [984, -240],
  notes: "Build skip notification message for Slack"
};

// NEW NODE 7: Post Skip to Slack
const postSkipNode = {
  parameters: {
    method: "POST",
    url: "https://slack.com/api/chat.postMessage",
    authentication: "genericCredentialType",
    genericAuthType: "httpHeaderAuth",
    sendHeaders: true,
    headerParameters: {
      parameters: [
        {
          name: "Content-Type",
          value: "application/json"
        }
      ]
    },
    sendBody: true,
    bodyParameters: {
      parameters: [
        {
          name: "channel",
          value: "={{$json.channel}}"
        },
        {
          name: "text",
          value: "={{$json.text}}"
        }
      ]
    },
    options: {}
  },
  id: generateNodeId(),
  name: "Post Skip to Slack",
  type: "n8n-nodes-base.httpRequest",
  typeVersion: 4.2,
  position: [1184, -240],
  credentials: {
    httpHeaderAuth: {
      id: "bZVxYcuUFrhDW3da",
      name: "Slack Bot Token"
    }
  },
  notes: "Send skip notification to #dinner-tonight channel"
};

// Existing nodes (keeping same IDs, adjusting positions)
const fetchMealNode = {
  parameters: {
    url: "=https://family-hub-dashboard-default-rtdb.firebaseio.com/meals/{{ $json.dayOfWeek }}.json",
    options: {}
  },
  id: "f2b24d49-7933-4697-8ade-f855590da857",
  name: "Fetch Today's Meal from Firebase",
  type: "n8n-nodes-base.httpRequest",
  typeVersion: 4.2,
  position: [984, -48],
  notes: "Get meal from Firebase for today"
};

const formatMealNode = {
  parameters: {
    jsCode: `// Extract meal details
const meal = $input.item.json;

if (!meal || !meal.name) {
  throw new Error('No meal found for today');
}

// Build Slack message
const message = \`🍽️ **Tonight's Dinner: \${meal.name}**\\n\` +
  \`⏱️ Prep time: \${meal.prepTime || 'Not specified'}\\n\` +
  \`📖 Recipe: \${meal.url || 'No link available'}\`;

return {
  channel: '#dinner-tonight',
  text: message
};`
  },
  id: "a395f58d-a442-4825-afeb-7bf24edf204b",
  name: "Format Slack Message",
  type: "n8n-nodes-base.code",
  typeVersion: 2,
  position: [1184, -48]
};

const postMealNode = {
  parameters: {
    method: "POST",
    url: "https://slack.com/api/chat.postMessage",
    authentication: "genericCredentialType",
    genericAuthType: "httpHeaderAuth",
    sendHeaders: true,
    headerParameters: {
      parameters: [
        {
          name: "Content-Type",
          value: "application/json"
        }
      ]
    },
    sendBody: true,
    bodyParameters: {
      parameters: [
        {
          name: "channel",
          value: "={{$json.channel}}"
        },
        {
          name: "text",
          value: "={{$json.text}}"
        }
      ]
    },
    options: {}
  },
  id: "7d9ed82b-8d36-4427-9318-262e8a09083c",
  name: "Post to Slack",
  type: "n8n-nodes-base.httpRequest",
  typeVersion: 4.2,
  position: [1384, -48],
  credentials: {
    httpQueryAuth: {
      id: "jOtWdsKTauV30mbJ",
      name: "Firebase Database Secret"
    },
    httpHeaderAuth: {
      id: "bZVxYcuUFrhDW3da",
      name: "Slack Bot Token"
    }
  },
  notes: "Send meal to #dinner-tonight channel"
};

// Build complete node array
const nodes = [
  scheduleNode,
  getDayNode,
  getTodayDateNode,
  googleCalendarNode,
  googleSheetsNode,
  skipLogicNode,
  ifNode,
  formatSkipNode,
  postSkipNode,
  fetchMealNode,
  formatMealNode,
  postMealNode
];

// Build connections
const connections = {
  "Schedule: Mon-Fri 4pm EST": {
    main: [[{ node: "Get Day of Week", type: "main", index: 0 }]]
  },
  "Get Day of Week": {
    main: [[{ node: "Get Today's Date", type: "main", index: 0 }]]
  },
  "Get Today's Date": {
    main: [
      [
        { node: "Google Calendar - Check Andrea's Schedule", type: "main", index: 0 },
        { node: "Google Sheets - Read Holiday List", type: "main", index: 0 }
      ]
    ]
  },
  "Google Calendar - Check Andrea's Schedule": {
    main: [[{ node: "Skip Logic Evaluator", type: "main", index: 0 }]]
  },
  "Google Sheets - Read Holiday List": {
    main: [[{ node: "Skip Logic Evaluator", type: "main", index: 0 }]]
  },
  "Skip Logic Evaluator": {
    main: [[{ node: "Should Skip Recipe?", type: "main", index: 0 }]]
  },
  "Should Skip Recipe?": {
    main: [
      [{ node: "Format Skip Notification", type: "main", index: 0 }], // True branch
      [{ node: "Fetch Today's Meal from Firebase", type: "main", index: 0 }] // False branch
    ]
  },
  "Format Skip Notification": {
    main: [[{ node: "Post Skip to Slack", type: "main", index: 0 }]]
  },
  "Fetch Today's Meal from Firebase": {
    main: [[{ node: "Format Slack Message", type: "main", index: 0 }]]
  },
  "Format Slack Message": {
    main: [[{ node: "Post to Slack", type: "main", index: 0 }]]
  }
};

// Build complete workflow
const modifiedWorkflow = {
  name: "Daily Recipe Delivery",
  nodes: nodes,
  connections: connections,
  active: true,
  settings: {
    executionOrder: "v1"
  },
  staticData: {
    "node:Schedule: Mon-Fri 4pm EST": {
      recurrenceRules: []
    }
  }
};

console.log(JSON.stringify(modifiedWorkflow, null, 2));
