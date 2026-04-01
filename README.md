# qase_manage.py

A command-line tool for managing test suites and test cases in a [Qase](https://qase.io) project via the Qase API v1.

## Requirements

- Python 3.6+
- `requests` library

```bash
pip install requests
```

## Authentication

The script requires a Qase API token. You can provide it in two ways:

**As an environment variable (recommended):**
```bash
export QASE_API_TOKEN=your_token_here
```

**Or inline with any command:**
```bash
python qase_manage.py <command> --project XXX --token your_token_here
```

The `--project` and `--token` arguments can appear anywhere in the command line, in any order.

---

## Commands

### `list-suites`
List all test suites in the project.

```bash
python qase_manage.py list-suites --project XXX
```

**Output:**
```
ID       Parent ID    Title
--------------------------------------------------
5        -            Tests
6        5            Unit Tests
7        5            Integration Tests
```

---

### `list-cases`
List all test cases in the project. Optionally filter by suite.

```bash
# All cases
python qase_manage.py list-cases --project XXX

# Cases in a specific suite
python qase_manage.py list-cases --project XXX --id 6
```

| Argument | Required | Description        |
|----------|----------|--------------------|
| `--id`   | No       | Filter by suite ID |

**Output:**
```
ID       Suite ID     Priority     Title
------------------------------------------------------------
42       6            high         Unit test suite passes
43       7            high         Integrated test suite passes
```

---

### `info-suite`
Show full details of a single suite.

```bash
python qase_manage.py info-suite --project XXX --id 5
```

| Argument | Required | Description |
|----------|----------|-------------|
| `--id`   | Yes      | Suite ID    |

**Output:**
```
Suite details
----------------------------------------
  ID          : 5
  Title       : Tests
  Parent ID   : -
  Description : Top-level suite for all whatever tests
  Cases count : 4
  Created     : 2024-01-15T10:00:00Z
  Updated     : 2024-01-15T10:00:00Z
```

---

### `info-case`
Show full details of a single test case, including steps.

```bash
python qase_manage.py info-case --project XXX --id 42
```

| Argument | Required | Description  |
|----------|----------|--------------|
| `--id`   | Yes      | Test case ID |

**Output:**
```
Test case details
----------------------------------------
  ID            : 42
  Title         : Unit test suite passes
  Suite ID      : 6
  Priority      : high
  Severity      : critical
  Description   : Run unit tests and verify all tests pass
  Preconditions : whatever is installed and bats is available
  Expected      : All bats tests exit with code 0
  Created       : 2024-01-15T10:00:00Z
  Updated       : 2024-01-15T10:00:00Z
  Steps:
    1. Run unit tests -> TAP output shows all tests passing
```

---

### `create-suite`
Create a new test suite. Skips silently if a suite with the same title already exists.

```bash
# Top-level suite
python qase_manage.py create-suite --project XXX --title "Tests"

# Nested suite under a parent
python qase_manage.py create-suite --project XX --title "Unit Tests" --parent-id 5
```

| Argument        | Required | Description                   |
|-----------------|----------|-------------------------------|
| `--title`       | Yes      | Suite title                   |
| `--description` | No       | Suite description             |
| `--parent-id`   | No       | Parent suite ID (for nesting) |

---

### `create-case`
Create a new test case. Skips silently if a case with the same title already exists in the suite.

```bash
# Minimal
python qase_manage.py create-case --project XXX --title "Verify service starts"

# Full
python qase_manage.py create-case --project XXX \
    --title "Verify service starts" \
    --suite-id 6 \
    --priority high \
    --severity critical \
    --description "Check whatever service starts correctly" \
    --preconditions "Service is installed" \
    --expected "Service is active and running"
```

| Argument          | Required | Description                                                                         |
|-------------------|----------|-------------------------------------------------------------------------------------|
| `--title`         | Yes      | Test case title                                                                     |
| `--suite-id`      | No       | Suite ID to place the case in                                                       |
| `--priority`      | No       | `undefined` (default), `low`, `medium`, `high`                                      |
| `--severity`      | No       | `undefined` (default), `blocker`, `critical`, `major`, `normal`, `minor`, `trivial` |
| `--description`   | No       | Test case description                                                               |
| `--preconditions` | No       | Preconditions text                                                                  |
| `--expected`      | No       | Expected result text                                                                |

---

### `set-result`
Mark a test case as passed or failed. Internally, this creates a test run for the case, records the result, and completes the run, all in one step.

```bash
# Pass
python qase_manage.py set-result --project XXX --id 42 --status passed

# Fail with a comment
python qase_manage.py set-result --project XXX --id 42 --status failed \
    --comment "Service did not start within timeout"
```

| Argument    | Required | Description                    |
|-------------|----------|--------------------------------|
| `--id`      | Yes      | Test case ID                   |
| `--status`  | Yes      | `passed` or `failed`           |
| `--comment` | No       | Optional comment on the result |

**Output:**
```
Created run #101 for case #42
Case #42 marked as PASSED
Run #101 completed
```

---

## Global Arguments

These can be placed anywhere in the command line, before or after the subcommand:

| Argument    | Description                                             |
|-------------|---------------------------------------------------------|
| `--project` | Qase project code (e.g. `XXX`). **Required.**          |
| `--token`   | Qase API token. Falls back to `QASE_API_TOKEN` env var. |

---

## Typical Workflow

```bash
export QASE_API_TOKEN=your_token_here

# 1. See what suites exist
python qase_manage.py list-suites --project XXX

# 2. Create a suite and note the returned ID
python qase_manage.py create-suite --project XXX --title "Tests"
# Created suite: 'Tests' (ID: 5)

# 3. Create a test case inside it
python qase_manage.py create-case --project XXX \
    --title "Unit test suite passes" --suite-id 5 --priority high
# Created case: 'Unit test suite passes' (ID: 42)

# 4. Run your tests, then report the result
python qase_manage.py set-result --project XXX --id 42 --status passed
```
