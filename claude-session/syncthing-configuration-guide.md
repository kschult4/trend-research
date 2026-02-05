# Syncthing Configuration Guide - CrewAI UX Pivot Phase 1

**Created:** 2026-02-03
**Session:** Session-2026-02-03-c-CrewAI-UX-Pivot-Phase-1.md

---

## Device Information

### Container 118 (crewai-strategist)
- **IP Address:** 192.168.1.18
- **Web UI:** http://192.168.1.18:8384
- **Device ID:** `MSGP2OM-EHRQ53R-HO2GBKU-4K6D2VB-VYYCF7Y-IM2FX4B-RPT5D4H-25NBTQ4`
- **Device Name:** crewai-strategist
- **Syncthing Version:** v1.30.0
- **Running as:** root

### Mac (AU-KSCHU-MBP14b)
- **Web UI:** http://127.0.0.1:8384
- **Device ID:** `3ULDMXS-CY6FEXB-B6B5QRZ-RILJ7QB-URRTNRO-YENY4V6-XPEIMIB-DLAWQQC`
- **Device Name:** AU-KSCHU-MBP14b
- **Syncthing Version:** v2.0.14
- **Running as:** kyleschultz

---

## Sync Relationship #1: Bidirectional Context

**Purpose:** Kyle writes briefs, interests, homelab docs in Obsidian; agents read from /context/

### Mac Side
- **Folder Path:** `/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/CrewAI-Context`
- **Folder Label:** CrewAI Context
- **Folder Type:** Send & Receive
- **Remote Device:** Container 118 (MSGP2OM...)

### Container 118 Side
- **Folder Path:** `/context`
- **Folder Label:** CrewAI Context (or context)
- **Folder Type:** Send & Receive
- **Remote Device:** Mac (3ULDMXS...)

**Expected Behavior:**
- Edit file in Obsidian CrewAI-Context/ → appears in /context/ within 30 seconds
- Create file in /context/ → appears in CrewAI-Context/ within 30 seconds
- Both sides can read and write

---

## Sync Relationship #2: Unidirectional Outputs

**Purpose:** Catalyst writes Technical Plans on container that automatically appear in Obsidian

### Container 118 Side (Source)
- **Folder Path:** `/opt/crewai/homelab-outputs`
- **Folder Label:** Homelab Outputs
- **Folder Type:** Send Only
- **Remote Device:** Mac (3ULDMXS...)

### Mac Side (Destination)
- **Folder Path:** `/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/_crewai-outputs`
- **Folder Label:** CrewAI Outputs
- **Folder Type:** Receive Only
- **Remote Device:** Container 118 (MSGP2OM...)

**Expected Behavior:**
- Catalyst writes to /opt/crewai/homelab-outputs/ → file appears in _crewai-outputs/ within 30 seconds
- Mac side is read-only (cannot write to _crewai-outputs/)
- Container can only write, not receive

---

## Configuration Steps

### Step 1: Pair Devices

