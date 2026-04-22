# Jenkins Monitor - Usage Examples

## Quick Reference

```bash
# Set credentials once
export JENKINS_USER="your_username"
export JENKINS_TOKEN="your_api_token"
```

## Basic Usage

### Show All Builds (No Filtering)

```bash
# Last 10 builds, any parameters
python jenkins_monitor.py

# Last 20 builds, any parameters
python jenkins_monitor.py --limit 20

# All builds
python jenkins_monitor.py --limit 0
```

### Filter by Single Parameter

```bash
# Only builds with PROVISION_INFRA=true
python jenkins_monitor.py -f PROVISION_INFRA=true

# Only builds with specific environment
python jenkins_monitor.py -f TEST_ENVIRONMENT=AWS

# Only builds with specific cluster type
python jenkins_monitor.py -f CLUSTER_TYPE=selfmanaged
```

### Filter by Multiple Parameters

```bash
# Builds with PROVISION_INFRA=true AND TEST_ENVIRONMENT=AWS
python jenkins_monitor.py -f PROVISION_INFRA=true -f TEST_ENVIRONMENT=AWS

# Three filters
python jenkins_monitor.py \
  -f PROVISION_INFRA=true \
  -f TEST_ENVIRONMENT=AZURE \
  -f CLUSTER_TYPE=selfmanaged
```

## Watch Mode Examples

### Watch All Builds

```bash
# Watch mode showing all builds (refresh every 30 seconds)
python jenkins_monitor.py --watch

# Custom refresh interval (60 seconds)
python jenkins_monitor.py --watch --interval 60

# Watch last 20 builds
python jenkins_monitor.py --watch --limit 20
```

### Watch Filtered Builds

```bash
# Watch only builds with PROVISION_INFRA=true
python jenkins_monitor.py --watch -f PROVISION_INFRA=true

# Watch filtered builds with custom interval
python jenkins_monitor.py --watch --interval 15 -f PROVISION_INFRA=true

# Watch multiple filters
python jenkins_monitor.py --watch \
  -f PROVISION_INFRA=true \
  -f TEST_ENVIRONMENT=AWS \
  --limit 30
```

## Running vs Finished Builds

The script shows **ALL** build states including:
- ✅ **SUCCESS** - Build completed successfully
- ❌ **FAILURE** - Build failed
- ⚠️ **UNSTABLE** - Build has test failures
- 🔵 **RUNNING** - Build is currently in progress
- ⏸️ **ABORTED** - Build was cancelled

### Example: Monitor Running Builds

```bash
# Watch mode is great for seeing builds in progress
python jenkins_monitor.py --watch --interval 10
```

You'll see builds transition from:
- `RUNNING` (blue, duration shows "N/A")
- → `SUCCESS` (green) or `FAILURE` (red)

## Advanced Examples

### Different Jenkins Server/Job

```bash
# Override defaults
python jenkins_monitor.py \
  --url https://jenkins.example.com \
  --job team/project/pipeline \
  --user myuser \
  --token mytoken
```

### Self-Signed SSL Certificates

```bash
# Disable SSL verification
python jenkins_monitor.py --no-verify-ssl
```

### File Output Control

```bash
# Don't save files (one-time mode only)
python jenkins_monitor.py --no-save

# Custom filenames
python jenkins_monitor.py \
  --json-file my_report.json \
  --csv-file my_report.csv
```

### Complex Filtering

```bash
# Find all failed builds with PROVISION_INFRA=true
python jenkins_monitor.py \
  -f PROVISION_INFRA=true \
  --limit 50 \
  | grep FAILURE

# Watch only production environment builds
python jenkins_monitor.py --watch \
  -f TEST_ENVIRONMENT=production \
  -f PROVISION_INFRA=true
```

## Practical Scenarios

### Scenario 1: Daily Report of Infrastructure Provisioning

```bash
# Get all builds from today that provisioned infrastructure
python jenkins_monitor.py \
  -f PROVISION_INFRA=true \
  --limit 50 \
  --json-file daily_provisions.json
```

### Scenario 2: Monitor Active Deployments

```bash
# Watch running and recent builds (refreshes every 10 seconds)
python jenkins_monitor.py --watch --interval 10 --limit 15
```

### Scenario 3: Debug Failures in Specific Environment

```bash
# One-time report of Azure builds
python jenkins_monitor.py \
  -f TEST_ENVIRONMENT=AZURE \
  -f PROVISION_INFRA=true \
  --limit 30
```

### Scenario 4: Track All Pipeline Activity

```bash
# Watch all builds (no filters) with fast refresh
python jenkins_monitor.py --watch --interval 5 --limit 25
```

### Scenario 5: Export Data for Analysis

```bash
# Get comprehensive dataset
python jenkins_monitor.py \
  --limit 100 \
  --csv-file weekly_report.csv \
  --json-file weekly_report.json
```

## Tips

### 💡 When to Use Filters

- **Use filters** when you want specific builds (e.g., only infrastructure provisioning)
- **No filters** when you want to see all pipeline activity
- **Multiple filters** act as AND conditions (all must match)

### 💡 When to Use Watch Mode

- During active development/deployment
- When monitoring CI/CD pipeline
- To catch builds as they complete
- Real-time failure detection

### 💡 When to Use One-Time Mode

- Generating reports
- Exporting data for analysis
- Quick status check
- Scripting/automation

### 💡 Refresh Intervals

- **5-10 seconds**: Very active monitoring
- **30 seconds**: Default, good balance
- **60+ seconds**: Light monitoring

### 💡 Build Limits

- **10 builds**: Quick overview (default)
- **20-50 builds**: Recent history
- **100+ builds**: Comprehensive analysis
- **0 (all)**: Full history (may be slow)

## Environment Variables

```bash
# Set once in your shell profile (~/.bashrc, ~/.zshrc)
export JENKINS_USER="your_username"
export JENKINS_TOKEN="your_api_token"
export JENKINS_URL="https://jenkins.example.com"
export JENKINS_JOB="team/project/pipeline"

# Then simply run
python jenkins_monitor.py
python jenkins_monitor.py --watch
python jenkins_monitor.py -f PROVISION_INFRA=true
```

## Keyboard Shortcuts

- **Ctrl+C**: Exit watch mode or cancel one-time report
- **Ctrl+Z**: Pause (can resume with `fg`)

## Common Issues

### No Builds Match Filters

```bash
# Check what filters are active
python jenkins_monitor.py -f PROVISION_INFRA=true --limit 5

# Remove filters to see all builds
python jenkins_monitor.py --limit 5
```

### Build Still Running

Running builds show:
- Status: `RUNNING` (blue)
- Duration: `N/A`
- Automatically updates in watch mode when completed

### Too Many Builds

```bash
# Reduce limit for faster results
python jenkins_monitor.py --limit 10
```
