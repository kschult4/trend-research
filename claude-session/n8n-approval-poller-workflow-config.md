# n8n Approval Poller Workflow Configuration

**Workflow Name:** Approval Poller and Catalyst Trigger
**Description:** Polls Slack for approvals and triggers Catalyst deliverables
**Schedule:** Every 5 minutes
**Created:** 2026-02-02

---

## Prerequisites Checklist

- [x] Slack User ID: U09GDG5LACR
- [x] Slack Channel ID: C0ABUP7MHMM
- [x] Container 118 IP: 192.168.1.18
- [x] Approvals log created: /opt/crewai/output/approvals.jsonl
- [ ] n8n SSH credential "Container 118 SSH" exists
- [ ] Slack API token "Slack Trend Reporting Token" has required scopes

---

## Workflow Overview

```
Schedule (5 min)
  ↓
Get Today's Digest (Slack API)
  ↓
Parse Digest Response (Code)
  ↓
Check Digest Found (IF)
  ↓ (true)
Get Replies (Slack API)
  ↓
Filter User Replies (Code)
  ↓
Parse Each Approval (SSH Loop)
  ↓
Validate Opportunity Exists (SSH)
  ↓
Check for Duplicates (SSH)
  ↓
Filter New Approvals (IF)
  ↓ (new)
Log Approval (SSH)
  ↓
Trigger Catalyst (SSH)
  ↓
Parse Catalyst Output (Code)
  ↓
Check Catalyst Success (IF)
  ↓ (success)
Format Deliverable (Code)
  ↓
Post to Slack Thread (Slack API)
  ↓
Update Approval Log - Delivered (SSH)
```

---

## Node-by-Node Configuration

### Node 1: Schedule Trigger
- **Type:** Schedule Trigger
- **Name:** Every 5 Minutes
- **Configuration:**
  - Trigger Interval: Cron
  - Cron Expression: `*/5 * * * *`
  - Timezone: America/Chicago

---

### Node 2: Get Today's Digest
- **Type:** HTTP Request
- **Name:** Get Today's Digest
- **Configuration:**
  - Method: POST
  - URL: `https://slack.com/api/conversations.history`
  - Authentication: Generic Credential Type → OAuth2 API
  - Credential: "Slack Trend Reporting Token"
  - Send Body: Yes (JSON)
  - Body Parameters:
    ```json
    {
      "channel": "C0ABUP7MHMM",
      "limit": 10,
      "oldest": "{{ $now.minus(24, 'hours').toUnixInteger() }}"
    }
    ```
  - Options:
    - Response Format: JSON

---

### Node 3: Parse Digest Response
- **Type:** Code
- **Name:** Parse Digest Response
- **Configuration:**
  - Language: JavaScript
  - Code:
    ```javascript
    // Find most recent message from bot containing digest
    const messages = $input.first().json.messages || [];

    const botMessages = messages.filter(m =>
      m.text && m.text.includes('📊 *Strategic Intelligence Digest*')
    );

    if (botMessages.length === 0) {
      return [{
        json: {
          digest_found: false,
          reason: 'No digest found in last 24 hours'
        }
      }];
    }

    const digest = botMessages[0];
    const digestDate = new Date(parseFloat(digest.ts) * 1000).toISOString().split('T')[0];

    return [{
      json: {
        digest_found: true,
        digest_ts: digest.ts,
        digest_date: digestDate,
        digest_text: digest.text
      }
    }];
    ```

---

### Node 4: Check Digest Found
- **Type:** IF
- **Name:** Check Digest Found
- **Configuration:**
  - Conditions:
    - Condition 1:
      - Value 1: `{{ $json.digest_found }}`
      - Operation: Equal
      - Value 2: `true` (boolean)
  - **False Branch:** Connect to end (workflow stops)
  - **True Branch:** Continue to next node

---

