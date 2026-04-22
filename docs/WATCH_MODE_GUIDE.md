# Watch Mode Visual Feedback Guide

## Overview

Watch mode now includes dynamic visual indicators to show the refresh status in real-time.

## Status Indicators

### 🔄 Fetching Data (In Progress)

When fetching new data from Jenkins, you'll see a down arrow:

```
JENKINS BUILD MONITOR | Last updated: 2026-04-22 14:30:45 | Iteration: 5 | ↓ Fetching data...
```

### ✓ Success (Refresh Completed)

When data is successfully fetched, the spinner changes to a checkmark:

```
JENKINS BUILD MONITOR | Last updated: 2026-04-22 14:30:45 | Iteration: 5 | ✓ Last refresh successful
```

Color: **Green**

### ✗ Error (Refresh Failed)

If an error occurs during refresh, an X icon appears with the error message:

```
JENKINS BUILD MONITOR | Last updated: 2026-04-22 14:30:45 | Iteration: 5 | ✗ Refresh failed: Connection timeout
```

Color: **Red**

When refresh fails, the previous data is retained and displayed.

### ↻ Countdown (Waiting for Next Refresh)

Between refreshes, a countdown timer appears with a rotating icon:

```
⠋ Next refresh in 25 seconds... (Press Ctrl+C to exit)
```

The countdown updates every second, showing the exact time remaining.

## Visual Flow

A typical watch mode session shows this progression:

1. **Initial load**: `↓ Fetching data...`
2. **Data fetched**: `✓ Last refresh successful`
3. **Waiting**: `↻ Next refresh in 30 seconds...`
4. **Next refresh**: `↓ Fetching data...`
5. And repeat...

## Error Handling

If a refresh fails:

1. **Error displayed**: `✗ Refresh failed: [error message]`
2. **Previous data retained**: Last successful data remains visible
3. **Countdown continues**: Next refresh attempts automatically
4. **Automatic retry**: The next refresh will try again

Example error scenarios:
- Network timeout: `✗ Refresh failed: Connection timeout`
- Authentication: `✗ Refresh failed: 401 Unauthorized`
- Jenkins unavailable: `✗ Refresh failed: Connection refused`

## Status Colors

| Status | Icon | Color | Meaning |
|--------|------|-------|---------|
| Fetching | ↓ | Cyan | Actively fetching data |
| Success | ✓ | Green | Refresh completed successfully |
| Error | ✗ | Red | Refresh failed |
| Countdown | ↻ | Cyan | Waiting for next refresh |

## Examples

### Normal Operation

```
JENKINS BUILD MONITOR - WATCH MODE
Jenkins: 2.401
User: John Smith
Job: team/project/pipeline
Showing: Last 10 builds
Filters: INSTALL_CLUSTER=true
Refresh interval: 30 seconds

Last updated: 2026-04-22 14:30:45 | Iteration: 5 | ✓ Last refresh successful
============================================================================================

NEW  #        Status       Test Env             Cluster Type         Failed Stage
     12135    RUNNING      staging              kubernetes-aws       -
     12134    FAILURE      production           managed-k8s          Test Execution

⠋ Next refresh in 25 seconds... (Press Ctrl+C to exit)
```

### During Refresh

```
Last updated: 2026-04-22 14:31:15 | Iteration: 6 | ↓ Fetching data...
============================================================================================
```

### After Error

```
Last updated: 2026-04-22 14:31:45 | Iteration: 7 | ✗ Refresh failed: HTTPSConnectionPool timeout
============================================================================================

# Previous data still displayed
     12135    SUCCESS      staging              kubernetes-aws       -
     12134    FAILURE      production           managed-k8s          Test Execution

⠋ Next refresh in 28 seconds... (Press Ctrl+C to exit)
```

## Tips

### Monitoring Refresh Success

- Watch for the ✓ icon to confirm successful refresh
- Green checkmark = everything is working
- Red X = something went wrong (but watch mode continues)

### During Network Issues

- Previous data remains visible
- Error message shows what went wrong
- Next refresh automatically retries
- No need to restart watch mode

### Fast Refresh Monitoring

When using fast refresh intervals (e.g., `--interval 5`):

```bash
python jenkins_monitor.py --watch --interval 5
```

You'll see rapid status transitions:
1. `↓ Fetching data...` (1-2 seconds)
2. `✓ Last refresh successful` (brief moment)
3. `↻ Next refresh in 5 seconds...` (countdown)
4. Repeat

### Slow Connections

If refreshes take a long time:
- Down arrow (↓) shows the tool is fetching data
- Confirms the tool is still working
- Not frozen or hung

## Keyboard Shortcuts

- **Ctrl+C**: Exit watch mode immediately (works during countdown or refresh)
- No other interaction needed - everything is automatic

## Accessibility

The status indicators use:
- **Icons**: Visual representation
- **Text**: Clear status messages
- **Colors**: Additional visual feedback

Even without color support, the text messages provide full information:
- "Refreshing..."
- "Last refresh successful"
- "Refresh failed: [error]"

## Technical Details

### Status Icon Display

- Updates header in place (overwrites previous line)
- Uses ANSI escape codes for cursor movement
- Down arrow (↓) shows during data fetch
- Minimal CPU usage

### Countdown Timer

- Updates every second
- Shows exact remaining time
- Spinner rotates through frames
- Press Ctrl+C to interrupt

### Error Recovery

1. Exception caught during `get_builds()`
2. Error status set with message
3. Previous builds retained
4. Display updated with error icon
5. Countdown proceeds normally
6. Next iteration attempts refresh again

## Troubleshooting

### Icons Not Displaying

If you see question marks or boxes instead of icons:
- Your terminal may not support Unicode
- Status text still provides information
- Consider using a modern terminal (iTerm2, Windows Terminal, etc.)

### Refresh Status Not Updating

- Ensure terminal supports ANSI escape codes
- Try clearing terminal: `reset` or `clear`
- Restart watch mode

### Error Messages Unclear

Error messages come directly from the exception:
- Network errors: timeout, connection refused
- Authentication: 401, 403 errors
- Jenkins errors: specific Jenkins messages

Check Jenkins logs and network connectivity for more details.

## Comparison with Previous Version

| Feature | Before | After |
|---------|--------|-------|
| Refresh status | No indicator | Animated spinner |
| Success feedback | Timestamp only | ✓ icon + message |
| Error handling | Generic error | ✗ icon + details |
| Countdown | Static message | Animated timer |
| Visual feedback | Minimal | Rich and dynamic |

## See Also

- `README.md` - Main documentation
- `USAGE_EXAMPLES.md` - Practical examples
- Run `python jenkins_monitor.py --help` for command reference
