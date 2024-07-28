import pytest

from cli_tool_audit.audit_manager import AuditManager


@pytest.fixture
def audit_manager():
    return AuditManager()
