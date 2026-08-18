#!/usr/bin/env python3
"""
Seed contract memories directly into the database using sqlite3.
This avoids async driver issues.
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = "storage/memory_db/personavault.db"

def seed_contract_memories():
    # Ensure the directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if memories exist
    cursor.execute("SELECT COUNT(*) FROM memories;")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"   ℹ️  Memories already exist ({count} found)")
        conn.close()
        return
    
    # Insert memories
    now = datetime.now().isoformat()
    memories = [
        (1, 'Vendor Contract - XYZ Corp', 'Contract with XYZ Corp signed June 2026. Annual commitment: $500,000. Services: cloud infrastructure. Term: 2 years with auto-renewal clause.', 'contract,vendor,renewal', now, now),
        (1, 'Client Agreement - Acme Corporation', 'Acme Corporation agreement for software development services. Scope: 12-month project. Payment: $150,000 total, net 30 terms.', 'contract,client,payment', now, now),
        (1, 'NDA - Standard Mutual', 'Standard NDA template used for all vendor relationships. Mutual confidentiality, 5-year term, standard exceptions for public information.', 'contract,nda,confidentiality', now, now),
        (1, 'Service Level Agreement - Cloud Services', 'SLA for cloud services: 99.95% uptime guarantee, 2-hour response for critical issues, 24-hour resolution target.', 'contract,sla,service', now, now),
        (1, 'Procurement Review - FastLogistics', '3 suppliers evaluated for logistics contract. Top choice: FastLogistics. Projected savings: 15%. Contract value: $2.5M.', 'contract,procurement,vendor', now, now),
        (1, 'My Profile - Rajinder', 'I am a developer working on PersonaVault, an AI-powered memory and decision platform. I prefer detailed technical explanations.', 'personal,profile,preferences', now, now),
    ]
    
    cursor.executemany('''
        INSERT INTO memories (user_id, title, content, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', memories)
    
    conn.commit()
    conn.close()
    print(f"   ✅ Created {len(memories)} contract and profile memories")

if __name__ == "__main__":
    seed_contract_memories()
