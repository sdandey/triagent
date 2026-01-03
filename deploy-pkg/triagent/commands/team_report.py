"""Team report command - generates iteration status reports for Azure DevOps teams."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from triagent.config import ConfigManager

# ADO Configuration
ORG_URL = "https://dev.azure.com/symphonyvsts"
PROJECT = "Audit Cortex 2"

# Team area path mappings
TEAM_AREA_PATHS = {
    "alpha": "Audit Cortex 2\\Omnia Data\\Omnia Data Management\\Data Acquisition and Preparation\\Alpha",
    "beta": "Audit Cortex 2\\Omnia Data\\Omnia Data Management\\Data Acquisition and Preparation\\Beta",
    "megatron": "Audit Cortex 2\\Omnia Data\\Omnia Data Management\\Data Acquisition and Preparation\\Megatron",
    "delta": "Audit Cortex 2\\Omnia Data\\Omnia Data Management\\Data Management and Activation\\Delta",
    "gamma": "Audit Cortex 2\\Omnia Data\\Omnia Data Management\\Data Management and Activation\\Gamma",
    "skyrockets": "Audit Cortex 2\\Omnia Data\\Omnia Data Management\\Data Management and Activation\\Skyrockets",
    "giga": "Audit Cortex 2\\Omnia Data\\Omnia Data Automation\\Data In Use\\Giga",
    "kilo": "Audit Cortex 2\\Omnia Data\\Omnia Data Automation\\Data In Use\\Kilo",
    "tera": "Audit Cortex 2\\Omnia Data\\Omnia Data Automation\\Data In Use\\Tera",
    "peta": "Audit Cortex 2\\Omnia Data\\Omnia Data Automation\\Data In Use\\Peta",
    "jupiter": "Audit Cortex 2\\Omnia Data\\Omnia Data Automation\\Omnia JE\\Jupiter",
    "saturn": "Audit Cortex 2\\Omnia Data\\Omnia Data Automation\\Omnia JE\\Saturn",
    "neptune": "Audit Cortex 2\\Omnia Data\\Omnia Data Automation\\Omnia JE\\Neptune",
    "justice league": "Audit Cortex 2\\Omnia Data\\Omnia Data Automation\\Omnia JE\\Justice League",
    "exa": "Audit Cortex 2\\Omnia Data\\Omnia Data Automation\\Omnia JE\\Exa",
    "utopia": "Audit Cortex 2\\Omnia Data\\Omnia Data Automation\\Omnia JE\\Utopia",
}

# POD mappings
PODS = {
    "Data Acquisition and Preparation": ["Alpha", "Beta", "Megatron"],
    "Data Management and Activation": ["Delta", "Gamma", "Skyrockets"],
    "Omnia JE": ["Exa", "Jupiter", "Justice League", "Neptune", "Peta", "Saturn", "Utopia"],
    "Data In Use": ["Giga", "Kilo", "Tera"],
}


def run_az_command(command: str, console: Console | None = None) -> Any:
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
            if console:
                console.print(f"[dim]Command failed: {result.stderr[:200]}[/dim]")
            return []
    except subprocess.TimeoutExpired:
        if console:
            console.print("[yellow]Command timed out[/yellow]")
        return []
    except json.JSONDecodeError:
        return []
    except Exception:
        return []


def get_current_iteration(team_name: str, console: Console) -> tuple[str, str] | None:
    """Get the current iteration path for a team."""
    command = (
        f'az boards iteration team list --team "{team_name}" '
        f'--project "{PROJECT}" --organization {ORG_URL} --output json 2>/dev/null'
    )
    iterations = run_az_command(command, console)

    if not iterations:
        return None

    for iteration in iterations:
        time_frame = iteration.get("attributes", {}).get("timeFrame", "")
        if time_frame == "current":
            path = iteration.get("path", "")
            name = iteration.get("name", "")
            return (path, name)

    return None


def get_team_members(team_name: str, console: Console) -> list[dict[str, Any]]:
    """Get team member list with admin status."""
    command = (
        f'az devops team list-member --team "{team_name}" '
        f'--project "{PROJECT}" --organization {ORG_URL} --output json 2>/dev/null'
    )
    members = run_az_command(command, console)
    return members if members else []


def query_work_items(
    iteration_path: str,
    area_path: str,
    console: Console,
) -> list[dict[str, Any]]:
    """Query all work items for an iteration and area path."""
    # Escape backslashes for WIQL
    escaped_area = area_path.replace("\\", "\\\\")
    escaped_iter = iteration_path.replace("\\", "\\\\")

    wiql = (
        f"SELECT [System.Id], [System.Title], [System.State], "
        f"[System.WorkItemType], [System.AssignedTo], "
        f"[Microsoft.VSTS.Common.Priority], [Microsoft.VSTS.Scheduling.StoryPoints] "
        f"FROM WorkItems "
        f"WHERE [System.IterationPath] = '{escaped_iter}' "
        f"AND [System.AreaPath] UNDER '{escaped_area}' "
        f"ORDER BY [System.WorkItemType], [System.State]"
    )

    command = (
        f'az boards query --wiql "{wiql}" '
        f'--project "{PROJECT}" --organization {ORG_URL} --output json 2>/dev/null'
    )
    work_items = run_az_command(command, console)
    return work_items if work_items else []


def get_pod_for_team(team_name: str) -> str:
    """Get the POD name for a team."""
    title_team = team_name.title()
    for pod_name, teams in PODS.items():
        if title_team in teams:
            return pod_name
    return "Unknown"


def categorize_work_items(work_items: list[dict[str, Any]]) -> dict[str, list[dict]]:
    """Categorize work items by type."""
    categories: dict[str, list[dict]] = {
        "Task": [],
        "Bug": [],
        "Product Backlog Item": [],
        "Other": [],
    }

    for item in work_items:
        fields = item.get("fields", {})
        wi_type = fields.get("System.WorkItemType", "Other")

        parsed = {
            "id": item.get("id"),
            "title": fields.get("System.Title", "")[:80],
            "state": fields.get("System.State", ""),
            "assigned_to": fields.get("System.AssignedTo", {}).get("displayName", "Unassigned"),
            "priority": fields.get("Microsoft.VSTS.Common.Priority", 0),
            "story_points": fields.get("Microsoft.VSTS.Scheduling.StoryPoints", 0),
        }

        if wi_type in categories:
            categories[wi_type].append(parsed)
        else:
            categories["Other"].append(parsed)

    return categories


def count_by_state(items: list[dict]) -> dict[str, int]:
    """Count items by state."""
    return dict(Counter(item["state"] for item in items))


def generate_progress_bar(done: int, total: int, width: int = 20) -> str:
    """Generate an ASCII progress bar."""
    if total == 0:
        return "░" * width + " 0%"
    percentage = (done / total) * 100
    filled = int((done / total) * width)
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {percentage:.0f}%"


def identify_roles(
    members: list[dict[str, Any]],
    tasks: list[dict],
) -> dict[str, list[dict]]:
    """Identify team roles based on task assignments and admin status."""
    roles: dict[str, list[dict]] = {
        "admins": [],
        "developers": [],
        "qa": [],
        "other": [],
    }

    # Task patterns for role identification
    qa_patterns = ["[QA Task]", "Test Case", "Defect Testing", "UI Testing"]
    dev_patterns = ["[Dev-BE]", "[Dev-UI]", "[Dev UI]", "Implementation", "PR Creation", "Code Review"]

    # Get all unique assignees from tasks
    assignees_with_dev_tasks: set[str] = set()
    assignees_with_qa_tasks: set[str] = set()

    for task in tasks:
        title = task.get("title", "")
        assignee = task.get("assigned_to", "")

        if any(p.lower() in title.lower() for p in dev_patterns):
            assignees_with_dev_tasks.add(assignee)
        if any(p.lower() in title.lower() for p in qa_patterns):
            assignees_with_qa_tasks.add(assignee)

    # Categorize members
    for member in members:
        identity = member.get("identity", {})
        name = identity.get("displayName", "Unknown")
        email = identity.get("uniqueName", "")
        is_admin = member.get("isTeamAdmin", False)

        member_info = {"name": name, "email": email}

        if is_admin:
            roles["admins"].append(member_info)
        elif name in assignees_with_qa_tasks:
            roles["qa"].append(member_info)
        elif name in assignees_with_dev_tasks:
            roles["developers"].append(member_info)
        else:
            roles["other"].append(member_info)

    return roles


def generate_report_markdown(
    team_name: str,
    iteration_path: str,
    iteration_name: str,
    members: list[dict],
    work_items: dict[str, list[dict]],
    roles: dict[str, list[dict]],
) -> str:
    """Generate the full markdown report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pod_name = get_pod_for_team(team_name)

    # Count work items by state
    task_states = count_by_state(work_items["Task"])
    bug_states = count_by_state(work_items["Bug"])
    pbi_states = count_by_state(work_items["Product Backlog Item"])

    # Calculate totals
    total_tasks = len(work_items["Task"])
    done_tasks = task_states.get("Done", 0) + task_states.get("Closed", 0)

    total_bugs = len(work_items["Bug"])
    done_bugs = bug_states.get("Done", 0) + bug_states.get("Closed", 0)

    total_pbis = len(work_items["Product Backlog Item"])
    done_pbis = pbi_states.get("Done", 0) + pbi_states.get("Closed", 0)

    report = f"""# {team_name.title()} Team - {iteration_name} Status Report

**Team:** {team_name.title()}
**POD:** {pod_name}
**Organization:** symphonyvsts / {PROJECT}
**Current Iteration:** {iteration_path}
**Report Generated:** {now}

---

## Executive Summary

| Metric | Count |
|--------|-------|
| Total Work Items | {total_tasks + total_bugs + total_pbis} |
| Tasks Completed | {done_tasks} / {total_tasks} ({(done_tasks/total_tasks*100 if total_tasks else 0):.0f}%) |
| Bugs Resolved | {done_bugs} / {total_bugs} ({(done_bugs/total_bugs*100 if total_bugs else 0):.0f}%) |
| PBIs Done | {done_pbis} / {total_pbis} ({(done_pbis/total_pbis*100 if total_pbis else 0):.0f}%) |

---

## Team Structure ({len(members)} Members)

### Team Admins
"""

    for admin in roles["admins"]:
        report += f"- {admin['name']} ({admin['email']})\n"

    if not roles["admins"]:
        report += "- No admins identified\n"

    report += "\n### Developers\n"
    for dev in roles["developers"]:
        report += f"- {dev['name']}\n"

    if not roles["developers"]:
        report += "- No developers identified from task assignments\n"

    report += "\n### QA Engineers\n"
    for qa in roles["qa"]:
        report += f"- {qa['name']}\n"

    if not roles["qa"]:
        report += "- No QA engineers identified from task assignments\n"

    report += f"""
---

## Work Item Summary

### Tasks ({total_tasks} Total)

| State | Count | Percentage |
|-------|-------|------------|
"""
    for state, count in sorted(task_states.items()):
        pct = count / total_tasks * 100 if total_tasks else 0
        report += f"| {state} | {count} | {pct:.0f}% |\n"

    report += f"""
### Bugs ({total_bugs} Total)

| State | Count |
|-------|-------|
"""
    for state, count in sorted(bug_states.items()):
        report += f"| {state} | {count} |\n"

    report += f"""
### Product Backlog Items ({total_pbis} Total)

| State | Count |
|-------|-------|
"""
    for state, count in sorted(pbi_states.items()):
        report += f"| {state} | {count} |\n"

    # Active bugs section
    active_bugs = [b for b in work_items["Bug"] if b["state"] not in ["Done", "Closed"]]
    if active_bugs:
        report += """
---

## Active Bugs (Not Closed)

| ID | Title | Assignee | Priority |
|----|-------|----------|----------|
"""
        for bug in sorted(active_bugs, key=lambda x: x.get("priority", 99)):
            report += f"| {bug['id']} | {bug['title'][:50]}... | {bug['assigned_to']} | P{bug['priority']} |\n"

    # Progress visualization
    report += f"""
---

## Progress Visualization

```
Tasks:    {generate_progress_bar(done_tasks, total_tasks)} ({done_tasks}/{total_tasks})
Bugs:     {generate_progress_bar(done_bugs, total_bugs)} ({done_bugs}/{total_bugs})
PBIs:     {generate_progress_bar(done_pbis, total_pbis)} ({done_pbis}/{total_pbis})
```

---

## Risks & Blockers

"""

    # Find blocked items
    blocked_items = []
    for wi_type, items in work_items.items():
        for item in items:
            if "blocked" in item["state"].lower():
                blocked_items.append((wi_type, item))

    if blocked_items:
        report += "### Blocked Items\n"
        for wi_type, item in blocked_items:
            report += f"- [{wi_type}] #{item['id']}: {item['title'][:60]}... (Assigned: {item['assigned_to']})\n"
    else:
        report += "- No blocked items\n"

    # High priority unassigned bugs
    unassigned_p1_bugs = [
        b for b in work_items["Bug"]
        if b["assigned_to"] == "Unassigned" and b.get("priority", 99) == 1
    ]
    if unassigned_p1_bugs:
        report += "\n### Unassigned P1 Bugs\n"
        for bug in unassigned_p1_bugs:
            report += f"- #{bug['id']}: {bug['title'][:60]}...\n"

    report += """
---

*Report generated by Triagent | Azure DevOps Automation*
"""

    return report


