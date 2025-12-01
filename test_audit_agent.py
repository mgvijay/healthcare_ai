"""
Standalone test script for Government Audit Agent
Run this to test A2A communication independently
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from agents.gov_audit_agent import get_audit_runner, run_audit_query
from agent import get_runner


async def main():
    """Test A2A communication between root and audit agents"""
    
    print("="*70)
    print("🔐 GOVERNMENT AUDIT AGENT - A2A COMMUNICATION TEST")
    print("="*70)
    
    try:
        # Step 1: Initialize root healthcare agent
        print("\n📍 Step 1: Initializing Root Healthcare Agent...")
        root_runner, root_session = await get_runner()
        print("✅ Root Healthcare Agent initialized successfully")

        # Ensure a session exists on the root agent for the audit agent (A2A)
        # This creates (app_name="healthcare", user_id="audit_001", session_id="session_123")
        try:
            await root_session.create_session(app_name="healthcare", user_id="audit_001", session_id="session_123")
            print("✅ Created audit session on root agent: (healthcare, audit_001, session_123)")
        except Exception:
            # ignore if already exists
            pass
        
        # Step 2: Initialize audit agent
        print("\n📍 Step 2: Initializing Government Audit Agent...")
        audit_runner, audit_session = await get_audit_runner()
        print("✅ Government Audit Agent initialized successfully")
        
        # Step 3: Insert test patient data
        print("\n📍 Step 3: Creating test patient data...")
        from agent import insert_patient_record
        insert_patient_record("Test Patient 1", 45)
        insert_patient_record("Test Patient 2", 38)
        insert_patient_record("Test Patient 3", 52)
        print("✅ Test patient records created")
        
        # Step 4: Run A2A audit query
        print("\n📍 Step 4: Executing A2A Communication Test...")
        audit_result = await run_audit_query(root_runner, audit_runner)
        
        print("\n" + "="*70)
        print("✅ A2A COMMUNICATION TEST COMPLETED SUCCESSFULLY")
        print("="*70)
        
        print("\n📊 Audit records retrieved via A2A protocol:")
        print(audit_result)
        
        print("\n📊 Audit records also available at:")
        print("   http://localhost:8000/audit-report")
        print("\n💡 Start the audit server in another terminal:")
        print("   python audit_server.py")
        
    except Exception as e:
        print(f"\n❌ Error during A2A communication test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n✅ Test completed. Exiting...\n")


if __name__ == "__main__":
    print("\n🚀 Starting Government Audit Agent Test...\n")
    asyncio.run(main())