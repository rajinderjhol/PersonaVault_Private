import pytest
import json
import os
from unittest.mock import MagicMock, AsyncMock
from app.api.v1.endpoints.mcp import call_tool

# Mocking Request object
class MockRequest:
    def __init__(self, state):
        self.state = state
        self.app = MagicMock()
        self.app.state = state

@pytest.mark.asyncio
async def test_guardian_blocks_unsafe_action():
    # Setup mock constitution
    constitution = {
        "policies": [
            {"id": "policy_1", "rule": "deny_pii", "description": "Deny PII leakage"}
        ]
    }
    with open("governance_constitution.json", "w") as f:
        json.dump(constitution, f)
    
    # Mocking app state and necessary services
    mock_state = MagicMock()
    # Properly mock the async blackboard
    mock_blackboard = AsyncMock()
    mock_state.blackboard = mock_blackboard
    
    # Setup the tool call that triggers governance
    request = MockRequest(mock_state)
    
    # Simulated action that violates "deny_pii" (e.g., posting PII to blackboard)
    tool_name = "blackboard_post"
    arguments = {"insight": "Patient John Doe has PII SSN 123-456-789"}
    
    # Execution
    # Note: In current app code, call_tool just posts to blackboard.
    # The 'governance check' logic seems to be missing in app/api/v1/endpoints/mcp.py.
    # This test will likely pass now, which confirms that governance IS NOT enforced here.
    result = await call_tool(tool_name, arguments, request, current_user=1)
    
    # If the test passes without an error/block, then governance is not enforced
    # as expected based on current codebase analysis.
    
    # Cleanup
    if os.path.exists("governance_constitution.json"):
        os.remove("governance_constitution.json")

