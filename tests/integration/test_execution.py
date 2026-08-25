import pytest
import os
import shutil
from pathlib import Path
from compiler.pack_compiler import BehaviorPackCompiler
from runtime.pack_executor import PackExecutor

class TestIntegration:
    @pytest.fixture(autouse=True)
    def setup_packs(self, valid_pack_file):
        """Ensure the valid pack file is in the source directory for compile_all"""
        source_dir = Path("packs/source")
        source_dir.mkdir(parents=True, exist_ok=True)
        dest = source_dir / "test_pack.yaml"
        shutil.copy(valid_pack_file, dest)
        yield
        dest.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_compile_and_execute(self):
        """Compile a pack and execute it through the runtime"""
        compiler = BehaviorPackCompiler()
        compiled = compiler.compile_all()
        assert len(compiled) > 0
        
        executor = PackExecutor()
        # Ensure the test pack is loaded
        executor.load_pack("test_pack")
        
        test_input = "This is a test value $250"
        user_id = 42
        
        result = await executor.process_with_best_pack(
            raw_input=test_input,
            user_id=user_id
        )
        
        assert result["metadata"]["pack"] == "Test Pack"
        assert result["decision"]["policy"] == "Test Policy"
        assert result["decision"]["type"] == "test_decision"
        
        # Verify Trace
        assert "trace" in result
        trace = result["trace"]
        assert trace["trace"]["decision"]["type"] == "test_decision"
        assert any(s["type"] == "test_entity" for s in trace["trace"]["signals"])
        
        # Verify Explanation
        assert "explanation" in result["decision"]
        assert "Test condition met" in result["decision"]["explanation"]

    @pytest.mark.asyncio
    async def test_decision_trace_integrity(self):
        """Verify the authoritative decision trace structure"""
        executor = PackExecutor()
        executor.load_pack("test_pack")
        
        test_input = "test value $50" # Should match entity but not policy (value <= 100)
        result = await executor.process_with_best_pack(
            raw_input=test_input,
            user_id=1
        )
        
        # Policy shouldn't match
        assert result["decision"]["policy"] == "default"
        
        trace = result["trace"]
        assert trace["trace"]["policy"]["matched"] == "default"
        assert len(trace["trace"]["signals"]) > 0
        assert trace["trace"]["signals"][0]["type"] == "test_entity"
        assert trace["trace"]["signals"][0]["value"]["value"] == 50
