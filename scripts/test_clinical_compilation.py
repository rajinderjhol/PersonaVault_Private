#!/usr/bin/env python3
"""
Test compilation of the Clinical DIU.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.compiler.pack_compiler import BehaviorPackCompiler


async def main():
    print("🧪 Testing Clinical DIU Compilation")
    print("=" * 50)
    
    compiler = BehaviorPackCompiler()
    
    diu_path = Path("app/packs/clinical")
    output_dir = Path("app/packs/clinical/compiled")
    
    if not diu_path.exists():
        print(f"❌ DIU path not found: {diu_path}")
        return
    
    print(f"📁 DIU Path: {diu_path}")
    print(f"📁 Output Path: {output_dir}")
    
    try:
        compiled = await compiler.compile(
            source_path=diu_path,
            target="airgap",
            output_dir=output_dir
        )
        
        print("\n✅ Compilation Successful!")
        print(f"   Name: {compiled.name}")
        print(f"   Version: {compiled.version}")
        print(f"   Domain: {compiled.domain}")
        print(f"   Target: {compiled.target}")
        print(f"   Policies: {len(compiled.policies)}")
        print(f"   Agents: {len(compiled.agents)}")
        print(f"   Patterns: {len(compiled.patterns)}")
        
        if output_dir:
            runtime_file = output_dir / f"{compiled.name}_runtime.py"
            if runtime_file.exists():
                print(f"\n📄 Runtime file generated: {runtime_file}")
                print(f"   Size: {runtime_file.stat().st_size:,} bytes")
        
        print("\n🎉 Clinical DIU is ready for deployment!")
        
    except Exception as e:
        print(f"\n❌ Compilation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
