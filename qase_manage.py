"""
Qase API v1 - Manage test suites and test cases in a Qase project.

Commands:
    list-suites    List all suites in the project
    list-cases     List all test cases, optionally filtered by suite
    info-suite     Show full details of a suite by ID
    info-case      Show full details of a test case by ID
    create-suite   Create a test suite (skips if title already exists)
    create-case    Create a test case  (skips if title already exists)
    set-result     Pass or fail a test case (creates a run, sets result, completes it)

All arguments can appear in any order on the command line.

Usage examples:
    python qase_manage.py list-suites --project SLES
    python qase_manage.py list-cases  --project SLES --id 10

    python qase_manage.py info-suite  --project SLES --id 5
    python qase_manage.py info-case   --project SLES --id 42

    python qase_manage.py create-suite --project SLES --title "Systemd MCP Tests"
    python qase_manage.py create-suite --project SLES --title "Unit Tests" --parent-id 10

    python qase_manage.py create-case --project SLES --title "Verify service starts" \
        --suite-id 10 --priority high --severity critical \
        --description "Check systemd service starts" \
        --preconditions "Service is installed" \
        --expected "Service is active and running"

    python qase_manage.py set-result --project SLES --id 42 --status passed
    python qase_manage.py set-result --project SLES --id 42 --status failed \
        --comment "Service did not start"

Environment variable:
    QASE_API_TOKEN  - your Qase API token (or pass via --token anywhere in the command)
"""

import argparse
import os
import sys
import requests

BASE_URL = "https://api.qase.io/v1"

PRIORITY_MAP = {"undefined": 0, "low": 1, "medium": 2, "high": 3}
SEVERITY_MAP = {"undefined": 0, "blocker": 1, "critical": 2, "major": 3,
                "normal": 4, "minor": 5, "trivial": 6}
