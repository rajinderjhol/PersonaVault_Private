import pytest
from app.models import AuditLog, User

def test_audit_log_generation(client, session):
    """Verify that POST requests generate audit log entries."""
    # 1. Clear existing logs
    session.query(AuditLog).delete()
    session.commit()
    
    # 2. Perform a state-changing operation
    # Using register since it's a POST and usually public
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "audit_test", "email": "audit@test.com", "password": "SecurePassword123"}
    )
    
    # 3. Check the database for a new audit log
    logs = session.query(AuditLog).filter(AuditLog.action.contains("POST")).all()
    assert len(logs) >= 1
    
    log = logs[0]
    assert "/api/v1/auth/register" in log.action
    assert log.status == "success"
    assert "audit_test" in log.details