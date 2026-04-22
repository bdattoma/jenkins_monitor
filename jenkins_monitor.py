#!/usr/bin/env python3
"""
Jenkins Build Monitor - Unified script with one-time and watch modes
Install: pip install python-jenkins click
"""

import jenkins
import json
import os
import urllib3
import requests
import re
import time
import sys
import csv
import click
from datetime import datetime

# Disable SSL warnings when SSL verification is disabled
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ANSI color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'


# Status icons
class Icons:
    SPINNER = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    SUCCESS = '✓'
    ERROR = '✗'
    WARNING = '⚠'
    REFRESH = '↻'
    FETCHING = '↓'  # Down arrow for fetching data


class RefreshStatus:
    """Manages refresh status display with icons"""
    def __init__(self):
        self.spinner_index = 0
        self.status = 'idle'  # idle, refreshing, success, error
        self.last_refresh_time = None
        self.error_message = None

    def start_refresh(self):
        """Start a refresh operation"""
        self.status = 'refreshing'
        self.error_message = None

    def complete_success(self):
        """Mark refresh as successful"""
        self.status = 'success'
        self.last_refresh_time = datetime.now()

    def complete_error(self, error_msg):
        """Mark refresh as failed"""
        self.status = 'error'
        self.error_message = error_msg
        self.last_refresh_time = datetime.now()

    def get_spinner_frame(self):
        """Get next spinner frame"""
        frame = Icons.SPINNER[self.spinner_index]
        self.spinner_index = (self.spinner_index + 1) % len(Icons.SPINNER)
        return frame

    def get_status_display(self):
        """Get the status display with icon and color"""
        if self.status == 'refreshing':
            return f"{Colors.CYAN}{Icons.FETCHING} Fetching data...{Colors.RESET}"
        elif self.status == 'success':
            return f"{Colors.GREEN}{Icons.SUCCESS} Last refresh successful{Colors.RESET}"
        elif self.status == 'error':
            return f"{Colors.RED}{Icons.ERROR} Refresh failed: {self.error_message}{Colors.RESET}"
        else:
            return ""


def get_build_parameters(build_info):
    """Extract parameters from a build"""
    parameters = {}
    for action in build_info.get('actions', []):
        if action.get('_class') == 'hudson.model.ParametersAction':
            for param in action.get('parameters', []):
                param_name = param.get('name')
                if param_name:
                    param_value = param.get('value', param.get('defaultValue', None))
                    parameters[param_name] = param_value
    return parameters


def get_failed_stages(server, job_name, build_num, debug=False):
    """Get the list of failed stages from a pipeline build"""
    failed_stages = []

    # Method 1: Try wfapi/describe endpoint
    try:
        base_url = server.server.rstrip('/')
        job_name_api = '/job/'.join(job_name.split('/'))
        stages_url = f"{base_url}/job/{job_name_api}/{build_num}/wfapi/describe"
        response = server._session.get(stages_url)

        if debug:
            print(f"  wfapi URL: {stages_url}")
            print(f"  wfapi status: {response.status_code}")

        if response.status_code == 200:
            stages_data = response.json()

            if debug:
                print(f"  wfapi stages found: {len(stages_data.get('stages', []))}")

            for stage in stages_data.get('stages', []):
                stage_name = stage.get('name')
                stage_status = stage.get('status')

                if debug:
                    print(f"    - {stage_name}: {stage_status}")

                if stage_status in ['FAILED', 'FAILURE']:
                    failed_stages.append(stage_name)

            if failed_stages:
                return failed_stages
    except Exception as e:
        if debug:
            print(f"  wfapi method failed: {type(e).__name__}: {e}")

    # Method 2: Parse console output for stage failures
    try:
        console = server.get_build_console_output(job_name, build_num)
        lines = console.split('\n')

        for i, line in enumerate(lines):
            if '[Pipeline] stage' in line or 'Stage "' in line or "stage '" in line:
                for j in range(i, min(i+20, len(lines))):
                    if 'ERROR' in lines[j] or 'FAILED' in lines[j] or 'failed' in lines[j]:
                        if '[Pipeline] stage' in line:
                            match = re.search(r'\[Pipeline\] stage.*?\((.*?)\)', line)
                            if match:
                                stage_name = match.group(1)
                                if stage_name not in failed_stages:
                                    failed_stages.append(stage_name)
                        break

        if failed_stages:
            return failed_stages
    except Exception as e:
        if debug:
            print(f"  Console parsing method failed: {type(e).__name__}: {e}")

    return []


