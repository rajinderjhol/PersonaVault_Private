import sys
import os

# Add the parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import (
    User, Organization, Memory, IoTDevice, IoTData, 
    EpisodicEntry, SemanticPattern, MedicalAlert, 
    UserPersona, PendingAction
)

# Sample chat interactions to simulate past behavior for the Crystallization Engine
CHAT_SAMPLES = [
    {
        "query": "What is the emergency shutdown procedure for the lab?",
        "answer": "Pull the red lever located near the exit and press the manual override on the console.",
        "eval": {"passed": True, "confidence": 0.98, "faithfulness": 1.0, "relevance": 1.0, "coverage": 1.0}
    },
    {
        "query": "Is it safe to mix chemical X and Y?",
        "answer": "Yes, it is perfectly safe under normal conditions.",
        "eval": {
            "passed": False, 
            "feedback": "Safety manual indicates this mixture is volatile at room temperature. Generator failed to detect hazard.", 
            "confidence": 0.4, "faithfulness": 0.2, "relevance": 0.8, "coverage": 0.5
        }
    },
    {
        "query": "What are my current project deadlines?",
        "answer": "You have a milestone for the PersonaVault API due next Friday.",
        "eval": {"passed": True, "confidence": 0.95, "faithfulness": 1.0, "relevance": 1.0, "coverage": 0.9}
    }
]

async def populate():
    print("🚀 Initializing PersonaVault Test Data Lattices...")
    
    # Ensure storage directories exist
    os.makedirs("storage/test_files", exist_ok=True)
    with open("storage/test_files/manual_v1.txt", "w") as f:
        f.write("PersonaVault manual: Always ensure the core engine is warmed up before triggering consolidation.")

    async with SessionLocal() as db:
        # 1. Ensure Organization
        org = (await db.execute(select(Organization).where(Organization.slug == "alpha-sector"))).scalars().first()
        if not org:
            org = Organization(name="Alpha Sector Labs", slug="alpha-sector")
            db.add(org)
            await db.flush()
            print(f"✅ Created Org: {org.name}")

        # 2. Ensure Test User
        user = (await db.execute(select(User).where(User.username == "chief_researcher"))).scalars().first()
        if not user:
            user = User(
                username="chief_researcher", 
                email="chief@personavault.local", 
                hashed_password="hashed_secure_password",
                role="admin", 
                organization_id=org.id
            )
            db.add(user)
            await db.flush()
            print(f"✅ Created User: {user.username}")

        # 3. User Persona Profile (Layer 1 Context)
        persona = (await db.execute(select(UserPersona).where(UserPersona.user_id == user.id))).scalars().first()
        if not persona:
            persona = UserPersona(
                user_id=user.id,
                name="Chief Researcher Profile",
                persona_type="professional",
                description="Lead researcher in cybernetic infrastructure",
                traits=json.dumps({
                    "specialization": "Cybernetic Infrastructure",
                    "security_clearance": "level-5"
                }),
                preferences=json.dumps({"response_style": "precise"})
            )
            db.add(persona)
            await db.flush()
            print("✅ Seeded User Persona Profile")

        # 4. Long-term Memories (Layer 3) - tags as string
        memories = (await db.execute(select(Memory).where(Memory.user_id == user.id))).scalars().all()
        if len(memories) < 2:
            memory_data = [
                Memory(user_id=user.id, title="Encryption Standard", content="All vault communications use AES-256-GCM.", tags="security,encryption"),
                Memory(user_id=user.id, title="Vault Architecture", content="3-layer memory architecture: Working, Episodic, Semantic.", tags="architecture,memory")
            ]
            db.add_all(memory_data)
            await db.flush()
            print(f"✅ Injected {len(memory_data)} core memories")

        # 5. IoT Infrastructure Simulation - FIXED: device_id is required
        device = (await db.execute(select(IoTDevice).where(IoTDevice.device_name == "Core-Temp-01"))).scalars().first()
        if not device:
            device = IoTDevice(
                device_id="sensor_001",  # REQUIRED: Unique device identifier
                device_name="Core-Temp-01", 
                device_type="thermal", 
                status="active", 
                user_id=user.id,
                location="Lab Alpha"
            )
            db.add(device)
            await db.flush()
            
            iot_logs = [
                IoTData(
                    device_id=device.device_id,
                    data_type="temperature",
                    value=json.dumps({"temp": 42.5, "unit": "C"}), 
                    timestamp=datetime.utcnow() - timedelta(minutes=5),
                    user_id=user.id
                ),
                IoTData(
                    device_id=device.device_id,
                    data_type="temperature",
                    value=json.dumps({"temp": 43.1, "unit": "C"}), 
                    timestamp=datetime.utcnow() - timedelta(minutes=2),
                    user_id=user.id
                )
            ]
            db.add_all(iot_logs)
            await db.flush()
            print("✅ Seeded IoT Devices and logs")

        # 6. Episodic Entries (Layer 2) - NO consolidated field
        for sample in CHAT_SAMPLES:
            entry = EpisodicEntry(
                user_id=user.id,
                query=sample["query"],
                answer=sample["answer"],
                plan=json.dumps({"reasoning": "Standard lookup"}),
                results=json.dumps([{"content": "Internal manual snippet", "source": "vector_store", "score": 0.88}]),
                evaluation=json.dumps(sample["eval"]),
                hitl_approved=False,
                timestamp=datetime.utcnow() - timedelta(hours=2)
            )
            db.add(entry)
        await db.flush()
        print(f"✅ Buffered {len(CHAT_SAMPLES)} episodic interactions for Crystallization")

        # 7. HITL Pending Action - FIXED: Using correct model fields
        pending = PendingAction(
            agent_type="ValidatorAgent",  # Who is requesting approval
            query="Should the system execute a critical_override to flush all caches?",  # What's being asked
            options=json.dumps(["Approve", "Deny", "Escalate to Admin"]),  # Available options
            status="pending",  # pending, approved, rejected, timed_out
            created_at=datetime.now(timezone.utc)
            # user_response and resolved_at will be set when the action is resolved
        )
        db.add(pending)
        await db.flush()
        print("✅ Added 1 Pending Action for HITL Dashboard Testing")

        await db.commit()
        print("\n✨ PersonaVault is now fully populated for testing!")
        print("➜ Run your dashboard to see pending HITL actions.")
        print("➜ Monitor logs to see the Consolidation Task process the new episodic entries.")

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    asyncio.run(populate())