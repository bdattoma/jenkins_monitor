# Jenkins Build Monitor

A unified CLI tool to monitor Jenkins job builds. Supports both one-time reports and continuous watch mode with optional parameter filtering.

## Features

✨ **Two Modes**:
- **One-time mode**: Generate detailed reports with JSON/CSV export
- **Watch mode**: Continuous monitoring with auto-refresh and visual status indicators

🔍 **Flexible Filtering**:
- Show all builds (default)
- Filter by any parameter (e.g., `PROVISION_INFRA=true`, `ENV=prod`)
- Multiple filters supported (AND logic)
- Includes **running/in-progress** builds, not just finished ones

🎨 **Color-coded output**:
- 🔴 RED = FAILURE
- 🟢 GREEN = SUCCESS  
- 🟡 YELLOW = UNSTABLE
- 🔵 BLUE = RUNNING (in progress)
- 🟣 PURPLE = ABORTED

📊 **Comprehensive reporting**:
- Test environment and cluster type
- Failed pipeline stages (auto-detected)
- Build duration and timestamps
- Direct links to Jenkins builds
- Real-time status for running builds

🎬 **Visual Status Indicators** (Watch Mode):
- ↓ **Down arrow** while fetching data
- ✓ **Green checkmark** on successful refresh
- ✗ **Red X** on errors with details
- ↻ **Live countdown** timer between refreshes

## 📚 Documentation

- **[Usage Examples](docs/USAGE_EXAMPLES.md)** - Practical scenarios and common use cases
- **[Watch Mode Guide](docs/WATCH_MODE_GUIDE.md)** - Visual indicators and watch mode details
- **[Changelog](CHANGELOG.md)** - Version history and migration guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or install directly
pip install python-jenkins click
```

## Quick Start

### Setup Credentials

```bash
export JENKINS_USER="your_username"
export JENKINS_TOKEN="your_api_token"
```

Get your API token: Jenkins → User → Configure → API Token

### One-Time Report

```bash
# Default: last 10 builds (all parameters)
python jenkins_monitor.py

# Filter by parameter
python jenkins_monitor.py -f PROVISION_INFRA=true

# Multiple filters (AND logic)
python jenkins_monitor.py -f PROVISION_INFRA=true -f TEST_ENVIRONMENT=AWS

# Check last 20 builds
python jenkins_monitor.py --limit 20

# Check all builds
python jenkins_monitor.py --limit 0

# Save to custom files
python jenkins_monitor.py --json-file my_report.json --csv-file my_report.csv

# Don't save files
python jenkins_monitor.py --no-save
```

### Watch Mode

```bash
# Default: refresh every 30 seconds (all builds)
python jenkins_monitor.py --watch

# Watch with filters
python jenkins_monitor.py --watch -f PROVISION_INFRA=true

# Custom refresh interval (60 seconds)
python jenkins_monitor.py --watch --interval 60

# Watch last 20 builds with filters
python jenkins_monitor.py --watch --limit 20 -f PROVISION_INFRA=true

# Exit with Ctrl+C
```

## Command-Line Options

```
Options:
  --url TEXT           Jenkins server URL [env: JENKINS_URL]
  --job TEXT           Jenkins job name [env: JENKINS_JOB]
  --user TEXT          Jenkins username (required) [env: JENKINS_USER]
  --token TEXT         Jenkins API token (required) [env: JENKINS_TOKEN]
  -l, --limit INTEGER  Number of builds to check (0 = all) [default: 10]
  -f, --filter TEXT    Filter builds by parameter (e.g., -f PROVISION_INFRA=true)
                       Can be used multiple times for multiple filters
                       If not specified, shows all builds
  -w, --watch          Enable watch mode (continuous monitoring)
  -i, --interval INT   Watch mode refresh interval in seconds [default: 30]
  --no-verify-ssl      Disable SSL certificate verification
  --save/--no-save     Save results to JSON/CSV (one-time mode) [default: save]
  --json-file TEXT     JSON output filename [default: jenkins_builds_install_cluster.json]
  --csv-file TEXT      CSV output filename [default: jenkins_builds_install_cluster.csv]
  --help               Show this message and exit
```

### Filter Examples

```bash
# Single filter
-f PROVISION_INFRA=true

# Multiple filters (all must match)
-f PROVISION_INFRA=true -f TEST_ENVIRONMENT=AWS

