# Session 2026-02-04: Syncthing Output Sync Fix

## Problem Summary

Unidirectional sync from Container 118 to Mac was not working:
- Container `/opt/crewai/homelab-outputs/` → Mac `_crewai-outputs/` configured but not syncing
- Test file on Container was not appearing in Obsidian
- Mac Syncthing UI showed misleading file count

## Root Cause

**Container 118 Syncthing folder configuration was missing the Mac device in its sharing list.**

The folder `qiukt-rurae` was configured as "sendonly" on Container 118, but only had the Container's own device ID in the devices list. The Mac device (3ULDMXS-CY6FEXB-B6B5QRZ-RILJ7QB-URRTNRO-YENY4V6-XPEIMIB-DLAWQQC) was not included.

This meant:
- Container had the files but wasn't sharing them with anyone
- Mac was configured to receive but wasn't being offered anything
- Devices were paired and connected, but folder wasn't shared

## Diagnostic Process

### 1. Checked Container 118 folder status
```bash
ssh root@192.168.1.18 'curl -s -H "X-API-Key: ..." http://127.0.0.1:8384/rest/db/status?folder=qiukt-rurae'
```

Result: Container showed 1 file, 827 bytes, everything healthy

### 2. Checked Mac folder status
```bash
curl -s -H "X-API-Key: ..." 'http://127.0.0.1:8384/rest/db/status?folder=qiukt-rurae'
```

Result: Mac showed **globalFiles: 0**, indicating no awareness of Container's files

### 3. Compared folder configurations

**Mac config:**
- Devices: [Container, Mac] ✅
- Type: receiveonly ✅

**Container config:**
- Devices: [Container only] ❌ **PROBLEM**
- Type: sendonly ✅

### 4. Verified device connection
```bash
curl -s -H "X-API-Key: ..." http://127.0.0.1:8384/rest/system/connections
```

Result: Devices connected and communicating via TLS1.3

## Solution

Added Mac device to Container's folder sharing configuration via Syncthing REST API:

```bash
# 1. Get current folder config
API_KEY=$(cat /root/.local/state/syncthing/config.xml | grep -oP "(?<=<apikey>)[^<]+")
curl -s -H "X-API-Key: $API_KEY" \
  http://127.0.0.1:8384/rest/config/folders/qiukt-rurae > folder.json

# 2. Add Mac device to devices list
# Modified JSON to include:
{
  "deviceID": "3ULDMXS-CY6FEXB-B6B5QRZ-RILJ7QB-URRTNRO-YENY4V6-XPEIMIB-DLAWQQC",
  "introducedBy": "",
  "encryptionPassword": ""
}

# 3. Update configuration
curl -s -X PUT -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d @updated_folder.json \
  http://127.0.0.1:8384/rest/config/folders/qiukt-rurae
```

## Result

Syncthing immediately detected the configuration change and:
1. Restarted the folder sync relationship
2. Scanned the folder
3. Synchronized all files to Mac
4. Established ongoing sync monitoring

**Logs (Container 118, 21:19:37 UTC):**
```
INFO: Ready to synchronize "Homelab Outputs" (qiukt-rurae) (sendonly)
INFO: Device 3ULDMXS folder "Homelab Outputs" (qiukt-rurae) has a new index ID
INFO: Restarted folder "Homelab Outputs" (qiukt-rurae) (sendonly)
INFO: Completed initial scan of sendonly folder "Homelab Outputs" (qiukt-rurae)
```

## Verification

### Test 1: Existing file sync
- File: `test-technical-plan.md` (827 bytes)
- Result: Appeared on Mac within 10 seconds
- Content: Verified byte-for-byte match

### Test 2: New file sync (real-time)
- Created: `verification-test-20260204-162029.md` (743 bytes)
- Result: Appeared on Mac within 15 seconds
- Content: Verified byte-for-byte match

### Test 3: API status after fix
```json
{
  "globalFiles": 2,
  "globalBytes": 1570,
  "localFiles": 2,
  "inSyncFiles": 2,
  "state": "idle",
  "remoteSequence": {
    "MSGP2OM-EHRQ53R-HO2GBKU-4K6D2VB-VYYCF7Y-IM2FX4B-RPT5D4H-25NBTQ4": 2
  }
}
```

Mac now has full global state awareness and ongoing sync.

## Key Learnings

1. **Syncthing folder sharing is explicit per folder, not automatic per device**
   - Pairing devices does NOT automatically share all folders
   - Each folder requires explicit device list configuration

2. **REST API is superior to Web UI for diagnostics**
   - Web UI showed misleading "9 files" count
   - API revealed exact global/local state discrepancy
   - API enables programmatic troubleshooting

3. **Configuration changes via API apply immediately**
   - No service restart required
   - Syncthing detects config changes and adapts
   - Folder sync restarts automatically

4. **Bidirectional sync worked because it was configured correctly initially**
   - Context folder had both devices in sharing list from the start
   - Outputs folder was misconfigured during manual setup

## Files Affected

**Container 118:**
- `/opt/crewai/homelab-outputs/test-technical-plan.md` (827 bytes)
- `/opt/crewai/homelab-outputs/verification-test-20260204-162029.md` (743 bytes)

**Mac (Obsidian):**
- `_crewai-outputs/test-technical-plan.md` (827 bytes, synced)
- `_crewai-outputs/verification-test-20260204-162029.md` (743 bytes, synced)

## Phase 1 Complete

Both sync relationships now operational:
1. Bidirectional: Obsidian `CrewAI-Context/` ↔ Container `/context/` ✅
2. Unidirectional: Container `/opt/crewai/homelab-outputs/` → Obsidian `_crewai-outputs/` ✅

Ready to proceed to Phase 2 (Slack message refactor).