### Node 5: Get Replies
- **Type:** HTTP Request
- **Name:** Get Replies
- **Configuration:**
  - Method: POST
  - URL: `https://slack.com/api/conversations.replies`
  - Authentication: Use existing credential "Slack Trend Reporting Token"
  - Send Body: Yes (JSON)
  - Body Parameters:
    ```json
    {
      "channel": "C0ABUP7MHMM",
      "ts": "={{ $json.digest_ts }}",
      "limit": 100
    }
    ```

---

### Node 6: Filter User Replies
- **Type:** Code
- **Name:** Filter User Replies
- **Configuration:**
  - Language: JavaScript
  - Code:
    ```javascript
    // Get data from previous nodes
    const replies = $input.first().json.messages || [];
    const digestData = $('Parse Digest Response').first().json;
    const kyleUserId = "U09GDG5LACR";

    // Filter for Kyle's replies (not bot, not original digest)
    const userReplies = replies.filter(r =>
      r.user === kyleUserId &&
      r.ts !== digestData.digest_ts
    );

    if (userReplies.length === 0) {
      return [{
        json: {
          has_replies: false,
          reason: 'No user replies found'
        }
      }];
    }

    // Return one item per reply for processing
    return userReplies.map(reply => ({
      json: {
        has_replies: true,
        digest_date: digestData.digest_date,
        digest_ts: digestData.digest_ts,
        reply_text: reply.text,
        reply_ts: reply.ts,
        user_id: reply.user
      }
    }));
    ```

---

### Node 7: Parse Approval Syntax
- **Type:** Execute Command (SSH)
- **Name:** Parse Approval Syntax
- **Configuration:**
  - Credential: "Container 118 SSH"
  - Command:
    ```bash
    cd /opt/crewai && python3 -c "
    from tools.approval_parser import parse_approval_syntax
    import json
    text = '''{{ $json.reply_text }}'''
    result = parse_approval_syntax(text)
    print(json.dumps(result))
    "
    ```
  - Options:
    - Working Directory: /opt/crewai

---

### Node 8: Check Valid Approval
- **Type:** IF
- **Name:** Check Valid Approval
- **Configuration:**
  - Conditions:
    - Value 1: `{{ $json.stdout }}`
    - Operation: Contains
    - Value 2: `"valid": true`
  - **False Branch:** Go to "Post Invalid Syntax Help" node
  - **True Branch:** Continue to next node

---

### Node 9: Extract Approvals
- **Type:** Code
- **Name:** Extract Approvals
- **Configuration:**
  - Language: JavaScript
  - Code:
    ```javascript
    // Parse the approval parser output
    const stdout = $json.stdout || '';
    const parsed = JSON.parse(stdout);

    // Get digest data
    const digestDate = $json.digest_date;
    const digestTs = $json.digest_ts;
    const replyTs = $json.reply_ts;
    const userId = $json.user_id;

    // Return one item per approval for parallel processing
    if (!parsed.valid || !parsed.approvals || parsed.approvals.length === 0) {
      return [];
    }

    return parsed.approvals.map(approval => ({
      json: {
        digest_date: digestDate,
        digest_ts: digestTs,
        reply_ts: replyTs,
        user_id: userId,
        opp_id: approval.opp_id,
        deliverable_type: approval.type,
        action: parsed.action
      }
    }));
    ```

---

### Node 10: Validate Opportunity Exists
- **Type:** Execute Command (SSH)
- **Name:** Validate Opportunity Exists
- **Configuration:**
  - Credential: "Container 118 SSH"
  - Command:
    ```bash
    digest_date="{{ $json.digest_date }}"
    opp_id="{{ $json.opp_id }}"

    # Check if opportunity exists in mapping
    if [ -f "/opt/crewai/output/opportunities_${digest_date}.json" ]; then
      if jq -e ".opportunities.\"${opp_id}\"" "/opt/crewai/output/opportunities_${digest_date}.json" > /dev/null 2>&1; then
        echo '{"exists": true}'
      else
        echo '{"exists": false, "error": "Opportunity '"$opp_id"' not found in digest"}'
      fi
    else
      echo '{"exists": false, "error": "No opportunities file found for '"$digest_date"'"}'
    fi
    ```

