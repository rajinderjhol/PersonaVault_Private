import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_current_user
from unittest.mock import MagicMock, AsyncMock
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

# Mock dependencies
mock_user = MagicMock()
mock_user.id = 1
mock_user.username = "testuser"
app.dependency_overrides[get_current_user] = lambda: mock_user

# Mock DB session with minimal AsyncSession interface
mock_db = MagicMock()
mock_db.execute = AsyncMock()
# Mock result for execute
mock_result = MagicMock()
mock_result.scalars.return_value.all.return_value = []
mock_result.scalars.return_value.first.return_value = None
mock_db.execute.return_value = mock_result
app.dependency_overrides[get_db] = lambda: mock_db

# Mock environment and membership services
from app.api.v2.services.environment_service import environment_service
from app.api.v2.services.membership_service import membership_service

async def mock_get_environment(env_id):
    mock_env = MagicMock()
    mock_env.id = env_id
    mock_env.name = "Test Env"
    mock_env.owner_principal_id = "1"
    return mock_env

async def mock_get_members(env):
    mock_member = MagicMock()
    mock_member.principal_id = "1"
    return [mock_member]

environment_service.get_environment = mock_get_environment
membership_service.get_members = mock_get_members

# Mock app state
app.state.ai_client = MagicMock()
app.state.ai_client.get = MagicMock()

client = TestClient(app)

def test_v2_model_endpoints_path():
    """Verify that models are accessible at /v2/environments/{env_id}/models"""
    env_id = "test-env-123"
    # Test WITH trailing slash
    response = client.get(f"/v2/environments/{env_id}/models/")
    assert response.status_code == 200
    # Test WITHOUT trailing slash
    response = client.get(f"/v2/environments/{env_id}/models")
    assert response.status_code == 200

def test_v2_intelligence_sources_path():
    """Verify that intelligence sources are accessible at /v2/intelligence-sources/"""
    response = client.get("/v2/intelligence-sources/")
    assert response.status_code == 200

def test_v2_trust_policies_path():
    """Verify that trust policies are accessible at /v2/trust-policies/"""
    response = client.get("/v2/trust-policies/")
    assert response.status_code == 200

def test_v2_mcp_servers_path():
    """Verify that MCP servers are accessible at /v2/mcp/servers (Fixed from /v2/mcp/mcp/servers)"""
    response = client.get("/v2/mcp/servers")
    assert response.status_code == 200

def test_v2_documents_path():
    """Verify that documents are accessible at /v2/environments/{env_id}/documents"""
    env_id = "test-env-123"
    response = client.get(f"/v2/environments/{env_id}/documents")
    assert response.status_code == 200

def test_v2_admin_health_path():
    """Verify that environment health is accessible at /v2/environments/{env_id}/admin/health"""
    env_id = "test-env-123"
    response = client.get(f"/v2/environments/{env_id}/admin/health")
    assert response.status_code == 200

def test_v2_admin_logs_path():
    """Verify that environment logs are accessible at /v2/environments/{env_id}/admin/logs"""
    env_id = "test-env-123"
    response = client.get(f"/v2/environments/{env_id}/admin/logs")
    assert response.status_code == 200

def test_v2_agent_websocket_path():
    """Verify that agent WebSocket is accessible at /v2/environments/{env_id}/agents/ws"""
    env_id = "test-env-123"
    with client.websocket_connect(f"/v2/environments/{env_id}/agents/ws") as websocket:
        data = websocket.receive_json()
        assert isinstance(data, list)
        assert len(data) > 0