# Any parameter name
-f ENV=production
-f CLUSTER_TYPE=selfmanaged
-f CUSTOM_PARAM=value
```

## Usage Examples

### Basic One-Time Report

```bash
# All builds (no filtering)
python jenkins_monitor.py --user=myuser --token=mytoken

# Filter by parameter
python jenkins_monitor.py --user=myuser --token=mytoken -f PROVISION_INFRA=true

# Multiple filters
python jenkins_monitor.py --user=myuser --token=mytoken \
  -f PROVISION_INFRA=true \
  -f TEST_ENVIRONMENT=AWS
```

### Watch Mode Examples

```bash
# Watch all builds
python jenkins_monitor.py --user=myuser --token=mytoken --watch

# Watch filtered builds
python jenkins_monitor.py --user=myuser --token=mytoken --watch \
  -f PROVISION_INFRA=true

# Custom settings
python jenkins_monitor.py --user=myuser --token=mytoken \
  --watch \
  --interval=15 \
  --limit=30 \
  -f PROVISION_INFRA=true
```

### Using Environment Variables

```bash
# Set once
export JENKINS_USER=myuser
export JENKINS_TOKEN=mytoken
export JENKINS_URL=https://jenkins.example.com
export JENKINS_JOB=my-team/my-job

# Run with defaults (all builds)
python jenkins_monitor.py

# With filters
python jenkins_monitor.py -f PROVISION_INFRA=true

# Enable watch mode
python jenkins_monitor.py --watch
```

### Advanced Filtering

```bash
# Find all production builds with infrastructure provisioning
python jenkins_monitor.py \
  -f PROVISION_INFRA=true \
  -f TEST_ENVIRONMENT=production \
  --limit 50

# Watch Azure self-managed clusters
python jenkins_monitor.py --watch \
  -f TEST_ENVIRONMENT=AZURE \
  -f CLUSTER_TYPE=selfmanaged
```

### Disable SSL Verification (Self-Signed Certs)

```bash
python jenkins_monitor.py --user=myuser --token=mytoken --no-verify-ssl
```

### Different Jenkins Job

```bash
python jenkins_monitor.py \
  --user=myuser \
  --token=mytoken \
  --job=team/project/pipeline
```

## Output Examples

### One-Time Mode

```
Connected to Jenkins 2.528.1
Authenticated as: John Smith
Configuration: Checking last 10 builds (use --limit=0 for all builds)
Filters: PROVISION_INFRA=true
====================================================================================================

#        Status       Test Env             Cluster Type         Failed Stage                   Started              Duration     URL
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
12141    RUNNING      AWS                  selfmanaged          -                              2026-04-22 15:30:33  N/A          https://jenkins.example.com/job/team/job/my-test-job/12141/
12140    SUCCESS      Cloud-A              selfmanaged          -                              2026-04-22 15:29:58  2145.32s     https://jenkins.example.com/job/team/job/my-test-job/12140/
12138    FAILURE      AWS                  selfmanaged          Provisioning, Setup...         2026-04-22 15:02:09  399.86s      https://jenkins.example.com/job/team/job/my-test-job/12138/
12135    SUCCESS      Managed-Cloud        managed              -                              2026-04-22 12:08:11  2224.94s     https://jenkins.example.com/job/team/job/my-test-job/12135/

====================================================================================================
Summary:
  FAILURE: 1
  RUNNING: 1
  SUCCESS: 8
  Total: 10

====================================================================================================
FAILED BUILDS DETAILS:
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Build #12138
  URL: https://jenkins.example.com/job/team/job/my-test-job/12138/
  Failed Stage(s): Provisioning, Setup Authentication, Deploy Services
  Test Environment: AWS
  Cluster Type: selfmanaged
  Started: 2026-04-22 15:02:09
  Duration: 399.86s

Results saved to: jenkins_builds_PROVISION_INFRA.json
Results saved to CSV: jenkins_builds_PROVISION_INFRA.csv
```

### Watch Mode

```
JENKINS BUILD MONITOR - WATCH MODE
Jenkins: 2.528.1
User: John Smith
Job: team/my-test-job
Showing: Last 10 builds with PROVISION_INFRA=true
Refresh interval: 30 seconds

Press Ctrl+C to exit

Last updated: 2026-04-22 14:30:45 | Iteration: 5
================================================================================================