---

### Node 11: Check Opportunity Exists
- **Type:** IF
- **Name:** Check Opportunity Exists
- **Configuration:**
  - Conditions:
    - Value 1: `{{ $json.stdout }}`
    - Operation: Contains
    - Value 2: `"exists": true`
  - **False Branch:** Go to "Post Opportunity Not Found" node
  - **True Branch:** Continue to next node

---

### Node 12: Check for Duplicates
- **Type:** Execute Command (SSH)
- **Name:** Check for Duplicates
- **Configuration:**
  - Credential: "Container 118 SSH"
  - Command:
    ```bash
    digest_date="{{ $json.digest_date }}"
    opp_id="{{ $json.opp_id }}"

    # Check if already processed (look for "delivered" status)
    if grep -q "\"digest_date\": \"$digest_date\".*\"opportunity_id\": \"$opp_id\".*\"status\": \"delivered\"" /opt/crewai/output/approvals.jsonl 2>/dev/null; then
      echo '{"already_processed": true}'
    else
      echo '{"already_processed": false}'
    fi
    ```

---

### Node 13: Filter New Approvals
- **Type:** IF
- **Name:** Filter New Approvals
- **Configuration:**
  - Conditions:
    - Value 1: `{{ $json.stdout }}`
    - Operation: Contains
    - Value 2: `"already_processed": false`
  - **False Branch:** End (skip duplicate)
  - **True Branch:** Continue to next node

---

### Node 14: Log Approval
- **Type:** Execute Command (SSH)
- **Name:** Log Approval
- **Configuration:**
  - Credential: "Container 118 SSH"
  - Command:
    ```bash
    cd /opt/crewai

    timestamp=$(date -Iseconds)
    digest_date="{{ $json.digest_date }}"
    opp_id="{{ $json.opp_id }}"
    deliverable_type="{{ $json.deliverable_type }}"
    user_id="{{ $json.user_id }}"
    reply_ts="{{ $json.reply_ts }}"

    echo "{\"timestamp\": \"$timestamp\", \"digest_date\": \"$digest_date\", \"opportunity_id\": \"$opp_id\", \"deliverable_type\": \"$deliverable_type\", \"status\": \"approved\", \"slack_user\": \"$user_id\", \"slack_message_ts\": \"$reply_ts\"}" >> output/approvals.jsonl

    echo '{"logged": true}'
    ```

---

### Node 15: Trigger Catalyst
- **Type:** Execute Command (SSH)
- **Name:** Trigger Catalyst
- **Configuration:**
  - Credential: "Container 118 SSH"
  - Command:
    ```bash
    cd /opt/crewai
    source venv/bin/activate
    python3 catalyst.py --digest-date "{{ $json.digest_date }}" --opportunity "{{ $json.opp_id }}" --type "{{ $json.deliverable_type }}" 2>&1
    ```
  - Options:
    - Timeout: 300000 (5 minutes)

---

### Node 16: Parse Catalyst Output
- **Type:** Code
- **Name:** Parse Catalyst Output
- **Configuration:**
  - Language: JavaScript
  - Code:
    ```javascript
    const stdout = $json.stdout || '';

    // Extract JSON between markers
    const startMarker = '[Catalyst] === OUTPUT START ===';
    const endMarker = '[Catalyst] === OUTPUT END ===';

    const startIdx = stdout.indexOf(startMarker);
    const endIdx = stdout.indexOf(endMarker);

    if (startIdx === -1 || endIdx === -1) {
      return [{
        json: {
          success: false,
          error: 'Could not parse Catalyst output',
          raw_output: stdout.substring(0, 500)
        }
      }];
    }

    const jsonStr = stdout.substring(startIdx + startMarker.length, endIdx).trim();

    try {
      const result = JSON.parse(jsonStr);

      return [{
        json: {
          ...result,
          digest_ts: $json.digest_ts,
          digest_date: $json.digest_date,
          opp_id: $json.opp_id,
          deliverable_type: $json.deliverable_type
        }
      }];
    } catch (e) {
      return [{
        json: {
          success: false,
          error: 'Failed to parse Catalyst JSON: ' + e.message,
          raw_json: jsonStr.substring(0, 500)
        }
      }];
    }
    ```