def parse_filter_params(filter_params):
    """Parse filter parameter strings like 'KEY=value' into a dict"""
    filters = {}
    if filter_params:
        for param in filter_params:
            if '=' in param:
                key, value = param.split('=', 1)
                filters[key.strip()] = value.strip()
    return filters


def matches_filter(parameters, filters):
    """Check if build parameters match the filter criteria"""
    if not filters:
        return True  # No filters means match everything

    for key, expected_value in filters.items():
        param_value = parameters.get(key)

        # Handle boolean and string representations
        if expected_value.lower() in ['true', 'false']:
            # Compare as boolean
            if expected_value.lower() == 'true':
                if param_value not in [True, 'true', 'True', 'TRUE']:
                    return False
            else:
                if param_value not in [False, 'false', 'False', 'FALSE']:
                    return False
        else:
            # Compare as string
            if str(param_value) != expected_value:
                return False

    return True


def get_builds(server, job_name, limit=None, filter_params=None, quiet=False):
    """Get builds, optionally filtered by parameters"""
    try:
        job_info = server.get_job_info(job_name, depth=1)

        if not quiet:
            print(f"Job Name: {job_info['name']}")
            print(f"Job URL: {job_info['url']}")
            print(f"Total Builds Available: {len(job_info['builds'])}")

        if limit is not None and limit > 0:
            builds_to_check = job_info['builds'][:limit]
            if not quiet:
                print(f"Build Limit: {limit} (only checking the last {limit} builds)")
        else:
            builds_to_check = job_info['builds']
            if not quiet:
                print(f"Build Limit: None (checking ALL builds)")

        # Parse filter parameters
        filters = parse_filter_params(filter_params)

        if not quiet:
            if filters:
                filter_strs = [f"{k}={v}" for k, v in filters.items()]
                print(f"Filters: {', '.join(filter_strs)}")
            else:
                print(f"Filters: None (showing all builds)")
            print("=" * 100)

        filtered_builds = []

        if not quiet:
            if filters:
                print(f"\nFetching build details and filtering by {', '.join([f'{k}={v}' for k, v in filters.items()])}...")
            else:
                print(f"\nFetching build details (no filters, all builds)...")
            print(f"Processing {len(builds_to_check)} builds...\n")

        for idx, build in enumerate(builds_to_check, 1):
            build_num = build['number']

            if not quiet and idx % 10 == 0:
                print(f"Processed {idx}/{len(builds_to_check)} builds...")

            try:
                build_info = server.get_build_info(job_name, build_num)
                parameters = get_build_parameters(build_info)

                # Check if build matches filters
                if matches_filter(parameters, filters):
                    failed_stages = []
                    status = build_info['result'] or 'RUNNING'

                    if status == 'FAILURE':
                        if not quiet:
                            failed_stages = get_failed_stages(server, job_name, build_num, debug=True)
                        else:
                            failed_stages = get_failed_stages(server, job_name, build_num, debug=False)

                    filtered_builds.append({
                        'number': build_num,
                        'status': status,
                        'building': build_info['building'],
                        'timestamp': build_info['timestamp'],
                        'duration': build_info['duration'],
                        'url': build_info['url'],
                        'parameters': parameters,
                        'failed_stages': failed_stages
                    })

            except Exception as e:
                if not quiet:
                    print(f"Error fetching build #{build_num}: {e}")
                continue

        if not quiet:
            if filters:
                filter_desc = ', '.join([f'{k}={v}' for k, v in filters.items()])
                print(f"\nCompleted! Found {len(filtered_builds)} builds matching filters: {filter_desc}")
            else:
                print(f"\nCompleted! Found {len(filtered_builds)} builds")
            print("=" * 100)

        return filtered_builds

    except jenkins.JenkinsException as e:
        print(f"Jenkins error: {e}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')


def countdown_with_spinner(seconds):
    """Display a countdown with spinner animation"""
    try:
        for remaining in range(seconds, 0, -1):
            spinner_frame = Icons.SPINNER[remaining % len(Icons.SPINNER)]
            sys.stdout.write(f'\r{Colors.CYAN}{spinner_frame} Next refresh in {remaining} seconds... (Press Ctrl+C to exit){Colors.RESET}')
            sys.stdout.flush()
            time.sleep(1)
        sys.stdout.write('\r' + ' ' * 80 + '\r')  # Clear the line
        sys.stdout.flush()
    except KeyboardInterrupt:
        raise  # Re-raise to let outer handler catch it

def show_refresh_status(refresh_status):
    """Show the refresh status"""
    print(f"{Colors.CYAN}{refresh_status.get_status_display()}{Colors.RESET}")


def display_filtered_builds(builds, last_builds=None, watch_mode=False):
    """Display the filtered builds in a readable format"""
    if not builds:
        print("\nNo builds found with MY_JOB_PARAMETER=true")
        return

    # Detect new builds in watch mode
    new_build_numbers = set()
    if watch_mode and last_builds:
        current_nums = {b['number'] for b in builds}
        last_nums = {b['number'] for b in last_builds}
        new_build_numbers = current_nums - last_nums

    # Header
    if watch_mode:
        header = f"\n{'NEW':<4} {'#':<8} {'Status':<12} {'Test Env':<20} {'Cluster Type':<20} {'Failed Stage':<30} {'Started':<20} {'Duration':<12}"
        separator = "-" * 160
    else:
        header = f"\n{'#':<8} {'Status':<12} {'Test Env':<20} {'Cluster Type':<20} {'Failed Stage':<30} {'Started':<20} {'Duration':<12} {'URL'}"
        separator = "-" * 180

    print(header)
    print(separator)

    for build in builds:
        build_num = build['number']
        status = build['status']
        timestamp = datetime.fromtimestamp(build['timestamp'] / 1000)
        started = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        duration = f"{build['duration'] / 1000:.2f}s" if build['duration'] else "N/A"
        url = build['url']

        params = build['parameters']
        test_env = params.get('TEST_ENVIRONMENT', 'N/A')
        cluster_type = params.get('CLUSTER_TYPE', 'N/A')

        failed_stages = build.get('failed_stages', [])
        failed_stage_str = ', '.join(failed_stages) if failed_stages else '-'

        # Truncate long values
        if len(str(test_env)) > 18:
            test_env = str(test_env)[:15] + "..."
        if len(str(cluster_type)) > 18:
            cluster_type = str(cluster_type)[:15] + "..."
        if len(failed_stage_str) > 28:
            failed_stage_str = failed_stage_str[:25] + "..."

        # Format the line
        if watch_mode:
            new_indicator = f"{Colors.CYAN}NEW{Colors.RESET}" if build_num in new_build_numbers else "   "
            line = f"{new_indicator:<4} {build_num:<8} {status:<12} {test_env:<20} {cluster_type:<20} {failed_stage_str:<30} {started:<20} {duration:<12}"
        else:
            line = f"{build_num:<8} {status:<12} {test_env:<20} {cluster_type:<20} {failed_stage_str:<30} {started:<20} {duration:<12} {url}"

        # Color-code by status
        if status == 'FAILURE':
            print(f"{Colors.RED}{Colors.BOLD}{line}{Colors.RESET}")
        elif status == 'UNSTABLE':
            print(f"{Colors.YELLOW}{line}{Colors.RESET}")
        elif status == 'SUCCESS':
            print(f"{Colors.GREEN}{line}{Colors.RESET}")
        elif status == 'ABORTED':
            print(f"{Colors.MAGENTA}{line}{Colors.RESET}")
        elif status == 'RUNNING':
            print(f"{Colors.BLUE}{line}{Colors.RESET}")
        else:
            print(line)

    # Summary
    sep_len = 160 if watch_mode else 180
    print("\n" + "=" * sep_len)

    status_counts = {}
    for build in builds:
        status = build['status']
        status_counts[status] = status_counts.get(status, 0) + 1

    if watch_mode:
        # Compact summary for watch mode
        summary_parts = []
        for status, count in sorted(status_counts.items()):
            if status == 'FAILURE':
                summary_parts.append(f"{Colors.RED}{Colors.BOLD}{status}: {count}{Colors.RESET}")
            elif status == 'SUCCESS':
                summary_parts.append(f"{Colors.GREEN}{status}: {count}{Colors.RESET}")
            elif status == 'UNSTABLE':
                summary_parts.append(f"{Colors.YELLOW}{status}: {count}{Colors.RESET}")
            elif status == 'RUNNING':
                summary_parts.append(f"{Colors.BLUE}{status}: {count}{Colors.RESET}")
            else:
                summary_parts.append(f"{status}: {count}")

        print("Summary: " + " | ".join(summary_parts) + f" | Total: {len(builds)}")

        if new_build_numbers:
            print(f"{Colors.CYAN}New builds since last check: {len(new_build_numbers)}{Colors.RESET}")
    else:
        # Detailed summary for one-time mode
        print("Summary:")
        for status, count in sorted(status_counts.items()):
            if status == 'FAILURE':
                print(f"  {Colors.RED}{Colors.BOLD}{status}: {count}{Colors.RESET}")
            elif status == 'SUCCESS':
                print(f"  {Colors.GREEN}{status}: {count}{Colors.RESET}")
            elif status == 'UNSTABLE':
                print(f"  {Colors.YELLOW}{status}: {count}{Colors.RESET}")
            else:
                print(f"  {status}: {count}")

        print(f"  Total: {len(builds)}")

        # Show failed builds details
        failed_builds = [b for b in builds if b['status'] == 'FAILURE']
        if failed_builds:
            print("\n" + "=" * 180)
            print(f"{Colors.RED}{Colors.BOLD}FAILED BUILDS DETAILS:{Colors.RESET}")
            print("-" * 180)
            for build in failed_builds:
                params = build['parameters']
                failed_stages = build.get('failed_stages', [])

                print(f"\n{Colors.RED}{Colors.BOLD}Build #{build['number']}{Colors.RESET}")
                print(f"  URL: {build['url']}")
                if failed_stages:
                    print(f"  {Colors.RED}Failed Stage(s): {', '.join(failed_stages)}{Colors.RESET}")
                else:
                    print(f"  Failed Stage(s): Unable to determine")
                print(f"  Test Environment: {params.get('TEST_ENVIRONMENT', 'N/A')}")
                print(f"  Cluster Type: {params.get('CLUSTER_TYPE', 'N/A')}")
                print(f"  Started: {datetime.fromtimestamp(build['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"  Duration: {build['duration'] / 1000:.2f}s" if build['duration'] else "  Duration: N/A")


def save_to_json(builds, filename="jenkins_builds_install_cluster.json", quiet=False):
    """Save the filtered builds to a JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(builds, f, indent=2)
        if not quiet:
            print(f"\nResults saved to: {filename}")
    except Exception as e:
        if not quiet:
            print(f"Error saving to JSON: {e}")


def save_to_csv(builds, filename="jenkins_builds_install_cluster.csv", quiet=False):
    """Save the filtered builds to a CSV file"""
    try:
        with open(filename, 'w', newline='') as f:
            if not builds:
                return

            param_keys = set()
            for build in builds:
                param_keys.update(build['parameters'].keys())

            fieldnames = ['number', 'status', 'building', 'timestamp', 'started_datetime',
                         'duration_seconds', 'url', 'test_environment', 'cluster_type', 'failed_stages']

            other_params = sorted(param_keys - {'TEST_ENVIRONMENT', 'CLUSTER_TYPE', 'MY_JOB_PARAMETER'})
            fieldnames.extend(other_params)

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for build in builds:
                params = build['parameters']
                failed_stages = build.get('failed_stages', [])

                row = {
                    'number': build['number'],
                    'status': build['status'],
                    'building': build['building'],
                    'timestamp': build['timestamp'],
                    'started_datetime': datetime.fromtimestamp(build['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                    'duration_seconds': build['duration'] / 1000 if build['duration'] else 0,
                    'url': build['url'],
                    'test_environment': params.get('TEST_ENVIRONMENT', ''),
                    'cluster_type': params.get('CLUSTER_TYPE', ''),
                    'failed_stages': ', '.join(failed_stages) if failed_stages else '',
                }
                for key in other_params:
                    row[key] = params.get(key, '')

                writer.writerow(row)

        if not quiet:
            print(f"Results saved to CSV: {filename}")
    except Exception as e:
        if not quiet:
            print(f"Error saving to CSV: {e}")

def show_intro(user_info, version, job, limit=None, filter_params=None):
    """Show the watch mode introduction header"""
    print(f"{Colors.BOLD}JENKINS BUILD MONITOR - WATCH MODE{Colors.RESET}")
    print(f"Jenkins: {version}")
    print(f"User: {user_info['fullName']}")
    print(f"Job: {job}")

    # Build limit info
    if limit:
        print(f"Showing: Last {limit} builds")
    else:
        print(f"Showing: All builds")

    # Filter info
    if filter_params:
        filters = parse_filter_params(filter_params)
        filter_strs = [f"{k}={v}" for k, v in filters.items()]
        print(f"Filters: {', '.join(filter_strs)}")
    else:
        print(f"Filters: None (showing all builds)")

def show_iteration_header(iteration, refresh_status):
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{Colors.BOLD}JENKINS BUILD MONITOR{Colors.RESET} | Last updated: {current_time} | Iteration: {iteration} | {refresh_status.get_status_display()}")
    print("=" * 160)



@click.command()
@click.option('--url', default='https://jenkins.example.com',
              envvar='JENKINS_URL', help='Jenkins server URL')
@click.option('--job', default='team/project/pipeline',
              envvar='JENKINS_JOB', help='Jenkins job name')
@click.option('--user', envvar='JENKINS_USER', required=True,
              help='Jenkins username (or set JENKINS_USER env var)')
@click.option('--token', envvar='JENKINS_TOKEN', required=True,
              help='Jenkins API token (or set JENKINS_TOKEN env var)')
@click.option('--limit', '-l', default=10, type=int,
              help='Number of builds to check (0 = all builds)')
@click.option('--filter', '-f', 'filter_params', multiple=True,
              help='Filter builds by parameter (e.g., -f MY_JOB_PARAMETER=true -f ENV=prod). Can be used multiple times. If not specified, shows all builds.')
@click.option('--watch', '-w', is_flag=True,
              help='Enable watch mode (continuous monitoring)')
@click.option('--interval', '-i', default=30, type=int,
              help='Watch mode refresh interval in seconds')
@click.option('--no-verify-ssl', is_flag=True,
              help='Disable SSL certificate verification')
@click.option('--save/--no-save', default=True,
              help='Save results to JSON/CSV files (one-time mode only)')
@click.option('--json-file', default='jenkins_builds_install_cluster.json',
              help='JSON output filename')
@click.option('--csv-file', default='jenkins_builds_install_cluster.csv',
              help='CSV output filename')
@click.option('--quiet', '-q', is_flag=True,
              help='Suppress progress messages (one-time mode only)')
def main(url, job, user, token, limit, filter_params, watch, interval, no_verify_ssl, save, json_file, csv_file, quiet):
    """
    Jenkins Build Monitor - Monitor job builds, optionally filtered by parameters

    \b
    Examples:

    #### Set credentials ####
      export JENKINS_USER=myuser
      export JENKINS_TOKEN=mytoken

    #### One-time report (last 10 builds, all parameters) ####
      python jenkins_monitor.py 

    #### Watch mode (refresh every 30 seconds) ####
      python jenkins_monitor.py --watch

    #### Watch mode with filters ####
      python jenkins_monitor.py --watch -f MY_JOB_PARAMETER=true

    python jenkins_monitor.py --watch
    """
    try:
        # Convert limit
        build_limit = limit if limit > 0 else None

        # Connect to Jenkins
        server = jenkins.Jenkins(url, username=user, password=token)
        server._session.verify = not no_verify_ssl

        # Verify connection
        jenkins_user = server.get_whoami()
        version = server.get_version()

        if watch:
            # Watch mode
            show_intro(jenkins_user, version, job, build_limit, filter_params)

            print(f"Refresh interval: {interval} seconds")
            if no_verify_ssl:
                print(f"{Colors.YELLOW}WARNING: SSL verification disabled{Colors.RESET}")
            print(f"\n{Colors.CYAN}Press Ctrl+C to exit{Colors.RESET}\n")

            last_builds = None
            iteration = 0
            refresh_status = RefreshStatus()

            while True:
                try:
                    iteration += 1
                    refresh_status.start_refresh()
                    show_refresh_status(refresh_status)
                    # Get builds
                    try:
                        builds = get_builds(server, job, limit=build_limit, filter_params=filter_params, quiet=True)
                        refresh_status.complete_success()
                    except Exception as e:
                        refresh_status.complete_error(str(e))
                        builds = last_builds if last_builds else []
                    
                    show_refresh_status(refresh_status)

                    # Clear screen and show header
                    if iteration > 1:
                        clear_screen()
                        show_intro(jenkins_user, version, job, build_limit, filter_params)

                    # Update header with final status
                    # Move cursor up to overwrite the header line
                    sys.stdout.write('\033[F' * 2)  # Move up 2 lines (header + separator)
                    sys.stdout.flush()
                    show_iteration_header(iteration, refresh_status)

                    # Display results
                    display_filtered_builds(builds, last_builds=last_builds, watch_mode=True)

                    last_builds = builds

                    # Show countdown with spinner
                    print()  # Blank line before countdown
                    countdown_with_spinner(interval)

                except KeyboardInterrupt:
                    print(f"\n\n{Colors.YELLOW}Exiting watch mode...{Colors.RESET}")
                    break

        else:
            # One-time mode
            if not quiet:
                print(f"Connected to Jenkins {version}")
                print(f"Authenticated as: {jenkins_user['fullName']}")

                if build_limit:
                    print(f"Configuration: Checking last {build_limit} builds (use --limit=0 for all builds)")
                else:
                    print(f"Configuration: Checking ALL builds")

                if filter_params:
                    filters = parse_filter_params(filter_params)
                    filter_strs = [f"{k}={v}" for k, v in filters.items()]
                    print(f"Filters: {', '.join(filter_strs)}")
                else:
                    print(f"Filters: None (showing all builds)")

                if no_verify_ssl:
                    print(f"{Colors.YELLOW}WARNING: SSL verification disabled{Colors.RESET}")

                print("=" * 100)

            # Get builds
            builds = get_builds(server, job, limit=build_limit, filter_params=filter_params, quiet=quiet)

            # Display results
            display_filtered_builds(builds, watch_mode=False)

            # Save to files
            if save and builds:
                save_to_json(builds, json_file, quiet=quiet)
                save_to_csv(builds, csv_file, quiet=quiet)

    except jenkins.JenkinsException as e:
        click.echo(f"{Colors.RED}Failed to connect to Jenkins: {e}{Colors.RESET}", err=True)
        click.echo("\nTips:")
        click.echo("1. Make sure your username and API token are correct")
        click.echo("2. Generate API token from: Jenkins -> User -> Configure -> API Token")
        click.echo("3. Check if you have permission to access this job")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Exiting...{Colors.RESET}")
    except Exception as e:
        click.echo(f"{Colors.RED}Error: {e}{Colors.RESET}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