PRIORITY_LABELS = {v: k for k, v in PRIORITY_MAP.items()}
SEVERITY_LABELS = {v: k for k, v in SEVERITY_MAP.items()}


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def get_headers(token):
    return {
        "Token": token,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def api_get(token, path, params=None):
    response = requests.get(f"{BASE_URL}{path}", headers=get_headers(token), params=params)
    response.raise_for_status()
    return response.json()


def api_post(token, path, payload):
    response = requests.post(f"{BASE_URL}{path}", json=payload, headers=get_headers(token))
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Suite operations
# ---------------------------------------------------------------------------

def get_existing_suites(token, project):
    """Return {title_lower: suite_id} for all suites in the project."""
    data = api_get(token, f"/suite/{project}", params={"limit": 100})
    return {s["title"].lower(): s["id"] for s in data["result"]["entities"]}


def list_suites(token, project):
    """Print all suites in the project."""
    data = api_get(token, f"/suite/{project}", params={"limit": 100})
    suites = data["result"]["entities"]
    if not suites:
        print("No suites found.")
        return
    print(f"\n{'ID':<8} {'Parent ID':<12} Title")
    print("─" * 50)
    for s in suites:
        parent = str(s.get("parent_id") or "-")
        print(f"{s['id']:<8} {parent:<12} {s['title']}")
    print()


def info_suite(token, project, suite_id):
    """Print full details of a single suite."""
    data = api_get(token, f"/suite/{project}/{suite_id}")
    s = data["result"]
    print(f"Suite details")
    print("-" * 40)
    print(f"  ID          : {s['id']}")
    print(f"  Title       : {s['title']}")
    print(f"  Parent ID   : {s.get('parent_id') or '-'}")
    print(f"  Description : {s.get('description') or '-'}")
    print(f"  Cases count : {s.get('cases_count', '-')}")
    print(f"  Created     : {s.get('created_at', '-')}")
    print(f"  Updated     : {s.get('updated_at', '-')}")
    print()


def create_suite(token, project, title, description=None, parent_id=None):
    """Create a suite only if one with the same title does not already exist."""
    existing = get_existing_suites(token, project)

    if title.lower() in existing:
        suite_id = existing[title.lower()]
        print(f"Suite already exists: '{title}' (ID: {suite_id}) - skipping")
        return suite_id

    payload = {"title": title}
    if description:
        payload["description"] = description
    if parent_id:
        payload["parent_id"] = parent_id

    data = api_post(token, f"/suite/{project}", payload)
    suite_id = data["result"]["id"]
    print(f"Created suite: '{title}' (ID: {suite_id})")
    return suite_id


# ---------------------------------------------------------------------------
# Case operations
# ---------------------------------------------------------------------------

def get_existing_cases(token, project, suite_id=None):
    """Return {title_lower: case_id} for all cases, optionally filtered by suite."""
    params = {"limit": 100}
    if suite_id:
        params["suite_id"] = suite_id
    data = api_get(token, f"/case/{project}", params=params)
    return {c["title"].lower(): c["id"] for c in data["result"]["entities"]}


def list_cases(token, project, suite_id=None):
    """Print all test cases in the project, optionally filtered by suite."""
    params = {"limit": 100}
    if suite_id:
        params["suite_id"] = suite_id
    data = api_get(token, f"/case/{project}", params=params)
    cases = data["result"]["entities"]
    if not cases:
        print("No test cases found.")
        return
    print(f"\n{'ID':<8} {'Suite ID':<12} {'Priority':<12} Title")
    print("─" * 60)
    for c in cases:
        suite = str(c.get("suite_id") or "-")
        priority = PRIORITY_LABELS.get(c.get("priority", 0), "undefined")
        print(f"{c['id']:<8} {suite:<12} {priority:<12} {c['title']}")
    print()


def info_case(token, project, case_id):
    """Print full details of a single test case."""
    data = api_get(token, f"/case/{project}/{case_id}")
    c = data["result"]
    print(f"\nTest case details")
    print("-" * 40)
    print(f"  ID            : {c['id']}")
    print(f"  Title         : {c['title']}")
    print(f"  Suite ID      : {c.get('suite_id') or '-'}")
    print(f"  Priority      : {PRIORITY_LABELS.get(c.get('priority', 0), '-')}")
    print(f"  Severity      : {SEVERITY_LABELS.get(c.get('severity', 0), '-')}")
    print(f"  Description   : {c.get('description') or '-'}")
    print(f"  Preconditions : {c.get('preconditions') or '-'}")
    print(f"  Expected      : {c.get('expected_result') or '-'}")
    print(f"  Created       : {c.get('created_at', '-')}")
    print(f"  Updated       : {c.get('updated_at', '-')}")
    if c.get("steps"):
        print(f"  Steps:")
        for i, step in enumerate(c["steps"], 1):
            print(f"    {i}. {step.get('action', '')} → {step.get('expected_result', '')}")
    print()


def create_case(token, project, title, suite_id=None, priority="undefined",
                severity="undefined", description=None, preconditions=None, expected=None):
    """Create a test case only if one with the same title does not already exist."""
    existing = get_existing_cases(token, project, suite_id)

    if title.lower() in existing:
        case_id = existing[title.lower()]
        print(f"Case already exists: '{title}' (ID: {case_id}) - skipping")
        return case_id

    payload = {
        "title": title,
        "priority": PRIORITY_MAP.get(priority, 0),
        "severity": SEVERITY_MAP.get(severity, 0),
    }
    if suite_id:
        payload["suite_id"] = suite_id
    if description:
        payload["description"] = description
    if preconditions:
        payload["preconditions"] = preconditions
    if expected:
        payload["expected_result"] = expected

    data = api_post(token, f"/case/{project}", payload)
    case_id = data["result"]["id"]
    print(f"Created case: '{title}' (ID: {case_id})")
    return case_id


# ---------------------------------------------------------------------------
# Result operations
# ---------------------------------------------------------------------------

def set_result(token, project, case_id, status, comment=None):
    """
    Create a throwaway test run for the given case, set it passed/failed,
    then mark the run complete - all in one go.
    """
    # 1. Create a run containing just this case
    run_payload = {"title": f"Result for case #{case_id}", "cases": [case_id]}
    run_data = api_post(token, f"/run/{project}", run_payload)
    run_id = run_data["result"]["id"]
    print(f"Created run #{run_id} for case #{case_id}")

    # 2. Set the result
    result_payload = {"case_id": case_id, "status": status}
    if comment:
        result_payload["comment"] = comment
    api_post(token, f"/result/{project}/{run_id}", result_payload)
    print(f"Case #{case_id} marked as {status.upper()}")

    # 3. Complete the run
    api_post(token, f"/run/{project}/{run_id}/complete", {})
    print(f"Run #{run_id} completed")


# ---------------------------------------------------------------------------
# CLI - two-phase parsing for order-independent global args
# ---------------------------------------------------------------------------

def build_parser():
    parser = argparse.ArgumentParser(
        description="Manage Qase test suites and cases via API v1.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # list-suites
    subparsers.add_parser("list-suites", help="List all suites in the project")

    # list-cases
    lc = subparsers.add_parser("list-cases", help="List all test cases in the project")
    lc.add_argument("--id", type=int, help="Filter by suite ID")

    # info-suite
    is_ = subparsers.add_parser("info-suite", help="Show full details of a suite")
    is_.add_argument("--id", type=int, required=True, help="Suite ID")

    # info-case
    ic = subparsers.add_parser("info-case", help="Show full details of a test case")
    ic.add_argument("--id", type=int, required=True, help="Test case ID")

    # create-suite
    cs = subparsers.add_parser("create-suite", help="Create a test suite")
    cs.add_argument("--title", required=True, help="Suite title")
    cs.add_argument("--description", help="Suite description")
    cs.add_argument("--parent-id", type=int, help="Parent suite ID (for nesting)")

    # create-case
    cc = subparsers.add_parser("create-case", help="Create a test case")
    cc.add_argument("--title", required=True, help="Test case title")
    cc.add_argument("--suite-id", type=int, help="Suite ID to place the case in")
    cc.add_argument("--priority", choices=PRIORITY_MAP.keys(), default="undefined")
    cc.add_argument("--severity", choices=SEVERITY_MAP.keys(), default="undefined")
    cc.add_argument("--description", help="Test case description")
    cc.add_argument("--preconditions", help="Preconditions text")
    cc.add_argument("--expected", help="Expected result text")

    # set-result
    sr = subparsers.add_parser("set-result", help="Pass or fail a test case")
    sr.add_argument("--id", type=int, required=True, help="Test case ID")
    sr.add_argument("--status", required=True, choices=["passed", "failed"],
                    help="Result status")
    sr.add_argument("--comment", help="Optional comment")

    return parser


def main():
    # Phase 1: extract --project and --token from anywhere in the command line
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--project")
    pre.add_argument("--token", default=os.environ.get("QASE_API_TOKEN"))
    pre_args, remaining = pre.parse_known_args()

    # Phase 2: parse the subcommand and its specific args
    parser = build_parser()
    args = parser.parse_args(remaining, namespace=pre_args)

    if not args.project:
        parser.error("--project is required")
    if not args.token:
        parser.error("--token is required (or set QASE_API_TOKEN env var)")

    try:
        if args.command == "list-suites":
            list_suites(args.token, args.project)

        elif args.command == "list-cases":
            list_cases(args.token, args.project, suite_id=args.id)

        elif args.command == "info-suite":
            info_suite(args.token, args.project, args.id)

        elif args.command == "info-case":
            info_case(args.token, args.project, args.id)

        elif args.command == "create-suite":
            create_suite(args.token, args.project, args.title,
                         description=args.description, parent_id=args.parent_id)

        elif args.command == "create-case":
            create_case(args.token, args.project, args.title,
                        suite_id=args.suite_id, priority=args.priority,
                        severity=args.severity, description=args.description,
                        preconditions=args.preconditions, expected=args.expected)

        elif args.command == "set-result":
            set_result(args.token, args.project, args.id, args.status,
                       comment=args.comment)

    except requests.exceptions.HTTPError as e:
        print(f"API error {e.response.status_code}: {e.response.text}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