---

### Node 17: Check Catalyst Success
- **Type:** IF
- **Name:** Check Catalyst Success
- **Configuration:**
  - Conditions:
    - Value 1: `{{ $json.success }}`
    - Operation: Equal
    - Value 2: `true` (boolean)
  - **False Branch:** Go to "Post Catalyst Error" node
  - **True Branch:** Continue to next node

---

### Node 18: Format Deliverable for Slack
- **Type:** Code
- **Name:** Format Deliverable for Slack
- **Configuration:**
  - Language: JavaScript
  - Code:
    ```javascript
    const deliverable = $json.deliverable_content || '';
    const oppTitle = $json.opportunity_title || 'Unknown';
    const oppId = $json.opp_id || '';
    const type = $json.deliverable_type || '';

    const typeEmoji = {
      'plan': '🔧',
      'brief': '📋',
      'slide': '📊'
    }[type] || '📄';

    const typeLabel = {
      'plan': 'Technical Plan',
      'brief': 'Leadership Brief',
      'slide': 'Client Slide'
    }[type] || 'Deliverable';

    const message = `${typeEmoji} *${typeLabel} for [${oppId}] ${oppTitle}*\n\n${deliverable}`;

    return [{
      json: {
        slack_message: message,
        thread_ts: $json.digest_ts,
        deliverable_file: $json.deliverable_file,
        digest_date: $json.digest_date,
        opp_id: $json.opp_id,
        deliverable_type: $json.deliverable_type
      }
    }];
    ```

---

### Node 19: Post to Slack Thread
- **Type:** HTTP Request
- **Name:** Post to Slack Thread
- **Configuration:**
  - Method: POST
  - URL: `https://slack.com/api/chat.postMessage`
  - Authentication: Use existing credential "Slack Trend Reporting Token"
  - Send Body: Yes (JSON)
  - Body Parameters:
    ```json
    {
      "channel": "C0ABUP7MHMM",
      "thread_ts": "={{ $json.thread_ts }}",
      "text": "={{ $json.slack_message }}"
    }
    ```

---

### Node 20: Update Approval Log - Delivered
- **Type:** Execute Command (SSH)
- **Name:** Update Approval Log - Delivered
- **Configuration:**
  - Credential: "Container 118 SSH"
  - Command:
    ```bash
    cd /opt/crewai

    timestamp=$(date -Iseconds)
    digest_date="{{ $json.digest_date }}"
    opp_id="{{ $json.opp_id }}"
    deliverable_type="{{ $json.deliverable_type }}"
    deliverable_file="{{ $json.deliverable_file }}"

    echo "{\"timestamp\": \"$timestamp\", \"digest_date\": \"$digest_date\", \"opportunity_id\": \"$opp_id\", \"deliverable_type\": \"$deliverable_type\", \"status\": \"delivered\", \"catalyst_file\": \"$deliverable_file\"}" >> output/approvals.jsonl

    echo '{"logged": true}'
    ```

---

## Error Handler Nodes

