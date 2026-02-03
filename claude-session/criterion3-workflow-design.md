# Criterion 3: Context Management Workflow Design

## Overview

Design for n8n workflow that bridges Slack `#trend-monitoring` channel to filesystem on container 118, enabling Kyle to manage project briefs, transcripts, and hot topics via Slack messages.

---

## Workflow Architecture

### High-Level Flow

```
Slack Message (#trend-monitoring)
    ↓
n8n Webhook Trigger (listens for new messages)
    ↓
Message Parser (extract command + content)
    ↓
Router (switch based on command type)
    ↓
    ├─→ "New project:" → Create Brief Handler
    ├─→ "Update [name]:" → Update Brief Handler
    ├─→ "Hot topic:" → Append Hot Topic Handler
    ├─→ "Transcript:" → Create Transcript Handler
    └─→ Unknown command → Error Handler
    ↓
SSH Execute Node (write to container 118)
    ↓
Confirmation Reply (post to Slack thread)
```

---

## Message Parsing Patterns

### Command Detection (Regex)

| Command | Regex Pattern | Capture Groups |
|---------|---------------|----------------|
| New project | `^New project:\s*(.+)$` | Group 1: Project name |
| Update brief | `^Update\s+(.+?):\s*(.+)$` | Group 1: Project name, Group 2: Changes |
| Hot topic | `^Hot topic:\s*(.+)$` | Group 1: Description |
| Transcript | `^Transcript:\s*(.+)$` | Group 1: Meeting name |

### Content Extraction

**For "New project:"**
- Line 1: Command with project name
- Lines 2+: Full brief content (user provides formatted markdown)
- OR: Use template if minimal content provided

**For "Hot topic:"**
- Single line: `Hot topic: [description]`
- Multi-line: Lines after command are full description

**For "Transcript:"**
- If message has attachment: Download file content
- If text only: Lines after command are transcript

**For "Update [name]:"**
- Find existing brief file
- Apply changes (simple append to end, or field-specific update)

---

## Filesystem Operations

### 1. Create Project Brief

**Operation:** Create new file
**Path:** `/context/briefs/[sanitized-name].md`
**Method:** SSH Execute or Write File node

**File Naming:**
- Convert project name to lowercase
- Replace spaces with hyphens
- Remove special characters (keep alphanumeric and hyphens)
- Example: "New project: AI Content Strategy" → `ai-content-strategy.md`

**Content:**
- If user provides full content: Use as-is
- If minimal content: Use template with project name filled in

**Template:**
```markdown
# Project: {{project_name}}

**Status:** Active
**Last Updated:** {{current_date}}

## Summary
{{user_content or "TODO: Add summary"}}

## My Role
TODO: Define role

## Key Stakeholders
TODO: List stakeholders

## Current Phase
TODO: Describe current phase

## Open Questions / Blockers
TODO: List questions

## Leadership Visibility
TODO: Describe visibility
```

**SSH Command:**
```bash
cat > /context/briefs/{{filename}}.md << 'EOF'
{{content}}
EOF
```

---

### 2. Update Project Brief

**Operation:** Append or modify existing file
**Path:** `/context/briefs/[name].md`

**Strategy (Simple - Append Mode):**
- Append update as new section at end of file
- Include timestamp
- User can manually clean up later if needed

**SSH Command:**
```bash
cat >> /context/briefs/{{filename}}.md << 'EOF'

---
**Update:** {{current_timestamp}}

{{update_content}}
EOF
```

**Future Enhancement (Smart Update):**
- Parse existing file
- Identify section to update
- Replace section content
- (Defer to later iteration)

---

### 3. Append Hot Topic

**Operation:** Append to shared file
**Path:** `/context/hot_topics.md`

**Format:**
```markdown
- **{{current_date}}:** {{description}}
```

**SSH Command:**
```bash
echo "- **$(date +%Y-%m-%d):** {{description}}" >> /context/hot_topics.md
```

**Initialization (if file is empty):**
```bash
if [ ! -s /context/hot_topics.md ]; then
  echo "# Hot Topics" > /context/hot_topics.md
  echo "" >> /context/hot_topics.md
  echo "Leadership concerns, themes, and priorities." >> /context/hot_topics.md
  echo "" >> /context/hot_topics.md
fi
echo "- **$(date +%Y-%m-%d):** {{description}}" >> /context/hot_topics.md
```

---

### 4. Create Transcript

**Operation:** Create new file
**Path:** `/context/transcripts/[date]-[meeting].md`

**File Naming:**
- Format: `YYYY-MM-DD-[sanitized-meeting-name].md`
- Example: "Transcript: Q1 Planning" → `2026-02-01-q1-planning.md`

**Content:**
- If file attachment: Download and save content
- If text: Use message body

**SSH Command:**
```bash
cat > /context/transcripts/{{filename}}.md << 'EOF'
# Transcript: {{meeting_name}}
**Date:** {{current_date}}

{{transcript_content}}
EOF
```

---

## Error Handling

### File Already Exists (Create operations)

**Check before create:**
```bash
if [ -f /context/briefs/{{filename}}.md ]; then
  echo "ERROR: File already exists. Use 'Update {{name}}:' instead."
  exit 1
fi
```

**n8n Response:** Post error message to Slack thread

### File Not Found (Update operations)

**Check before update:**
```bash
if [ ! -f /context/briefs/{{filename}}.md ]; then
  echo "ERROR: Brief '{{name}}' not found. Available briefs:"
  ls /context/briefs/
  exit 1
fi
```

