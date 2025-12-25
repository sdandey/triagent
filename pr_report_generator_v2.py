#!/usr/bin/env python3
"""Generate comprehensive Pull Request report for Omnia Data teams - Version 2.

This version uses repository ownership mapping instead of work item area paths
for more accurate team attribution.
"""

import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Configuration
ORG_URL = "https://dev.azure.com/symphonyvsts"
PROJECT = "Audit Cortex 2"
TARGET_BRANCHES = ["develop", "master", "main"]

# Date range: Past 6 months from today (2025-12-24)
END_DATE = datetime(2025, 12, 24)
START_DATE = END_DATE - timedelta(days=180)  # 6 months

# Repository ownership mapping (from omnia_data.md)
REPO_OWNERSHIP = {
    "data-exchange-service": ["Alpha", "Kilo"],
    "cortex-datamanagement-services": ["Gamma"],
    "engagement-service": ["Alpha", "Skyrockets"],
    "security-service": ["Skyrockets"],
    "data-kitchen-service": ["Beta", "Megatron"],
    "analytic-template-service": ["Tera"],
    "notification-service": ["Beta", "Skyrockets"],
    "staging-service": ["Gamma", "Alpha"],
    "spark-job-management": ["Alpha", "Beta"],
    "cortex-ui": ["Tera"],
    "client-service": ["Beta"],
    "workpaper-service": ["Giga"],
    "async-workflow-framework": ["Alpha", "Giga"],
    "sampling-service": ["Giga"],
    "localization-service": ["Justice League", "Skyrockets"],
    "scheduler-service": ["Alpha"],
    "cortexpy": ["Delta", "Beta"],
    "analytic-notebooks": ["Beta"],
}

# Repositories to check
REPOSITORIES = list(REPO_OWNERSHIP.keys())

# Team PODs for organization
PODS = {
    "Data Acquisition and Preparation": ["Alpha", "Beta", "Megatron"],
    "Data Management and Activation": ["Delta", "Gamma", "Skyrockets"],
    "Omnia JE": ["Exa", "Jupiter", "Justice League", "Neptune", "Peta", "Saturn", "Utopia"],
    "Data In Use": ["Giga", "Kilo", "Tera"],
    "Other Teams": ["Galileo", "Core Data Engineering", "Health Monitoring", "SpaceBots"],
}


def run_az_command(command: str) -> dict[str, Any]:
    """Execute an Azure CLI command and return parsed JSON output."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            if result.stdout.strip():
                return json.loads(result.stdout)
            return []
        else:
            print(f"Error executing command: {command}", file=sys.stderr)
            print(f"Error: {result.stderr}", file=sys.stderr)
            return []
    except subprocess.TimeoutExpired:
        print(f"Command timed out: {command}", file=sys.stderr)
        return []
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON: {e}", file=sys.stderr)
        print(f"Output: {result.stdout[:500]}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return []


def fetch_prs_for_repo(repo_name: str) -> list[dict[str, Any]]:
    """Fetch all PRs for a repository targeting develop/master/main branches."""
    all_prs = []

    print(f"Fetching PRs for {repo_name}...", file=sys.stderr)

    for branch in TARGET_BRANCHES:
        command = (
            f'az repos pr list '
            f'--org "{ORG_URL}" '
            f'--project "{PROJECT}" '
            f'--repository "{repo_name}" '
            f'--target-branch "{branch}" '
            f'--status all '
            f'--output json'
        )

        prs = run_az_command(command)

        if prs:
            print(f"  Found {len(prs)} PRs targeting {branch}", file=sys.stderr)
            # Add repository name to each PR for later attribution
            for pr in prs:
                pr["_repository_name"] = repo_name
            all_prs.extend(prs)

    return all_prs


def parse_date(date_str: str | None) -> datetime | None:
    """Parse ISO date string to datetime."""
    if not date_str:
        return None

    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def get_pr_teams(pr: dict[str, Any]) -> list[str]:
    """Determine the team(s) for a PR based on repository ownership."""
    repo_name = pr.get("_repository_name", pr.get("repository", {}).get("name", ""))

    if repo_name in REPO_OWNERSHIP:
        return REPO_OWNERSHIP[repo_name]

    return ["Unknown"]


def filter_prs_by_date(prs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter PRs created within the date range."""
    filtered = []

    for pr in prs:
        created_date = parse_date(pr.get("creationDate"))

        if created_date and START_DATE <= created_date.replace(tzinfo=None) <= END_DATE:
            filtered.append(pr)

    return filtered


