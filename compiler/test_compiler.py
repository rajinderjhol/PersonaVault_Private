import sys
import os
# Add current working directory to sys.path
sys.path.insert(0, os.getcwd())

from compiler.pack_compiler import PackCompiler

compiler = PackCompiler()
# Compile the procurement pack
compiled = compiler.compile("packs/procurement/behaviour_pack.yaml")

print(f"Compiled pack: {compiled.name} (v{compiled.version})")
print("\nGenerated Policy Engine Code:\n")
print(compiled.policy_engine_code)
