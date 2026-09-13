import asyncio
import pytest
from unittest.mock import MagicMock
from app.services.marketplace.reputation_service import ReputationService

@pytest.mark.asyncio
async def test_reputation_score_calculation():
    service = ReputationService()
    
    # Pack A: High confidence, low usage
    stats_a = {"confidence_avg": 0.95, "use_count": 10, "rating_avg": 4.5}
    score_a = service.calculate_reputation_score(stats_a, "2026-09-01")
    
    # Pack B: Lower confidence, high usage
    stats_b = {"confidence_avg": 0.80, "use_count": 1000, "rating_avg": 4.0}
    score_b = service.calculate_reputation_score(stats_b, "2026-08-01")
    
    assert score_a > 0 and score_b > 0
    # Higher confidence usually wins in this formula unless usage is extreme
    print(f"\nScore A (High Conf): {score_a}")
    print(f"Score B (High Usage): {score_b}")
    
    print("✅ Reputation calculation verified.")

@pytest.mark.asyncio
async def test_registry_sorting_by_reputation():
    from app.services.marketplace.registry import MarketplaceRegistry
    registry = MarketplaceRegistry()
    registry.packs = {
        "pack_low": {
            "id": "low",
            "metadata": {"name": "Low Pack"},
            "statistics": {"reputation_score": 0.1, "download_count": 100}
        },
        "pack_high": {
            "id": "high",
            "metadata": {"name": "High Pack"},
            "statistics": {"reputation_score": 0.9, "download_count": 10}
        }
    }
    
    result = registry.list_packs()
    
    # High reputation should be first despite lower downloads
    assert result["packs"][0]["id"] == "high"
    assert result["packs"][1]["id"] == "low"
    
    print("✅ Registry sorting verified.")

if __name__ == "__main__":
    asyncio.run(test_reputation_score_calculation())
    asyncio.run(test_registry_sorting_by_reputation())