**On Mac Syncthing UI (http://127.0.0.1:8384):**
1. Click "Actions" > "Show ID"
2. Copy Mac Device ID: `3ULDMXS-CY6FEXB-B6B5QRZ-RILJ7QB-URRTNRO-YENY4V6-XPEIMIB-DLAWQQC`
3. Click "Add Remote Device"
4. Paste Container 118 Device ID: `MSGP2OM-EHRQ53R-HO2GBKU-4K6D2VB-VYYCF7Y-IM2FX4B-RPT5D4H-25NBTQ4`
5. Device Name: "Container 118 - crewai-strategist"
6. Save

**On Container 118 Syncthing UI (http://192.168.1.18:8384):**
1. Click "Add Remote Device"
2. Paste Mac Device ID: `3ULDMXS-CY6FEXB-B6B5QRZ-RILJ7QB-URRTNRO-YENY4V6-XPEIMIB-DLAWQQC`
3. Device Name: "Mac - AU-KSCHU-MBP14b"
4. Save

### Step 2: Configure Sync #1 (Bidirectional Context)

**On Mac:**
1. Click "Add Folder"
2. Folder Label: "CrewAI Context"
3. Folder Path: `/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/CrewAI-Context`
4. Sharing tab: Check "Container 118 - crewai-strategist"
5. File Versioning: Simple File Versioning (keep 5 versions, 30 days)
6. Save

**On Container 118:**
1. When prompt appears to accept shared folder, click "Add"
2. OR manually add folder:
   - Folder Label: "CrewAI Context"
   - Folder Path: `/context`
   - Sharing tab: Check "Mac - AU-KSCHU-MBP14b"
3. Save

### Step 3: Configure Sync #2 (Unidirectional Outputs)

**On Container 118:**
1. Click "Add Folder"
2. Folder Label: "Homelab Outputs"
3. Folder Path: `/opt/crewai/homelab-outputs`
4. Folder Type: "Send Only"
5. Sharing tab: Check "Mac - AU-KSCHU-MBP14b"
6. Save

**On Mac:**
1. When prompt appears to accept shared folder, click "Add"
2. Change Folder Type to "Receive Only"
3. Folder Path: `/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/_crewai-outputs`
4. Save

---

## Existing /context/ Data to be Synced

```
/context/
├── briefs/
│   ├── phase-1-regression-test.md (55 bytes)
│   └── test-project.md (238 bytes)
├── transcripts/
│   └── 2026-02-02-curl-test-meeting.md (140 bytes)
├── homelab_architecture.md (2.1K)
├── hot_topics.md (172 bytes)
├── interest_areas.md (2.1K)
└── work_role.md (2.3K)

Total: ~7.1 KB
```

After sync is configured, these files should automatically appear in:
`/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/CrewAI-Context/`

---

## Verification Tests

### Test 1: Bidirectional Sync (Obsidian → Container)
```bash
# Create test file in Obsidian
echo "Test from Obsidian - $(date)" > "/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/CrewAI-Context/test-obsidian.md"

# Wait 30 seconds, then verify on container
ssh root@192.168.1.18 'cat /context/test-obsidian.md'
```

### Test 2: Bidirectional Sync (Container → Obsidian)
```bash
# Create test file on container
ssh root@192.168.1.18 'echo "Test from Container - $(date)" > /context/test-container.md'

# Wait 30 seconds, then verify in Obsidian
cat "/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/CrewAI-Context/test-container.md"
```

### Test 3: Unidirectional Output Sync
```bash
# Create test file in homelab-outputs on container
ssh root@192.168.1.18 'echo "# Test Technical Plan\n\nGenerated at $(date)" > /opt/crewai/homelab-outputs/test-plan.md'

# Wait 30 seconds, then verify in Obsidian
cat "/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/_crewai-outputs/test-plan.md"
```

### Test 4: Verify Receive-Only Protection
```bash
# Attempt to create file in _crewai-outputs (should fail or not sync)
echo "Should not sync" > "/Users/kyleschultz/Library/CloudStorage/OneDrive-Prophet/Desktop/Obsidian/The Good Stuff/Homelab/_crewai-outputs/should-not-appear.md"

# Verify it does NOT appear on container
ssh root@192.168.1.18 'ls /opt/crewai/homelab-outputs/should-not-appear.md'
# Expected: No such file or directory
```

---

## Troubleshooting

### Sync Not Working
1. Check Syncthing service status on both systems
   - Mac: `brew services list | grep syncthing`
   - Container: `ssh root@192.168.1.18 'systemctl status syncthing'`
2. Check Web UI for errors or "Out of Sync" warnings
3. Verify folder paths are correct
4. Check file permissions (container runs as root, Mac as kyleschultz)

### Files Not Appearing
1. Check sync progress in Web UI
2. Look for conflict files (name.sync-conflict-*)
3. Verify device is connected (green checkmark in Web UI)
4. Check Syncthing logs for errors

### Performance Issues
1. Initial sync of /context/ should be fast (~7KB)
2. Subsequent syncs should happen within 30 seconds
3. Large files may take longer depending on network

---

## Next Steps After Configuration

1. Verify all existing /context/ files appear in CrewAI-Context/
2. Run all 4 verification tests
3. Update Catalyst agent to write to /opt/crewai/homelab-outputs/ instead of posting to Slack
4. Test end-to-end: trigger Catalyst → verify .md file appears in Obsidian
5. Update session note with verification evidence
6. Mark Phase 1 complete in Roadmap

---

**Status:** Configuration guide complete. Ready for manual Web UI configuration.