**n8n Response:** Post error with list of available briefs

### Invalid Command Format

**n8n Router:** If no pattern matches, route to error handler

**Response:**
```
❌ Command not recognized. Valid formats:
• New project: [name]
• Update [name]: [changes]
• Hot topic: [description]
• Transcript: [meeting]
```

### SSH Connection Failure

**n8n Error Node:** Catch SSH errors

**Response:**
```
⚠️ Failed to write to container 118. Please check system status.
```

---

## Confirmation Messages

### Successful Operations

**New Project:**
```
✅ Created brief: /context/briefs/{{filename}}.md
```

**Update Brief:**
```
✅ Updated brief: /context/briefs/{{filename}}.md
```

**Hot Topic:**
```
✅ Added hot topic to /context/hot_topics.md
```

**Transcript:**
```
✅ Saved transcript: /context/transcripts/{{filename}}.md
```

---

## n8n Node Structure

### Recommended Nodes

1. **Slack Trigger** (Webhook or App Event Subscription)
   - Event: `message.channels`
   - Filter: Channel = `#trend-monitoring`
   - Filter: Not from bot

2. **Function Node: Parse Message**
   - Extract command type
   - Extract parameters (name, content)
   - Sanitize filenames
   - Set variables for downstream nodes

3. **Switch Node: Route by Command**
   - Branch 1: "New project:" → Create Brief Flow
   - Branch 2: "Update [name]:" → Update Brief Flow
   - Branch 3: "Hot topic:" → Hot Topic Flow
   - Branch 4: "Transcript:" → Transcript Flow
   - Default: Error Handler

4. **SSH Node: Execute on Container 118**
   - Host: 192.168.1.18
   - User: root
   - Auth: SSH key (already configured from n8n)
   - Command: Dynamic based on operation type

5. **Slack Node: Post Reply**
   - Method: Post message to thread
   - Content: Confirmation or error message

---

## Security Considerations

### Input Sanitization

**Critical:** Sanitize all user input before constructing shell commands

**Sanitization Rules:**
- File names: Only alphanumeric, hyphens, underscores
- Content: Use heredoc (`<< 'EOF'`) to prevent command injection
- No shell metacharacters in filenames

**Example Sanitization (JavaScript in Function Node):**
```javascript
function sanitizeFilename(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')  // Remove special chars
    .replace(/\s+/g, '-')           // Spaces to hyphens
    .replace(/-+/g, '-')            // Collapse multiple hyphens
    .trim();
}
```

### File Permissions

**Ensure files are readable by crewai user:**
- Set appropriate permissions on created files
- Files should be owned by root with 644 permissions
- Directories should be 755

**SSH Command Addition:**
```bash
chmod 644 /context/briefs/{{filename}}.md
```

---

## Testing Strategy

### Test Cases

1. **Create new brief (simple)**
   - Input: `New project: Test Project`
   - Expected: `/context/briefs/test-project.md` created with template

2. **Create new brief (with content)**
   - Input: Multi-line message with formatted markdown
   - Expected: File created with exact content

3. **Create duplicate brief (error)**
   - Input: `New project: Test Project` (already exists)
   - Expected: Error message, no file overwrite

4. **Add hot topic**
   - Input: `Hot topic: Focus on Q2 planning`
   - Expected: Line appended to `/context/hot_topics.md`

5. **Update existing brief**
   - Input: `Update Test Project: Added new stakeholder`
   - Expected: Update appended to existing file

6. **Update non-existent brief (error)**
   - Input: `Update NonExistent: ...`
   - Expected: Error message with list of available briefs

7. **Create transcript**
   - Input: `Transcript: Weekly Standup`
   - Expected: `/context/transcripts/2026-02-01-weekly-standup.md` created

8. **Invalid command**
   - Input: `Random message`
   - Expected: Error with valid command formats

### Validation

**After each operation:**
1. SSH to container 118
2. Verify file exists with `ls -la /context/briefs/`
3. Check file content with `cat /context/briefs/[file]`
4. Verify permissions with `ls -l`

---

## Implementation Priority

### Phase 1 (MVP - This Session)
1. ✅ "Hot topic:" handler (simplest - append only)
2. ✅ "New project:" handler (create with template)
3. ✅ Error handling for unknown commands

### Phase 2 (Next Session)
4. "Transcript:" handler (file creation)
5. "Update [name]:" handler (append mode)
6. File existence checks and better error messages

### Phase 3 (Future)
7. File upload support for transcripts
8. Smart update (section-specific modifications)
9. Recall query functionality (search context files)

---

## Expected Outcomes for Criterion 3

**Primary Outcome (from Roadmap):**
n8n workflow bridges Slack `#trend-monitoring` channel to filesystem. Kyle can add/update project briefs, transcripts, and hot topics via Slack messages.

**Evidence Required:**
- ✅ Message "New project: Test Project" creates `/context/briefs/test-project.md`
- ✅ Message "Hot topic: Testing" appends to `/context/hot_topics.md`
- ✅ File upload with "Transcript: Test Meeting" saves to `/context/transcripts/`
- ⚠️ Recall query (deferred to later)

**This Session Goal:**
- At minimum: Hot topic + New project handlers working
- Stretch: Transcript handler if time permits

---

**Design Status:** COMPLETE
**Next Step:** Implement in n8n web UI (Task 3)