def save_report_to_file(report: str, team_name: str, console: Console) -> None:
    """Save the report to a markdown file."""
    # Create reports directory if not exists
    reports_dir = Path("docs/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    filename = f"{team_name.lower().replace(' ', '-')}-report-{timestamp}.md"
    filepath = reports_dir / filename

    # Write file
    filepath.write_text(report)

    console.print()
    console.print(
        Panel(
            f"[green]Report saved to:[/green] {filepath}",
            border_style="green",
        )
    )


def team_report_command(
    console: Console,
    config_manager: ConfigManager,
    args: list[str] | None = None,
) -> None:
    """Generate team iteration status report.

    Args:
        console: Rich console for output
        config_manager: Config manager instance
        args: Command arguments (team name, --save flag)
    """
    # Parse arguments
    team_name: str | None = None
    save_to_file = False

    if args:
        for arg in args:
            if arg == "--save":
                save_to_file = True
            elif not arg.startswith("-"):
                if team_name is None:
                    team_name = arg
                else:
                    team_name = f"{team_name} {arg}"  # Handle multi-word team names

    # Prompt for team if not provided
    if not team_name:
        console.print()
        console.print("[bold]Available teams:[/bold]")
        for name in sorted(TEAM_AREA_PATHS.keys()):
            console.print(f"  - {name.title()}")
        console.print()
        team_name = console.input("[cyan]Enter team name: [/cyan]").strip()

    team_key = team_name.lower()

    # Validate team
    if team_key not in TEAM_AREA_PATHS:
        console.print(f"[red]Error: Unknown team '{team_name}'[/red]")
        console.print("[bold]Available teams:[/bold]")
        for name in sorted(TEAM_AREA_PATHS.keys()):
            console.print(f"  - {name.title()}")
        return

    area_path = TEAM_AREA_PATHS[team_key]

    # Fetch data with progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        # Get current iteration
        progress.add_task("Fetching current iteration...", total=None)
        iteration_info = get_current_iteration(team_name, console)

        if not iteration_info:
            console.print(f"[red]Error: Could not find current iteration for team '{team_name}'[/red]")
            return

        iteration_path, iteration_name = iteration_info

        # Get team members
        progress.add_task("Fetching team members...", total=None)
        members = get_team_members(team_name, console)

        # Query work items
        progress.add_task("Querying work items...", total=None)
        raw_work_items = query_work_items(iteration_path, area_path, console)

    # Process work items
    work_items = categorize_work_items(raw_work_items)

    # Identify roles
    roles = identify_roles(members, work_items["Task"])

    # Generate report
    report = generate_report_markdown(
        team_name,
        iteration_path,
        iteration_name,
        members,
        work_items,
        roles,
    )

    # Display report
    console.print()
    from rich.markdown import Markdown
    console.print(Markdown(report))

    # Save to file if requested
    if save_to_file:
        save_report_to_file(report, team_name, console)
