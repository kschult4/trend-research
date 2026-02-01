# CrewAI Strategic Intelligence Crew - Setup Documentation

**Date:** 2026-01-31
**Status:** Criterion 1 Complete
**Reproducibility:** Fully documented

---

## Prerequisites

- Access to Proxmox host at 192.168.1.200
- SSH key authentication configured
- Debian 12 template available: `debian-12-standard_12.12-1_amd64.tar.zst`
- Available IP address: 192.168.1.18 (static)
- Available container ID: 118

---

## Step-by-Step Setup

### Step 1: Create LXC Container

```bash
# SSH to Proxmox host
ssh root@192.168.1.200

# Create container 118
pct create 118 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname crewai-strategist \
  --memory 2048 \
  --cores 2 \
  --storage local-lvm \
  --rootfs 20 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.18/24,gw=192.168.1.1 \
  --nameserver 192.168.1.13 \
  --ssh-public-keys /root/.ssh/authorized_keys \
  --unprivileged 1 \
  --features nesting=1

# Start container
pct start 118

# Verify container is running
pct list | grep 118
# Expected output: "118        running                 crewai-strategist"
```

**Configuration Details:**
- Hostname: `crewai-strategist`
- Memory: 2048 MB (2 GB)
- CPU Cores: 2
- Storage: 20 GB on local-lvm
- Network: Static IP 192.168.1.18/24
- Gateway: 192.168.1.1
- DNS: 192.168.1.13 (PiHole)
- SSH: Public key authentication from Proxmox host
- Type: Unprivileged container
- Features: Nesting enabled (for potential Docker use)

---

### Step 2: Verify Network and SSH Access

```bash
# Wait for container to fully initialize (5 seconds)
sleep 5

# Test SSH access
ssh root@192.168.1.18 "hostname && cat /etc/debian_version"
# Expected output:
# crewai-strategist
# 12.12
```

---

### Step 3: Install Python and Dependencies

```bash
# SSH to container
ssh root@192.168.1.18

# Update package manager
apt update

# Install Python 3, pip, and venv
apt install -y python3 python3-pip python3-venv

# Verify Python version
python3 --version
# Expected: Python 3.11.2

# Verify pip version
pip3 --version
# Expected: pip 23.0.1 from /usr/lib/python3/dist-packages/pip (python 3.11)
```

**Note:** Debian 12 uses PEP 668 externally-managed Python environments, which prevents system-wide pip installations. This is why we install `python3-venv` and will create a virtual environment in the next step.

---

### Step 4: Create Python Virtual Environment

```bash
# Create directory for CrewAI
mkdir -p /opt/crewai

# Navigate to directory
cd /opt/crewai

# Create virtual environment
python3 -m venv venv

# Verify venv created
ls -la
# Expected: venv/ directory exists
```

**Rationale:** Virtual environment approach:
- Complies with Debian 12 PEP 668 policy
- Isolates CrewAI dependencies from system Python
- Allows version control without breaking system packages
- Easy to destroy and recreate if needed

---

### Step 5: Install CrewAI

```bash
# Activate virtual environment
cd /opt/crewai
source venv/bin/activate

# Upgrade pip within venv
pip install --upgrade pip

# Install CrewAI and tools
pip install crewai crewai-tools

# Verify installation
pip show crewai
# Expected output includes:
# Name: crewai
# Version: 1.9.3
# Location: /opt/crewai/venv/lib/python3.11/site-packages

pip show crewai-tools
# Expected output includes:
# Name: crewai-tools
# Version: 1.9.3

# Deactivate venv
deactivate
```

**Installed Versions:**
- pip: 26.0
- crewai: 1.9.3
- crewai-tools: 1.9.3

---

### Step 6: Create Context Directory Structure

```bash
# Create context directories and files
mkdir -p /context/briefs
mkdir -p /context/transcripts
touch /context/hot_topics.md
touch /context/homelab_architecture.md
touch /context/interest_areas.md
touch /context/work_role.md

# Verify structure
ls -la /context/
# Expected output:
# briefs/
# transcripts/
# homelab_architecture.md
# hot_topics.md
# interest_areas.md
# work_role.md
```

**Directory Purpose:**
- `/context/briefs/` - Work project briefs
- `/context/transcripts/` - Meeting transcripts
- `/context/hot_topics.md` - Leadership concerns and themes
- `/context/homelab_architecture.md` - Current homelab state
- `/context/interest_areas.md` - Topics for Scout to monitor
- `/context/work_role.md` - Kyle's role and boundaries

---

## Verification Checklist

After setup, verify all evidence criteria:

- [ ] Container 118 shows as "running" in `pct list`
- [ ] SSH connection to 192.168.1.18 succeeds
- [ ] `python3 --version` returns 3.11+
- [ ] `pip show crewai` shows package installed in venv
- [ ] `/context/` directory contains all expected subdirectories and files

### Full Verification Commands

```bash
# 1. Container running
ssh root@192.168.1.200 "pct list | grep 118"

# 2. SSH access
ssh root@192.168.1.18 "echo 'SSH OK'"

# 3. Python version
ssh root@192.168.1.18 "python3 --version"

# 4. CrewAI installed
ssh root@192.168.1.18 "cd /opt/crewai && source venv/bin/activate && pip show crewai && deactivate"

# 5. Context structure
ssh root@192.168.1.18 "ls /context/"
```

---

## Troubleshooting

### Issue: Container won't start

```bash
# Check container status
pct status 118

# Check container logs
pct logs 118

# Force stop and restart
pct stop 118
pct start 118
```

### Issue: SSH connection refused

```bash
# Wait longer for container initialization
sleep 10
ssh root@192.168.1.18

# Check container is running
pct status 118

# Check network config inside container
pct enter 118
ip addr show
exit
```

### Issue: pip installation fails with "externally-managed-environment"

**Cause:** Attempting to install packages system-wide on Debian 12

**Solution:** Always use virtual environment:
```bash
cd /opt/crewai
source venv/bin/activate
pip install <package>
deactivate
```

### Issue: CrewAI import errors

```bash
# Ensure venv is activated
cd /opt/crewai
source venv/bin/activate

# Reinstall CrewAI
pip uninstall crewai crewai-tools
pip install crewai crewai-tools

# Verify
python3 -c "import crewai; print(crewai.__version__)"
```

---

## Reproducibility Notes

This setup can be fully reproduced by:

1. Running all commands in sequence from Step 1-6
2. No manual configuration steps were omitted
3. All decisions documented in session notes
4. Container can be destroyed and recreated without data loss

**Destruction Command:**
```bash
ssh root@192.168.1.200 "pct stop 118 && pct destroy 118"
```

**Recreation:** Follow Step 1-6 again

---

## Next Steps

After Criterion 1 completion:

1. Add container 118 to Uptime Kuma monitoring
2. Update `homelab_system_overview.md` with container details
3. Begin Criterion 2: Minimal Viable Crew (Scout + Analyst)
4. Configure API credentials (Anthropic)
5. Implement first crew.py script

---

## References

- Container ID allocation: 118 (next available after 117)
- IP allocation: 192.168.1.18 (next available in static range)
- Memory allocation: 2048 MB (based on multi-agent workload estimate)
- Storage allocation: 20 GB (sufficient for code, context, logs)

---

*Setup documentation created: 2026-01-31*
*Reproducibility verified: 2026-01-31*
