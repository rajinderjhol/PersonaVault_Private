import pytest
import yaml
from pathlib import Path
from compiler.pack_compiler import BehaviorPackCompiler

class TestBehaviorPackCompiler:
    def test_compiles_valid_pack(self, valid_pack_file):
        """A valid pack should compile without errors"""
        compiler = BehaviorPackCompiler()
        compiled = compiler.compile_pack(valid_pack_file)
        
        assert compiled.name == "Test Pack"
        assert compiled.version == "1.0.0"
        assert compiled.runtime_class is not None
        assert "class TestPackPack" in compiled.runtime_class

    def test_generates_signal_normalizer(self, valid_pack_file):
        """Compiler should generate signal normalization code"""
        compiler = BehaviorPackCompiler()
        compiled = compiler.compile_pack(valid_pack_file)
        
        assert "class TestPackSignalNormalizer" in compiled.signal_normalizer
        assert "def normalize" in compiled.signal_normalizer
        assert "test_entity" in compiled.signal_normalizer

    def test_generates_policy_engine(self, valid_pack_file):
        """Compiler should generate policy evaluation code"""
        compiler = BehaviorPackCompiler()
        compiled = compiler.compile_pack(valid_pack_file)
        
        assert "class TestPackPolicyEngine" in compiled.policy_engine
        assert "def evaluate" in compiled.policy_engine
        assert "Test Policy" in compiled.policy_engine

    def test_deterministic_output(self, valid_pack_file):
        """Same input should produce same output (for caching)"""
        compiler = BehaviorPackCompiler()
        ts = "2026-08-25T22:00:00"
        compiled1 = compiler.compile_pack(valid_pack_file, fixed_timestamp=ts)
        compiled2 = compiler.compile_pack(valid_pack_file, fixed_timestamp=ts)
        
        assert compiled1.signature == compiled2.signature
        assert compiled1.runtime_class == compiled2.runtime_class