NEW  #        Status       Test Env             Cluster Type         Failed Stage                   Started              Duration    
NEW  12141    RUNNING      AWS                  selfmanaged          -                              2026-04-22 15:30:33  N/A         
     12140    SUCCESS      Cloud-A              selfmanaged          -                              2026-04-22 15:29:58  2145.32s     
     12138    FAILURE      AWS                  selfmanaged          Provisioning, Setup...         2026-04-22 15:02:09  399.86s     

================================================================================================
Summary: FAILURE: 1 | RUNNING: 1 | SUCCESS: 8 | Total: 10
New builds since last check: 1

Refreshing in 30 seconds... (Press Ctrl+C to exit)
```

## File Outputs (One-Time Mode)

### JSON Format
```json
[
  {
    "number": 12138,
    "status": "FAILURE",
    "building": false,
    "timestamp": 1745503329000,
    "duration": 399860,
    "url": "https://jenkins.example.com/job/team/job/my-test-job/12138/",
    "parameters": {
      "PROVISION_INFRA": "true",
      "TEST_ENVIRONMENT": "AWS",
      "CLUSTER_TYPE": "selfmanaged"
    },
    "failed_stages": ["Provisioning", "Setup Authentication", "Deploy Services"]
  }
]
```

### CSV Format
Includes columns: number, status, building, timestamp, started_datetime, duration_seconds, url, test_environment, cluster_type, failed_stages, and all other job parameters.

## Tips

- **First run**: Use one-time mode without filters to see all builds
- **Active monitoring**: Use watch mode during deployments to see builds complete in real-time
- **Running builds**: Builds show as `RUNNING` (blue) until they complete
- **Filter strategically**: Use `-f` to focus on specific builds (e.g., only cluster installations)
- **Multiple filters**: Combine filters for precise queries (filters use AND logic)
- **Long history**: Increase `--limit` to see more builds
- **Fast refresh**: Set `--interval 10` for rapid updates during active development
- **All builds**: Use `--limit 0` (may be slow for large job histories)
- **Multiple jobs**: Run multiple instances in different terminals
- **More examples**: See **[USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md)** for practical scenarios

## Troubleshooting

### Authentication Fails
- Verify username and token are correct
- Generate a new API token from Jenkins
- Check you have permission to access the job

### SSL Certificate Errors
- Use `--no-verify-ssl` for self-signed certificates
- Or set `JENKINS_SSL_VERIFY=false` environment variable

### No Builds Found
- If using filters: Try removing filters to see all builds
- Verify the job path is correct (e.g., `team/project/job`)
- Check filter parameter names match exactly (case-sensitive)
- Increase `--limit` to check more builds

### Running Builds

Running builds are **automatically included** and show:
- Status: `RUNNING` (displayed in blue)
- Duration: `N/A` (no duration while running)
- Building: `true` in JSON output

In watch mode, you'll see builds transition from `RUNNING` to their final status (`SUCCESS`, `FAILURE`, etc.)

### Failed Stage Not Detected
- Check if wfapi plugin is installed on Jenkins
- Verify you have permission to access build details
- Stage names may not be available for all job types

## Watch Mode Visual Feedback

Watch mode includes dynamic status indicators to provide real-time feedback:

### Status Icons

| Icon | Meaning | Color |
|------|---------|-------|
| ↓ | Fetching data | Cyan |
| ✓ | Refresh successful | Green |
| ✗ | Refresh failed | Red |
| ↻ | Countdown to next refresh | Cyan |

### Example Display

```
Last updated: 2026-04-22 14:30:45 | Iteration: 5 | ✓ Last refresh successful
============================================================================================
NEW  #        Status       Test Env             Cluster Type
     12135    RUNNING      staging              kubernetes-aws

⠋ Next refresh in 25 seconds... (Press Ctrl+C to exit)
```

### Error Handling

If a refresh fails, the previous data is retained and an error indicator appears:

```
Last updated: 2026-04-22 14:31:45 | Iteration: 6 | ✗ Refresh failed: Connection timeout
```

The tool automatically retries on the next refresh interval.

**See [WATCH_MODE_GUIDE.md](docs/WATCH_MODE_GUIDE.md) for detailed documentation on visual indicators.**

## 📖 Additional Documentation

- **[USAGE_EXAMPLES.md](docs/USAGE_EXAMPLES.md)** - Practical usage scenarios and examples
- **[WATCH_MODE_GUIDE.md](docs/WATCH_MODE_GUIDE.md)** - Visual feedback and watch mode details
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and migration guide
- **README.md** - This file (overview and quick start)

## Acknowledgments

This project was developed with the assistance of Claude Code (Sonnet 4.5)

## License

MIT
