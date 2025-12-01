"""
Government Audit Agent - communicates with root agent using Runner.run_async only.
No usage of google.adk.client or other optional ADK client packages.
"""
import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.genai.types import Part, Content
from config import MODEL_NAME, SECURITY_CODE
AUDIT_USER_ID = "audit_001"
AUDIT_SESSION_ID = "session_123"
ROOT_APP_NAME = "healthcare"

# Create the government audit agent
gov_audit_agent = Agent(
    name="gov_audit_agent",
    model=MODEL_NAME,
    description="Government health audit authority agent. Communicates with healthcare agent to retrieve and audit patient records.",
    instruction=(
        "You are a Government Health Audit Authority Agent.\n"
        "When you need to retrieve patient records: send 'show records' to the root agent, "
        f"then supply the security code '{SECURITY_CODE}' when prompted."
    ),
    tools=[],
    sub_agents=[]
)


async def get_audit_runner() -> Runner:
    """Initialize runner for government audit agent."""
    session_service = InMemorySessionService()
    runner = Runner(agent=gov_audit_agent, app_name="gov_audit", session_service=session_service)

    # create local audit session (this is for the audit runner itself)
    await session_service.create_session(app_name="gov_audit", user_id=AUDIT_USER_ID, session_id=AUDIT_SESSION_ID)
    return runner, session_service


async def _ensure_root_session(root_runner: Runner) -> None:
    """
    Ensure the audit session exists in the root runner's session service.
    Avoids 'Session not found' when sending A2A messages that reuse a session id.
    """
    sess_svc = getattr(root_runner, "session_service", None) or getattr(root_runner, "_session_service", None)
    if sess_svc is None:
        return
    try:
        await sess_svc.create_session(app_name=ROOT_APP_NAME, user_id=AUDIT_USER_ID, session_id=AUDIT_SESSION_ID)
    except Exception:
        pass  # ignore if already exists or unsupported


async def communicate_with_root_agent_a2a(root_runner: Runner, query: str) -> str:
    """
    A2A communication using only the Runner.run_async API (no google.adk.client).
    Sends the query as a Content message and waits for the final response.
    """
    await _ensure_root_session(root_runner)

    content = Content(role="user", parts=[Part(text=query)])
    try:
        events = root_runner.run_async(
            new_message=content,
            user_id=AUDIT_USER_ID,
            session_id=AUDIT_SESSION_ID,
        )
    except Exception as e:
        return f"❌ A2A Communication Error (send): {e}"

    response_text = ""
    try:
        async for event in events:
            try:
                if event.is_final_response():
                    if getattr(event, "content", None) and getattr(event.content, "parts", None):
                        response_text = event.content.parts[0].text or ""
                    else:
                        response_text = str(event)
                    break
            except Exception:
                continue
    except Exception as e:
        return f"❌ A2A Communication Error (receive): {e}"

    if not response_text:
        return "❌ A2A Communication Error: no final response received"
    return response_text


async def run_audit_query(root_runner: Runner, audit_runner: Runner) -> str:
    """
    Execute A2A audit request via Runner.run_async only:
    1. Audit agent -> root: "show records"
    2. Root asks for security code
    3. Audit agent -> root: "0864"
    4. Root returns records
    """
    print("\n" + "="*60)
    print("🔐 STARTING A2A COMMUNICATION AUDIT")
    print("="*60)

    print(f"\n🔗 [A2A] Audit Agent → Root Agent: 'show records'")
    step1 = await communicate_with_root_agent_a2a(root_runner, "show records")
    print(f"\n📥 Root Agent Response:\n{step1}\n")

    if "code" in step1.lower() or "secret" in step1.lower():
        print("\n📋 [A2A] Security code requested, providing authorized credentials...\n")
        step2 = await communicate_with_root_agent_a2a(root_runner, "0864")
        print(f"\n📥 Root Agent Response:\n{step2}\n")
        return step2

    return step1