---
name: python_code_review
display_name: "Python Code Review"
description: "Review Python code with focus on clean code principles, type safety, and best practices"
version: "2.0.0"
tags: [code-review, python, clean-code]
requires: [ado_basics]
subagents: [python-code-reviewer]
tools:
  - mcp__azure-devops__get_pull_request_changes
  - mcp__azure-devops__add_pull_request_comment
  - Read
  - Glob
  - Grep
triggers:
  - "review.*\\.py"
  - "review.*python"
---

## Python Code Review Guidelines

### 1. Core Principles

#### 1.1 Single Responsibility Principle (SRP)

**Rule**: Each function/class should do one thing well

```python
# BAD: Multiple responsibilities
def process_and_save_and_notify(data):
    cleaned = clean_data(data)
    save_to_database(cleaned)
    send_notification("Data saved")
    return cleaned

# GOOD: Separate responsibilities
def process_data(data: dict) -> dict:
    """Process and clean data."""
    return clean_data(data)

def save_processed_data(data: dict) -> None:
    """Save data to database."""
    save_to_database(data)

def notify_completion(message: str) -> None:
    """Send completion notification."""
    send_notification(message)
```

**Signs of SRP violation:**
- Function name contains "and" (e.g., `validate_and_save`)
- Function has multiple return paths for different responsibilities
- Function requires multiple mocks to test

#### 1.2 DRY (Don't Repeat Yourself)

**Rule**: Extract repeated logic into reusable functions

```python
# BAD: Repeated logic
def get_user_name(user_id: int) -> str:
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    if user:
        return user.name
    return "Unknown"

def get_user_email(user_id: int) -> str:
    user = db.query(f"SELECT * FROM users WHERE id = {user_id}")
    if user:
        return user.email
    return "unknown@example.com"

# GOOD: Reusable helper
def get_user(user_id: int) -> User | None:
    """Fetch user by ID."""
    return db.query(f"SELECT * FROM users WHERE id = {user_id}")

def get_user_name(user_id: int) -> str:
    user = get_user(user_id)
    return user.name if user else "Unknown"

def get_user_email(user_id: int) -> str:
    user = get_user(user_id)
    return user.email if user else "unknown@example.com"
```

### 2. Dependency Management

#### 2.1 Global Logger Pattern

**Rule**: Define logger once at module level, not in every function

```python
# BAD: Logger in every function
def process_file(file_path: str) -> None:
    logger = logging.getLogger(__name__)  # Repeated!
    logger.info(f"Processing {file_path}")

def validate_file(file_path: str) -> bool:
    logger = logging.getLogger(__name__)  # Repeated!
    logger.debug(f"Validating {file_path}")

# GOOD: Global logger at module level
import logging

logger = logging.getLogger(__name__)

def process_file(file_path: str) -> None:
    logger.info(f"Processing {file_path}")

def validate_file(file_path: str) -> bool:
    logger.debug(f"Validating {file_path}")
    return True
```

#### 2.2 Import Organization

**Rule**: Organize imports in standard order

```python
# GOOD: Standard import order (isort compatible)
# 1. Standard library
import logging
import os
from datetime import datetime
from pathlib import Path

# 2. Third-party packages
import pandas as pd
import pyspark.sql.functions as F
from pyspark.sql import DataFrame

# 3. Local imports
from mypackage.config import Settings
from mypackage.utils import helper
```

### 3. Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Functions | verb_phrase (snake_case) | `get_user()`, `calculate_total()`, `is_valid()` |
| Variables | descriptive nouns (snake_case) | `user_count`, `total_amount` |
| Constants | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_TIMEOUT` |
| Classes | PascalCase | `DataProcessor`, `UserValidator` |
| Boolean | is/has/can/should prefix | `is_valid`, `has_permission`, `can_proceed` |
| Private | leading underscore | `_internal_method()`, `_cache` |

```python
# BAD: Vague names
def proc(d):
    x = d.get("val")
    return x * 2

# GOOD: Descriptive names
def calculate_doubled_value(data: dict) -> float:
    original_value = data.get("val", 0)
    return original_value * 2

# BAD: Non-descriptive boolean
def check(user):
    return user.active and user.verified

# GOOD: Descriptive boolean function
def is_user_eligible(user: User) -> bool:
    return user.active and user.verified
```

### 4. Type Annotations

#### 4.1 Modern Python 3.9+ Syntax

**Rule**: Use built-in generics, not typing module imports

```python
# BAD: Legacy typing (Python 3.8 style)
from typing import List, Dict, Optional, Union, Tuple

