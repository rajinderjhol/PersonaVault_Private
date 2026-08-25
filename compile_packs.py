#!/usr/bin/env python
"""
Behavior Pack Compiler CLI
Usage:
    python compile_packs.py --compile-all
    python compile_packs.py --compile pack_name
    python compile_packs.py --list
    python compile_packs.py --clean
"""
import sys
import logging
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from compiler.pack_compiler import BehaviorPackCompiler
from runtime.pack_executor import PackExecutor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Behavior Pack Compiler')
    parser.add_argument('--compile-all', action='store_true', help='Compile all packs')
    parser.add_argument('--compile', type=str, help='Compile a specific pack by name')
    parser.add_argument('--list', action='store_true', help='List compiled packs')
    parser.add_argument('--clean', action='store_true', help='Clean compiled outputs')
    parser.add_argument('--test', type=str, help='Test a pack with sample input')
    
    args = parser.parse_args()
    
    compiler = BehaviorPackCompiler()
    executor = PackExecutor()
    
    if args.compile_all:
        logger.info("🚀 Compiling all packs...")
        compiled = compiler.compile_all()
        logger.info(f"✅ Compiled {len(compiled)} packs")
        
    elif args.compile:
        logger.info(f"🚀 Compiling pack: {args.compile}")
        yaml_path = compiler.pack_dir / f"{args.compile}.yaml"
        if not yaml_path.exists():
            # Try searching in subdirectories of packs/
            alt_path = Path("packs") / args.compile / "behaviour_pack.yaml"
            if alt_path.exists():
                yaml_path = alt_path
            else:
                logger.error(f"❌ Pack not found: {yaml_path} or {alt_path}")
                sys.exit(1)
        compiled = compiler.compile_pack(yaml_path)
        logger.info(f"✅ Compiled {compiled.name} v{compiled.version}")
        
    elif args.list:
        logger.info("📦 Compiled packs:")
        for pack_info in executor.list_packs():
            meta = pack_info['metadata']
            print(f"  - {pack_info['name']} (v{meta['version']}, {meta['domain']})")
            
    elif args.clean:
        logger.info("🧹 Cleaning compiled packs...")
        compiler.clean()
        logger.info("✅ Cleaned")
        
    elif args.test:
        logger.info(f"🧪 Testing pack: {args.test}")
        pack = executor.get_pack(args.test)
        if not pack:
            # Try loading it if it exists but not loaded
            try:
                pack = executor.load_pack(args.test)
            except Exception:
                logger.error(f"❌ Pack not found or failed to load: {args.test}")
                sys.exit(1)
        
        import asyncio
        async def test():
            # Test input designed to trigger the High Value policy
            test_input = "High value case for legal case $2,500,000"
            logger.info(f"🔍 Input: {test_input}")
            
            result = await executor.process_with_best_pack(
                raw_input=test_input,
                user_id=1
            )
            import json
            print("\n🛡️  AUDITABLE DECISION TRACE:")
            print(json.dumps(result['trace'], indent=2))
            print("\n📋 SUMMARY RESULT:")
            summary = {
                "decision": result['decision'],
                "actions": result['actions'],
                "autonomy": result['autonomy']
            }
            print(json.dumps(summary, indent=2))
            return result
        
        asyncio.run(test())
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
