import asyncio
import os
import sys
sys.path.insert(0, '.')
import yaml
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.services.packs.pack_loader import PackLoader

async def install_all_packs():
    print("📦 Installing Domain Intelligence Packs...")
    packs_dir = "packs"
    loader = PackLoader(lambda: SessionLocal())
    
    # Simple admin user ID
    admin_user_id = 1
    
    for root, dirs, files in os.walk(packs_dir):
        for file in files:
            if file == "behaviour_pack.yaml":
                pack_path = os.path.join(root, file)
                print(f"  - Installing {pack_path}...")
                try:
                    with open(pack_path, "r") as f:
                        yaml_content = f.read()
                    
                    pack = await loader.load_pack_from_yaml(yaml_content, admin_user_id)
                    if pack:
                        await loader.install_pack(pack)
                        print(f"    ✅ Installed {pack.name}")
                    else:
                        print(f"    ❌ Failed to load {pack_path}")
                except Exception as e:
                    print(f"    ❌ Error installing {pack_path}: {e}")

if __name__ == "__main__":
    sys.path.insert(0, '.')
    asyncio.run(install_all_packs())