### Node 21: Post Invalid Syntax Help
- **Type:** HTTP Request
- **Name:** Post Invalid Syntax Help
- **Configuration:**
  - Method: POST
  - URL: `https://slack.com/api/chat.postMessage`
  - Authentication: Use existing credential "Slack Trend Reporting Token"
  - Send Body: Yes (JSON)
  - Body Parameters:
    ```json
    {
      "channel": "C0ABUP7MHMM",
      "thread_ts": "={{ $json.digest_ts }}",
      "text": "⚠️ Invalid approval syntax. Here's how to use it:\n\n*Homelab opportunities:*\n  • `approve H1` (generates Technical Plan)\n\n*Work opportunities:*\n  • `approve W1 brief` (generates Leadership Brief)\n  • `approve W2 slide` (generates Client Slide)\n\n*Multiple approvals:*\n  • `approve H1, W1 brief, W2 slide`\n\n*Dismiss:*\n  • `dismiss H1` or `dismiss W2`"
    }
    ```
  - Connect from: Node 8 (Check Valid Approval) False branch

---

### Node 22: Post Opportunity Not Found
- **Type:** Code + HTTP Request
- **Name:** Post Opportunity Not Found
- **Configuration:**
  - First, use Code node to extract error:
    ```javascript
    const stdout = $json.stdout || '';
    const parsed = JSON.parse(stdout);
    const oppId = $json.opp_id;

    return [{
      json: {
        error_message: `❌ Opportunity **${oppId}** not found in today's digest. Please check the opportunity ID and try again.`,
        digest_ts: $json.digest_ts
      }
    }];
    ```
  - Then HTTP Request to post:
    ```json
    {
      "channel": "C0ABUP7MHMM",
      "thread_ts": "={{ $json.digest_ts }}",
      "text": "={{ $json.error_message }}"
    }
    ```
  - Connect from: Node 11 (Check Opportunity Exists) False branch

---

### Node 23: Post Catalyst Error
- **Type:** Code + HTTP Request
- **Name:** Post Catalyst Error
- **Configuration:**
  - First, use Code node to format error:
    ```javascript
    const error = $json.error || 'Unknown error';
    const oppId = $json.opp_id || '';

    return [{
      json: {
        error_message: `❌ Failed to generate deliverable for **${oppId}**\n\nError: ${error}\n\nPlease try again or contact support.`,
        digest_ts: $json.digest_ts
      }
    }];
    ```
  - Then HTTP Request to post:
    ```json
    {
      "channel": "C0ABUP7MHMM",
      "thread_ts": "={{ $json.digest_ts }}",
      "text": "={{ $json.error_message }}"
    }
    ```
  - Connect from: Node 17 (Check Catalyst Success) False branch

---

## Testing Checklist

After building the workflow:

- [ ] Save workflow
- [ ] Test "Parse Digest Response" with manual execution
- [ ] Test "Filter User Replies" with mock data
- [ ] Test "Parse Approval Syntax" via SSH
- [ ] Test "Trigger Catalyst" with real opportunity
- [ ] Test full workflow end-to-end with manual approval
- [ ] Activate workflow
- [ ] Monitor first automated run

---

## Monitoring Commands

```bash
# Check approvals log
ssh root@192.168.1.18 "cat /opt/crewai/output/approvals.jsonl | jq -s '.'"

# Count approvals by status
ssh root@192.168.1.18 "cat /opt/crewai/output/approvals.jsonl | jq -r '.status' | sort | uniq -c"

# View latest deliverable
ssh root@192.168.1.18 "ls -t /opt/crewai/output/catalyst_*.json | head -1 | xargs cat | jq '.deliverable_content' -r"

# Check workflow execution history in n8n UI
# Navigate to: Executions tab
```

---

## Rollback Procedure

If workflow needs to be disabled:

1. Open n8n workflow
2. Toggle "Active" switch to OFF
3. Workflow will stop polling
4. No files are modified on container (safe to deactivate)

To fully remove:

1. Deactivate workflow
2. Delete workflow in n8n UI
3. Remove approvals.jsonl: `ssh root@192.168.1.18 "rm /opt/crewai/output/approvals.jsonl"`

---

*Configuration complete: 2026-02-02*
*Ready for n8n UI implementation*