def analyze_prs(all_prs: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze PRs and generate statistics."""
    # Group PRs by team (PRs can belong to multiple teams)
    team_prs: dict[str, list[dict[str, Any]]] = defaultdict(list)

    # Daily statistics
    daily_created: dict[str, int] = defaultdict(int)
    daily_merged: dict[str, int] = defaultdict(int)
    daily_by_team: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: {"created": 0, "merged": 0})
    )

    # Repository statistics
    repo_stats: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "merged": 0})

    print(f"\nAnalyzing {len(all_prs)} PRs...", file=sys.stderr)

    for i, pr in enumerate(all_prs):
        if i % 50 == 0 and i > 0:
            print(f"  Processed {i}/{len(all_prs)} PRs...", file=sys.stderr)

        # Get teams for this PR (can be multiple)
        teams = get_pr_teams(pr)

        # Add PR to each team's list
        for team in teams:
            team_prs[team].append(pr)

        # Track creation date
        created_date = parse_date(pr.get("creationDate"))
        if created_date:
            created_day = created_date.date().isoformat()
            daily_created[created_day] += 1

            for team in teams:
                daily_by_team[team][created_day]["created"] += 1

        # Track merge date (if completed)
        is_merged = pr.get("status") == "completed"
        if is_merged:
            closed_date = parse_date(pr.get("closedDate"))
            if closed_date:
                merged_day = closed_date.date().isoformat()
                daily_merged[merged_day] += 1

                for team in teams:
                    daily_by_team[team][merged_day]["merged"] += 1

        # Track repository stats
        repo_name = pr.get("_repository_name", pr.get("repository", {}).get("name", "Unknown"))
        repo_stats[repo_name]["total"] += 1
        if is_merged:
            repo_stats[repo_name]["merged"] += 1

    print(f"Analysis complete!", file=sys.stderr)

    return {
        "team_prs": dict(team_prs),
        "daily_created": dict(daily_created),
        "daily_merged": dict(daily_merged),
        "daily_by_team": dict(daily_by_team),
        "repo_stats": dict(repo_stats),
    }


def generate_html_report(analysis: dict[str, Any], output_file: str) -> None:
    """Generate an HTML report with visualizations."""
    team_prs = analysis["team_prs"]
    daily_created = analysis["daily_created"]
    daily_merged = analysis["daily_merged"]
    daily_by_team = analysis["daily_by_team"]
    repo_stats = analysis["repo_stats"]

    # Calculate summary statistics (unique PRs)
    all_pr_ids = set()
    for prs in team_prs.values():
        for pr in prs:
            all_pr_ids.add(pr.get("pullRequestId"))

    total_unique_prs = len(all_pr_ids)

    # Count merged PRs
    total_merged = sum(stats["merged"] for stats in repo_stats.values())

    # Prepare data for charts
    dates = sorted(set(list(daily_created.keys()) + list(daily_merged.keys())))
    created_values = [daily_created.get(date, 0) for date in dates]
    merged_values = [daily_merged.get(date, 0) for date in dates]

    # Team summary data
    team_summary = []
    for team_name in sorted(team_prs.keys()):
        prs = team_prs[team_name]
        merged_count = sum(1 for pr in prs if pr.get("status") == "completed")

        team_summary.append({
            "team": team_name,
            "total": len(prs),
            "merged": merged_count,
            "merge_rate": f"{(merged_count / len(prs) * 100):.1f}%" if prs else "0%",
        })

    # Repository summary
    repo_summary = []
    for repo_name in sorted(repo_stats.keys()):
        stats = repo_stats[repo_name]
        teams = REPO_OWNERSHIP.get(repo_name, ["Unknown"])
        team_str = ", ".join(teams)

        repo_summary.append({
            "repo": repo_name,
            "teams": team_str,
            "total": stats["total"],
            "merged": stats["merged"],
            "merge_rate": f"{(stats['merged'] / stats['total'] * 100):.1f}%" if stats["total"] > 0 else "0%",
        })

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pull Request Report - Omnia Data Teams (v2)</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        .header p {{
            font-size: 1.2em;
            opacity: 0.95;
        }}

        .header .version {{
            margin-top: 10px;
            font-size: 0.9em;
            opacity: 0.8;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}

        .summary-card {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            text-align: center;
            transition: transform 0.2s;
        }}

        .summary-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
        }}

        .summary-card h3 {{
            color: #667eea;
            font-size: 1.1em;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}

        .summary-card .value {{
            font-size: 3em;
            font-weight: 700;
            color: #2d3748;
        }}

        .content {{
            padding: 40px;
        }}

        .section {{
            margin-bottom: 50px;
        }}

        .section h2 {{
            font-size: 2em;
            color: #2d3748;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }}

        .chart-container {{
            position: relative;
            height: 400px;
            margin: 30px 0;
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        th {{
            padding: 18px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
        }}

        td {{
            padding: 15px 18px;
            border-bottom: 1px solid #e2e8f0;
        }}

        tbody tr:hover {{
            background: #f7fafc;
        }}

        tbody tr:last-child td {{
            border-bottom: none;
        }}

        .pod-section {{
            margin-bottom: 40px;
            padding: 30px;
            background: #f8f9fa;
            border-radius: 12px;
        }}

        .pod-section h3 {{
            font-size: 1.5em;
            color: #667eea;
            margin-bottom: 20px;
        }}

        .badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .badge-success {{
            background: #48bb78;
            color: white;
        }}

        .badge-info {{
            background: #4299e1;
            color: white;
        }}

        .badge-warning {{
            background: #ed8936;
            color: white;
        }}

        .footer {{
            text-align: center;
            padding: 30px;
            background: #f8f9fa;
            color: #718096;
            font-size: 0.9em;
        }}

        .pr-link {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}

        .pr-link:hover {{
            text-decoration: underline;
        }}

        .note {{
            background: #fff5cc;
            border-left: 4px solid #ffc107;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}

        .note strong {{
            color: #d97706;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Pull Request Report</h1>
            <p>Omnia Data Teams | {START_DATE.strftime('%B %d, %Y')} - {END_DATE.strftime('%B %d, %Y')}</p>
            <div class="version">Version 2: Repository Ownership Attribution</div>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>Total PRs</h3>
                <div class="value">{total_unique_prs}</div>
            </div>
            <div class="summary-card">
                <h3>Merged PRs</h3>
                <div class="value">{total_merged}</div>
            </div>
            <div class="summary-card">
                <h3>Teams</h3>
                <div class="value">{len([t for t in team_prs.keys() if t != 'Unknown'])}</div>
            </div>
            <div class="summary-card">
                <h3>Merge Rate</h3>
                <div class="value">{(total_merged / total_unique_prs * 100):.1f}%</div>
            </div>
        </div>

        <div class="content">
            <div class="note">
                <strong>Note:</strong> This report uses repository ownership mapping for team attribution.
                PRs are assigned to teams based on which team(s) own the repository. Some PRs may appear
                in multiple team reports if the repository is co-owned.
            </div>

            <div class="section">
                <h2>Daily Pull Request Activity</h2>
                <div class="chart-container">
                    <canvas id="dailyChart"></canvas>
                </div>
            </div>

            <div class="section">
                <h2>Repository Summary</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Repository</th>
                            <th>Owning Team(s)</th>
                            <th>Total PRs</th>
                            <th>Merged PRs</th>
                            <th>Merge Rate</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Add repository summary rows
    for repo_data in sorted(repo_summary, key=lambda x: x["total"], reverse=True):
        html += f"""
                        <tr>
                            <td><strong>{repo_data['repo']}</strong></td>
                            <td><span class="badge badge-info">{repo_data['teams']}</span></td>
                            <td>{repo_data['total']}</td>
                            <td>{repo_data['merged']}</td>
                            <td><span class="badge badge-success">{repo_data['merge_rate']}</span></td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </div>

            <div class="section">
                <h2>Team Summary</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Team</th>
                            <th>Total PRs</th>
                            <th>Merged PRs</th>
                            <th>Merge Rate</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Add team summary rows
    for team_data in sorted(team_summary, key=lambda x: x["total"], reverse=True):
        if team_data["team"] == "Unknown":
            continue
        html += f"""
                        <tr>
                            <td><strong>{team_data['team']}</strong></td>
                            <td>{team_data['total']}</td>
                            <td>{team_data['merged']}</td>
                            <td><span class="badge badge-success">{team_data['merge_rate']}</span></td>
                        </tr>
"""

    html += """
                    </tbody>
                </table>
            </div>
"""

    # Add POD sections with detailed PR listings
    for pod_name, teams in PODS.items():
        pod_teams_with_prs = [team for team in teams if team in team_prs and team_prs[team]]

        if not pod_teams_with_prs:
            continue

        html += f"""
            <div class="section">
                <h2>{pod_name} POD</h2>
"""

        for team_name in pod_teams_with_prs:
            prs = team_prs[team_name]
            merged_count = sum(1 for pr in prs if pr.get("status") == "completed")

            html += f"""
                <div class="pod-section">
                    <h3>{team_name} <span class="badge badge-info">{len(prs)} PRs</span> <span class="badge badge-success">{merged_count} merged</span></h3>
                    <table>
                        <thead>
                            <tr>
                                <th>PR ID</th>
                                <th>Title</th>
                                <th>Author</th>
                                <th>Repository</th>
                                <th>Created</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
"""

            # Sort PRs by creation date (newest first)
            sorted_prs = sorted(prs, key=lambda x: x.get("creationDate", ""), reverse=True)

            for pr in sorted_prs[:50]:  # Limit to 50 PRs per team
                pr_id = pr.get("pullRequestId", "N/A")
                title = pr.get("title", "No title")[:80]
                author = pr.get("createdBy", {}).get("displayName", "Unknown")
                repo = pr.get("_repository_name", pr.get("repository", {}).get("name", "Unknown"))
                created = parse_date(pr.get("creationDate"))
                created_str = created.strftime("%Y-%m-%d") if created else "N/A"
                status = pr.get("status", "unknown")

                status_badge = "badge-success" if status == "completed" else "badge-info"

                pr_url = pr.get("url", "")
                # Convert API URL to web URL
                web_url = pr_url.replace("_apis/git/repositories", "_git").replace("/pullRequests/", "/pullrequest/") if pr_url else "#"

                html += f"""
                            <tr>
                                <td><a href="{web_url}" class="pr-link" target="_blank">#{pr_id}</a></td>
                                <td>{title}</td>
                                <td>{author}</td>
                                <td>{repo}</td>
                                <td>{created_str}</td>
                                <td><span class="badge {status_badge}">{status}</span></td>
                            </tr>
"""

            html += """
                        </tbody>
                    </table>
                </div>
"""

        html += """
            </div>
"""

    # Add JavaScript for charts
    html += f"""
        </div>

        <div class="footer">
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Data source: Azure DevOps | Organization: symphonyvsts | Project: Audit Cortex 2</p>
            <p>Team attribution: Repository ownership mapping</p>
        </div>
    </div>

    <script>
        // Daily PR Activity Chart
        const dailyCtx = document.getElementById('dailyChart').getContext('2d');
        new Chart(dailyCtx, {{
            type: 'line',
            data: {{
                labels: {json.dumps(dates)},
                datasets: [
                    {{
                        label: 'PRs Created',
                        data: {json.dumps(created_values)},
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4,
                        fill: true
                    }},
                    {{
                        label: 'PRs Merged',
                        data: {json.dumps(merged_values)},
                        borderColor: '#48bb78',
                        backgroundColor: 'rgba(72, 187, 120, 0.1)',
                        tension: 0.4,
                        fill: true
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'top',
                        labels: {{
                            font: {{
                                size: 14,
                                weight: '600'
                            }}
                        }}
                    }},
                    title: {{
                        display: true,
                        text: 'Daily Pull Request Trends',
                        font: {{
                            size: 18,
                            weight: '700'
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        display: true,
                        title: {{
                            display: true,
                            text: 'Date',
                            font: {{
                                weight: '600'
                            }}
                        }},
                        ticks: {{
                            maxRotation: 45,
                            minRotation: 45
                        }}
                    }},
                    y: {{
                        display: true,
                        title: {{
                            display: true,
                            text: 'Number of PRs',
                            font: {{
                                weight: '600'
                            }}
                        }},
                        beginAtZero: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    # Write to file
    with open(output_file, "w") as f:
        f.write(html)

    print(f"\nReport generated: {output_file}", file=sys.stderr)


def main():
    """Main execution function."""
    print("=" * 80, file=sys.stderr)
    print("Pull Request Report Generator v2 (Repository Ownership Attribution)", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    print(f"Organization: symphonyvsts", file=sys.stderr)
    print(f"Project: Audit Cortex 2", file=sys.stderr)
    print(f"Date Range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}", file=sys.stderr)
    print(f"Repositories: {len(REPOSITORIES)}", file=sys.stderr)
    print("=" * 80, file=sys.stderr)

    # Fetch PRs from all repositories
    all_prs = []

    for repo in REPOSITORIES:
        prs = fetch_prs_for_repo(repo)
        all_prs.extend(prs)

    print(f"\nTotal PRs fetched: {len(all_prs)}", file=sys.stderr)

    # Filter by date range
    filtered_prs = filter_prs_by_date(all_prs)
    print(f"PRs in date range: {len(filtered_prs)}", file=sys.stderr)

    # Analyze PRs
    analysis = analyze_prs(filtered_prs)

    # Generate HTML report
    output_file = f"/Users/sdandey/Documents/code/triagent/pr_report_v2_{END_DATE.strftime('%Y%m%d')}.html"
    generate_html_report(analysis, output_file)

    print("\n" + "=" * 80, file=sys.stderr)
    print("Report generation complete!", file=sys.stderr)
    print("=" * 80, file=sys.stderr)


if __name__ == "__main__":
    main()