def process_items(items: List[str]) -> Dict[str, int]:
    pass

def get_user(id: int) -> Optional[User]:
    pass

def parse_value(val: Union[str, int]) -> str:
    pass

# GOOD: Modern syntax (Python 3.9+)
def process_items(items: list[str]) -> dict[str, int]:
    pass

def get_user(id: int) -> User | None:
    pass

def parse_value(val: str | int) -> str:
    pass

# GOOD: Complex types
def get_users_by_status(status: str) -> dict[str, list[User]]:
    pass

def process_batch(data: list[tuple[str, int]]) -> None:
    pass
```

#### 4.2 ClassVar for Shared State

**Rule**: Use ClassVar for class-level shared attributes

```python
from typing import ClassVar, Any

# BAD: Mutable default shared across instances (bug!)
class ConfigManager:
    _cache = {}  # Shared unintentionally!

# GOOD: Explicit ClassVar
class ConfigManager:
    _cache: ClassVar[dict[str, Any]] = {}
    _lock: ClassVar[threading.Lock] = threading.Lock()

    def __init__(self):
        self.instance_data: dict[str, str] = {}  # Instance-specific
```

#### 4.3 Return Type Annotations

```python
# BAD: Missing return types
def calculate_tax(amount):
    return amount * 0.1

def get_users():
    return db.query("SELECT * FROM users")

# GOOD: Explicit return types
def calculate_tax(amount: float) -> float:
    return amount * 0.1

def get_users() -> list[User]:
    return db.query("SELECT * FROM users")

# GOOD: Use -> None for functions with no return
def log_event(message: str) -> None:
    logger.info(message)
```

### 5. Code Organization

#### 5.1 Extract Constants

**Rule**: Replace magic numbers and strings with named constants

```python
# BAD: Magic numbers
def is_valid_age(age: int) -> bool:
    return 0 < age < 150

def get_timeout() -> int:
    return 30  # What does 30 mean?

# GOOD: Named constants
MIN_AGE = 0
MAX_AGE = 150
DEFAULT_TIMEOUT_SECONDS = 30

def is_valid_age(age: int) -> bool:
    return MIN_AGE < age < MAX_AGE

def get_timeout() -> int:
    return DEFAULT_TIMEOUT_SECONDS
```

#### 5.2 Context Objects for Complex State

**Rule**: Use dataclasses for complex state management

```python
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar

