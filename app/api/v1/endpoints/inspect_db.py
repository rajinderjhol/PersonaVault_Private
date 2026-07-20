import asyncio
import os
import sys

# Ensure we can import from the app directory
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import User, Organization, LegalMatter, LegalDocument, SystemConfig

async def main():
    print("🔍 PersonaVault Database Inspector")
    async with SessionLocal() as db:
        print("\n--- [ Organizations ] ---")
        orgs = (await db.execute(select(Organization))).scalars().all()
        for org in orgs:
            print(f"ID: {org.id} | Name: {org.name} | Slug: {org.slug}")
        
        print("\n--- [ System Config ] ---")
        configs = (await db.execute(select(SystemConfig))).scalars().all()
        for cfg in configs:
            print(f"Key: {cfg.key} | Value: {cfg.value}")

        print("\n--- [ Users ] ---")
        users = (await db.execute(select(User))).scalars().all()
        for user in users:
            pwd = getattr(user, 'hashed_password', 'N/A')
            print(f"ID: {user.id} | User: {user.username} | Role: {user.role} | Pwd_Set: {pwd != 'N/A'}")

        print("\n--- [ Legal Entities ] ---")
        matters = (await db.execute(select(LegalMatter))).scalars().all()
        docs = (await db.execute(select(LegalDocument))).scalars().all()
        print(f"Matters found: {len(matters)} | Documents found: {len(docs)}")

    print("\n✅ Inspection complete.")

if __name__ == "__main__":
    asyncio.run(main())