@dataclass
class ProcessingContext:
    """Thread-safe processing context."""

    _lock: ClassVar[threading.Lock] = threading.Lock()
    _instance: ClassVar["ProcessingContext | None"] = None

    start_time: datetime = field(default_factory=datetime.now)
    processed_count: int = 0
    errors: list[str] = field(default_factory=list)

    @classmethod
    def get_instance(cls) -> "ProcessingContext":
        """Get singleton instance (thread-safe)."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def reset(self) -> None:
        """Reset context for new processing run."""
        self.start_time = datetime.now()
        self.processed_count = 0
        self.errors.clear()
```

#### 5.3 Function Length

**Rule**: Keep functions short and focused (< 20-30 lines ideally)

```python
# BAD: Long function doing too much
def process_order(order):
    # Validate order
    if not order.customer_id:
        raise ValueError("Missing customer")
    if not order.items:
        raise ValueError("No items")
    # Calculate totals
    subtotal = sum(item.price * item.quantity for item in order.items)
    tax = subtotal * 0.1
    total = subtotal + tax
    # Save to database
    db.save(order)
    # Send notification
    email.send(order.customer_id, f"Order total: {total}")
    return total

# GOOD: Split into focused functions
def validate_order(order: Order) -> None:
    """Validate order has required fields."""
    if not order.customer_id:
        raise ValueError("Missing customer")
    if not order.items:
        raise ValueError("No items")

def calculate_order_total(order: Order, tax_rate: float = 0.1) -> float:
    """Calculate order total including tax."""
    subtotal = sum(item.price * item.quantity for item in order.items)
    return subtotal * (1 + tax_rate)

def process_order(order: Order) -> float:
    """Process order: validate, calculate, save, notify."""
    validate_order(order)
    total = calculate_order_total(order)
    db.save(order)
    notify_customer(order.customer_id, total)
    return total
```

### 6. Error Handling

#### 6.1 Specific Exceptions

**Rule**: Catch specific exceptions, not bare Exception

```python
# BAD: Generic exception
try:
    result = process_data(data)
except Exception as e:
    logger.error(f"Error: {e}")

# GOOD: Specific exceptions
try:
    result = process_data(data)
except ValidationError as e:
    logger.error(f"Validation failed: {e}")
    raise
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    raise
except Exception as e:
    logger.exception("Unexpected error during processing")
    raise
```

#### 6.2 Custom Exceptions

**Rule**: Create domain-specific exceptions for clarity

```python
# GOOD: Domain-specific exception hierarchy
class DataProcessingError(Exception):
    """Base exception for data processing."""
    pass

class ValidationError(DataProcessingError):
    """Raised when data validation fails."""
    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"{field}: {message}")

class TransformationError(DataProcessingError):
    """Raised when data transformation fails."""
    pass

class DataSourceError(DataProcessingError):
    """Raised when data source is unavailable."""
    def __init__(self, source: str, cause: Exception | None = None):
        self.source = source
        self.cause = cause
        super().__init__(f"Failed to access {source}")
```

#### 6.3 Context Managers for Resources

**Rule**: Use context managers for resource cleanup

```python
# BAD: Manual resource management
def read_file(path: str) -> str:
    f = open(path)
    content = f.read()
    f.close()  # May not execute on error!
    return content

# GOOD: Context manager
def read_file(path: str) -> str:
    with open(path) as f:
        return f.read()

# GOOD: Custom context manager
from contextlib import contextmanager

@contextmanager
def database_connection(connection_string: str):
    """Context manager for database connections."""
    conn = create_connection(connection_string)
    try:
        yield conn
    finally:
        conn.close()
```

### 7. Security

#### 7.1 Input Validation

**Rule**: Validate all external input at system boundaries

```python
# BAD: No validation (SQL injection risk!)
def get_user_data(user_id: str) -> dict:
    return db.query(f"SELECT * FROM users WHERE id = '{user_id}'")

# GOOD: Parameterized queries + validation
def get_user_data(user_id: str) -> dict:
    if not user_id.isalnum():
        raise ValidationError("user_id", "Must be alphanumeric")
    return db.query("SELECT * FROM users WHERE id = ?", [user_id])

# GOOD: Use ORM
def get_user_data(user_id: str) -> dict:
    return session.query(User).filter(User.id == user_id).first()
```

#### 7.2 Secrets Management

**Rule**: Never hardcode secrets; use appropriate secret stores

```python
# BAD: Hardcoded secrets
API_KEY = "sk-1234567890abcdef"
DATABASE_PASSWORD = "supersecret123"

# BAD: Environment variables in Databricks notebooks
API_KEY = os.environ.get("API_KEY")

# GOOD: Databricks secrets
API_KEY = dbutils.secrets.get(scope="my-scope", key="api-key")

# GOOD: Azure Key Vault (non-Databricks)
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://myvault.vault.azure.net/", credential=credential)
secret = client.get_secret("my-secret").value
```

#### 7.3 Path Traversal Prevention

```python
# BAD: Direct path concatenation
def read_user_file(filename: str) -> str:
    return open(f"/data/users/{filename}").read()  # "../../../etc/passwd" attack!

# GOOD: Safe path handling
from pathlib import Path

BASE_DIR = Path("/data/users")

def read_user_file(filename: str) -> str:
    # Resolve and verify path stays within base
    safe_path = (BASE_DIR / filename).resolve()
    if not safe_path.is_relative_to(BASE_DIR):
        raise SecurityError("Path traversal attempt detected")
    return safe_path.read_text()
```

### 8. Code Quality Tools

#### 8.1 Ruff Configuration

**Rule**: Use Ruff for fast, comprehensive linting

```toml
# pyproject.toml
[tool.ruff]
line-length = 120
target-version = "py39"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "SIM",  # flake8-simplify
    "TCH",  # flake8-type-checking
]

# Databricks-specific ignores
ignore = [
    "F821",  # Undefined name (dbutils, spark, display are magic globals)
    "E402",  # Module level import not at top (notebook cells)
    "N812",  # Lowercase imported as non-lowercase (pyspark.sql.functions as F)
]

[tool.ruff.lint.isort]
known-first-party = ["mypackage"]
```

#### 8.2 Type Checking with mypy

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.9"
strict = true
warn_return_any = true
warn_unused_ignores = true
disallow_untyped_defs = true

[[tool.mypy.overrides]]
module = "pyspark.*"
ignore_missing_imports = true
```

### 9. Databricks Notebook Specific

#### 9.1 Widget Usage

**Rule**: Use widgets for notebook parameters

```python
# GOOD: Widgets for parameters
dbutils.widgets.text("environment", "dev", "Environment")
dbutils.widgets.dropdown("mode", "full", ["full", "incremental"], "Mode")
dbutils.widgets.text("date", "", "Processing Date (YYYY-MM-DD)")

# Get widget values with defaults
environment = dbutils.widgets.get("environment")
mode = dbutils.widgets.get("mode")
date = dbutils.widgets.get("date") or datetime.now().strftime("%Y-%m-%d")
```

#### 9.2 Magic Commands Best Practices

- `%run` - Execute shared utility notebooks (same context)
- `%pip install` - Install packages (restart kernel after)
- `%sql` - Run SQL with automatic display
- `%md` - Markdown documentation

```python
# GOOD: Structured notebook with magic commands
# %md # Data Processing Pipeline

# %run ./shared/utilities  # Load common functions

# %pip install great-expectations  # Install if needed

# Python code
df = spark.read.table("source_table")
```

#### 9.3 Notebook Organization

```python
# Recommended notebook structure:
# Cell 1: Configuration and widgets
# Cell 2: Imports
# Cell 3: Constants and configuration
# Cell 4: Helper functions
# Cell 5+: Main logic
# Final cell: Cleanup/summary
```

### 10. Testing Best Practices

#### 10.1 Testable Code

**Rule**: Write code that's easy to test

```python
# BAD: Hard to test (hidden dependencies)
def process_order():
    order = get_current_order()  # Where does this come from?
    db.save(order)  # Global db dependency
    return order.total

# GOOD: Dependency injection (easy to test)
def process_order(order: Order, repository: OrderRepository) -> float:
    repository.save(order)
    return order.total

# Test
def test_process_order():
    mock_repo = Mock(spec=OrderRepository)
    order = Order(total=100.0)
    result = process_order(order, mock_repo)
    assert result == 100.0
    mock_repo.save.assert_called_once_with(order)
```

#### 10.2 Test Naming

```python
# GOOD: Descriptive test names
def test_calculate_tax_returns_correct_amount_for_positive_value():
    pass

def test_calculate_tax_raises_error_for_negative_value():
    pass

def test_get_user_returns_none_when_user_not_found():
    pass
```

### 11. Code Review Checklist

**Core Principles:**
- [ ] Functions have single responsibility (SRP)
- [ ] No repeated logic (DRY)
- [ ] Descriptive names for all identifiers
- [ ] Constants extracted with UPPER_SNAKE_CASE
- [ ] Functions are reasonably short (< 30 lines)

**Type Annotations:**
- [ ] Modern Python 3.9+ syntax used (`list[str]` not `List[str]`)
- [ ] Return types specified on all functions
- [ ] `None` returns use `| None` not `Optional`
- [ ] ClassVar used for class-level attributes

**Error Handling:**
- [ ] Specific exceptions caught (not bare `except:`)
- [ ] Custom exceptions for domain errors
- [ ] Proper logging with context
- [ ] Resources cleaned up (context managers)

**Security:**
- [ ] No hardcoded credentials
- [ ] Parameterized queries (no SQL injection)
- [ ] Input validation at boundaries
- [ ] Path traversal prevention

**Code Quality:**
- [ ] Ruff/linting passes
- [ ] No unused imports
- [ ] Proper docstrings on public functions
- [ ] Import organization (isort)

**Databricks Specific:**
- [ ] Widgets for parameters
- [ ] dbutils.secrets for credentials
- [ ] Proper notebook structure

### 12. Review Process

1. Fetch PR changes using `mcp__azure-devops__get_pull_request_changes`
2. Filter to Python files (.py)
3. Check for clean code violations:
   - SRP violations (functions doing multiple things)
   - DRY violations (repeated code blocks)
   - Poor naming (single-letter variables, vague names)
4. Verify type annotations:
   - Use modern Python 3.9+ syntax
   - All functions have return types
5. Check security patterns:
   - No hardcoded secrets
   - Parameterized queries
   - Input validation
6. Verify error handling:
   - Specific exceptions
   - Proper logging
7. Post inline comments with:
   - File path and line number
   - Severity (Critical/High/Medium/Low)
   - Problem description
   - Code example of the fix
