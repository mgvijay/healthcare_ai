"""
Main Agent Module for Healthcare Application using Google ADK
Supports A2A (Agent-to-Agent) communication with gov_audit_agent
"""

import os
import logging
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from config import MODEL_NAME, SECURITY_CODE
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import inspect
from google.adk.tools import FunctionTool
from datetime import datetime
from sqlalchemy.sql import func

from subagents.ent.agent import ent_doctor_assistant
from subagents.gynec.agent import gynec_doctor_assistant
from subagents.generalphysician.agent import general_physician_doctor_assistant
# Import the root agent prompt from separate file
from prompts.root_prompt import ROOT_AGENT_INSTRUCTION

# Load environment variables
load_dotenv()
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'ERROR'))
logger = logging.getLogger(__name__)

# Configuration
USER_ID = os.getenv("PATIENT_ID", "patient_001")

# ============================================
# Database Setup
# ============================================
engine = create_engine('sqlite:///healthcare.db', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)

class PatientDetails(Base):
    __tablename__ = "patient_details"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False) 
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    def __init__(self, name, age, weight=None):
        self.name = name
        self.age = age
        self.weight = weight
    
    def __repr__(self):
        return f"<PatientDetails(id={self.id}, name='{self.name}', age={self.age}, weight={self.weight})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'age': self.age,
            'weight': self.weight,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Create all tables
Base.metadata.create_all(engine)
print("✅ Database and tables created successfully.")


def ensure_weight_column(engine):
    """
    Checks if the 'weight' column exists in the 'patient_details' table and adds it if it is missing.

    This function is a lightweight database migration utility that ensures the schema is up-to-date
    with the application's requirements. It uses SQLAlchemy's inspection capabilities to check for the
    presence of the column before attempting to add it.

    Args:
        engine: The SQLAlchemy engine instance for the database connection.
    """
    try:
        inspector = inspect(engine)
        if "patient_details" not in inspector.get_table_names():
            return

        cols = [c["name"] for c in inspector.get_columns("patient_details")]
        if "weight" in cols:
            return

        print("⚙️  Migrating database: adding 'weight' column to patient_details...")
        with engine.connect() as conn:
            conn.exec_driver_sql("ALTER TABLE patient_details ADD COLUMN weight FLOAT;")
        print("✅ Migration complete: 'weight' column added.")
    except Exception as e:
        print(f"⚠️  Migration skipped or failed: {e}")


# Run lightweight migration to add weight column if needed
ensure_weight_column(engine)


# ============================================
# Database Helper Functions
# ============================================
def insert_patient_record(name: str, age: int, weight: float = None) -> PatientDetails:
    """
    Inserts a new patient record into the database.

    Args:
        name: The name of the patient.
        age: The age of the patient.
        weight: The weight of the patient (optional).

    Returns:
        The created PatientDetails object, or None if an error occurred.
    """
    session = Session()
    try:
        patient = PatientDetails(name=name, age=age, weight=weight)
        session.add(patient)
        session.commit()
        print(f"✅ Patient record inserted: ID={patient.id}, Name={name}, Age={age}, Weight={weight}")
        return patient
    except Exception as e:
        session.rollback()
        print(f"❌ Error inserting record: {e}")
        return None
    finally:
        session.close()


def get_all_patient_records() -> list:
    """
    Retrieves all patient records from the database.

    Returns:
        A list of PatientDetails objects.
    """
    session = Session()
    try:
        patients = session.query(PatientDetails).all()
        return patients
    except Exception as e:
        print(f"❌ Error retrieving records: {e}")
        return []
    finally:
        session.close()


def display_patient_records() -> str:
    """
    Formats all patient records into a string table.

    Returns:
        A formatted string representing the patient records in a table,
        or a message if no records are found.
    """
    patients = get_all_patient_records()
    
    if not patients:
        return "📊 No patient records found in the database."
    
    output = "\n" + "="*50 + "\n"
    output += "📊 Patient Records in Database\n"
    output += "="*50 + "\n"
    output += f"{'ID':<5} {'Name':<25} {'Age':<6} {'Weight':<8}\n"
    output += "-"*50 + "\n"
    
    for patient in patients:
        weight_disp = f"{patient.weight}" if getattr(patient, 'weight', None) is not None else "-"
        output += f"{patient.id:<5} {patient.name:<25} {patient.age:<6} {weight_disp:<8}\n"
    
    output += "="*50 + "\n"
    return output


def get_patient_records_json() -> dict:
    """
    Retrieves all patient records and returns them in a JSON-serializable format.

    Returns:
        A dictionary containing the count of records and a list of patient records as dictionaries.
    """
    patients = get_all_patient_records()
    return {
        'count': len(patients),
        'records': [p.to_dict() for p in patients]
    }


def show_patient_records_secure(security_code: str) -> str:
    """
    Securely displays patient records only if the correct security code is provided.

    This function is exposed to the agent as a tool and is intended to be used for
    Agent-to-Agent (A2A) communication.

    Args:
        security_code: The security code provided by the calling agent.

    Returns:
        A formatted string of patient records if the code is correct, otherwise an access denied message.
    """
    if security_code == SECURITY_CODE:
        records = display_patient_records()
        print(f"\n✅ [A2A] Security code validated. Patient records accessed by authorized agent.")
        return records
    else:
        print(f"\n❌ [A2A] Invalid security code attempt. Access denied.")
        return "❌ Access Denied: Invalid security code. Please provide the correct code to view patient records."


SENTINEL_FORWARD = "__FORWARD_TO_ROOT__"

# Ensure all imported sub-agents return the sentinel when asked to "show records".
def _ensure_subagent_sentinel(sub_agent):
    """
    Ensures that a sub-agent has a rule to forward record-related requests to the root agent.

    This function modifies the sub-agent's instruction to include a rule that triggers a
    sentinel value (`__FORWARD_TO_ROOT__`) when the user asks to see records. This allows the
    root agent to handle the secure display of records.

    Args:
        sub_agent: The sub-agent to modify.
    """
    sentinel_rule = (
        "\n\nSecurity routing rule: If the user requests 'show records', 'display records', or 'view records',"
        " do NOT attempt to access or describe records. Instead respond exactly with the single token: "
        f"'{SENTINEL_FORWARD}' (no extra text, no explanation)."
    )
    try:
        # Only append if the agent has an instruction attribute and rule not already present.
        if hasattr(sub_agent, "instruction") and sentinel_rule.strip() not in (sub_agent.instruction or ""):
            # Mutate in-place so the Agent used by Runner has the updated instruction.
            sub_agent.instruction = (sub_agent.instruction or "") + sentinel_rule
    except Exception:
        # Fail silently — don't break startup if a sub-agent is not mutable.
        pass

# Apply sentinel rule to all loaded sub-agents before creating the root agent
_ensure_subagent_sentinel(ent_doctor_assistant)
_ensure_subagent_sentinel(gynec_doctor_assistant)
_ensure_subagent_sentinel(general_physician_doctor_assistant)

def root_handle_show_records():
    """
    Prompts the user for a security code and displays patient records if the code is correct.

    This function is intended to be called only by the root agent's interactive session when a
    sub-agent forwards a request to show records.
    """
    code = input("🔐 Enter security code to view records: ").strip()
    result = show_patient_records_secure(code)
    print("\n" + result + "\n")


async def set_session_state(session_service, session_id: str, state: dict, app_name: str = "healthcare"):
    """
    Sets session-level state in a resilient way across different SessionService implementations.

    This function attempts to set the session state using various common method names and fallbacks
    to ensure compatibility with different session service implementations.

    Args:
        session_service: The session service instance.
        session_id: The ID of the session to update.
        state: A dictionary containing the state to set.
        app_name: The name of the application (defaults to "healthcare").
    """
    if not state:
        return

    # Try a few known method names and call them (sync or async)
    candidates = [
        ("set_state", ("app_name", "session_id", "state")),
        ("set_state", ("session_id", "state")),
        ("set_session_state", ("app_name", "session_id", "state")),
        ("update_session", ("app_name", "session_id", "state")),
        ("update_session_state", ("session_id", "state")),
    ]

    for method_name, params in candidates:
        method = getattr(session_service, method_name, None)
        if not callable(method):
            continue

        try:
            # Build kwargs according to params tuple
            kwargs = {}
            for p in params:
                if p == "app_name":
                    kwargs[p] = app_name
                elif p == "session_id":
                    kwargs[p] = session_id
                elif p == "state":
                    kwargs[p] = state

            result = method(**kwargs)
            # Await if coroutine
            if hasattr(result, "__await__"):
                await result
            return
        except TypeError:
            # Signature mismatch; try next candidate
            continue
        except Exception:
            # Ignore other errors and try other fallbacks
            continue

    # Try to set into a private storage if available
    try:
        if hasattr(session_service, "_sessions") and isinstance(getattr(session_service, "_sessions"), dict):
            sess = session_service._sessions.get(session_id) or {}
            sess_state = sess.get("state", {}) or {}
            sess_state.update(state)
            sess["state"] = sess_state
            session_service._sessions[session_id] = sess
            return
    except Exception:
        pass

    # As a last resort, try recreating the session with a state parameter (some impls accept it)
    try:
        maybe = session_service.create_session(app_name=app_name, user_id=USER_ID, session_id=session_id, state=state)
        if hasattr(maybe, "__await__"):
            await maybe
    except Exception:
        # Give up silently; session state is best-effort
        return


async def get_session_state(session_service, session_id: str, app_name: str = "healthcare") -> dict:
    """
    Tries to read session state in a resilient way from the session service.

    This function attempts to get the session state using various common method names and fallbacks
    to ensure compatibility with different session service implementations.

    Args:
        session_service: The session service instance.
        session_id: The ID of the session to read.
        app_name: The name of the application (defaults to "healthcare").

    Returns:
        A dictionary containing the session state, or an empty dictionary if not available.
    """
    # Try common method names
    candidates = [
        ("get_state", ("app_name", "session_id")),
        ("get_state", ("session_id",)),
        ("get_session", ("app_name", "session_id")),
        ("get_session", ("session_id",)),
        ("read_session", ("session_id",)),
    ]

    for method_name, params in candidates:
        method = getattr(session_service, method_name, None)
        if not callable(method):
            continue
        try:
            kwargs = {}
            for p in params:
                if p == "app_name":
                    kwargs[p] = app_name
                elif p == "session_id":
                    kwargs[p] = session_id
            maybe = method(**kwargs)
            if hasattr(maybe, "__await__"):
                result = await maybe
            else:
                result = maybe
            # If result looks like a mapping, try to extract 'state' key
            if isinstance(result, dict):
                return result.get("state", result)
        except Exception:
            continue

    # Try private storage fallback
    try:
        if hasattr(session_service, "_sessions") and isinstance(getattr(session_service, "_sessions"), dict):
            sess = session_service._sessions.get(session_id) or {}
            return sess.get("state", {}) or {}
    except Exception:
        pass

    return {}

async def get_runner() -> Runner:
    """
    Initializes and returns the healthcare agent runner.

    This function sets up the root agent, its sub-agents, and the session service.
    It also creates a tool for fetching session state and attaches it to the agents.

    Returns:
        A tuple containing the Runner instance and the session service instance.
    """
    
    root_agent = Agent(
        name="healthcare_agent_app",
        model=MODEL_NAME,
        description="The first agent that the patient meets when he/she enters the healthcare system.",
        instruction=ROOT_AGENT_INSTRUCTION,
        tools=[FunctionTool(show_patient_records_secure)],
        sub_agents=[ent_doctor_assistant, gynec_doctor_assistant, general_physician_doctor_assistant]
    )
    
    print("✅ Healthcare Agent App instantiated successfully.")

    # Use InMemorySessionService for session management
    session_service = InMemorySessionService()
    
    runner = Runner(agent=root_agent, app_name="healthcare", session_service=session_service)
    
    print("✅ In-memory session service initialized.")
    
    # Create session once at startup
    try:
        await session_service.create_session(app_name="healthcare", user_id=USER_ID, session_id="session_123")
        print("✅ Session 'session_123' created successfully.")
    except Exception as e:
        print(f"⚠️  Session creation note: {e}")

    print("✅ Runner created!")

    # Create a FunctionTool that allows agents to fetch session state at runtime.
    # The tool function accepts tool_context: ToolContext which ADK injects automatically.
    # This gives direct access to session.state without async operations.
    def fetch_session_state_tool(tool_context) -> dict:
        """Fetch current session state including patient_name, interactant_name, patient_age, patient_weight.
        
        ADK automatically injects tool_context when this tool is called by an agent.
        """
        try:
            return dict(tool_context.state)
        except Exception:
            return {}

    fetch_tool = FunctionTool(fetch_session_state_tool)

    # Attach the fetch tool to the root agent and also to each sub-agent so they can invoke it.
    try:
        root_agent.tools = (getattr(root_agent, "tools", []) or []) + [fetch_tool]
    except Exception:
        pass

    for sa in (ent_doctor_assistant, gynec_doctor_assistant, general_physician_doctor_assistant):
        try:
            sa.tools = (getattr(sa, "tools", []) or []) + [fetch_tool]
        except Exception:
            continue
    return runner, session_service


async def main(query: str, runner: Runner) -> None:
    """
    Executes a single query through the healthcare agent.

    This function sends a query to the agent runner and prints the final response.
    It also handles the special case where a sub-agent forwards a request to show records.

    Args:
        query: The user's query to the agent.
        runner: The Runner instance for the agent.
    """
    
    content = types.Content(role="user", parts=[types.Part(text=query)])
    
    events = runner.run_async(
        new_message=content,
        user_id=USER_ID,
        session_id="session_123",
    )

    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text.strip()
            # If a sub-agent returned the sentinel, take control and run the secure flow.
            if final_response == SENTINEL_FORWARD:
                root_handle_show_records()
            else:
                print(f"\n🤖 Agent Response:\n{final_response}")


async def interactive_session(runner: Runner, session_service: InMemorySessionService) -> None:
    """
    Runs an interactive chat session with the healthcare agent.

    This function provides a command-line interface for interacting with the agent.
    It handles user input, special commands ('exit', 'audit', 'show session'), and the initial
    patient information gathering flow.

    Args:
        runner: The Runner instance for the agent.
        session_service: The session service instance.
    """
    
    def _get_patient_details():
        """Helper to collect patient's name, age, and optional weight with validation."""
        patient_name = None
        patient_age = None
        patient_weight = None

        while not patient_name:
            patient_name = input("📝 Please enter the patient's name: ").strip()
            if not patient_name:
                print("⚠️  Name cannot be empty. Please try again.")

        while patient_age is None:
            try:
                patient_age = int(input("📝 Please enter the patient's age: ").strip())
                if patient_age < 0 or patient_age > 150:
                    print("⚠️  Please enter a valid age (0-150).")
                    patient_age = None
            except ValueError:
                print("⚠️  Age must be a number. Please try again.")
        
        while patient_weight is None:
            w = input("📝 Please enter the patient's weight in kg (or press Enter to skip): ").strip()
            if w == "":
                patient_weight = None
                break
            try:
                patient_weight = float(w)
            except ValueError:
                print("⚠️  Weight must be a number or blank to skip. Please try again.")
        
        return patient_name, patient_age, patient_weight
    
    def _get_interactant_name():
        """Helper to collect the interactant's name with validation."""
        interactant_name = None
        while not interactant_name:
            interactant_name = input("📝 Please enter your name (who is calling on behalf of the patient): ").strip()
            if not interactant_name:
                print("⚠️  Caller name cannot be empty. Please try again.")
        return interactant_name

    async def _handle_first_interaction(current_user_query: str):
        """Orchestrates the first interaction to gather patient and interactant details."""
        nonlocal first_interaction # Only first_interaction needs to be nonlocal
        
        # Local to this function
        patient_name = None 
        patient_age = None
        patient_weight = None 
        interactant_name = None 

        resp = input("📝 Are you the patient? (y/n): ").strip().lower()
        if resp.startswith("y"):
            patient_name, patient_age, patient_weight = _get_patient_details()
            interactant_name = patient_name
            enriched_query = f"My name is {patient_name}. I am {patient_age} years old. {current_user_query}"
        else:
            patient_name, patient_age, patient_weight = _get_patient_details() # Collect for the patient
            interactant_name = _get_interactant_name() # Collect for the caller
            enriched_query = (
                f"This is {interactant_name} calling on behalf of {patient_name} (age {patient_age}"
                + (f", weight {patient_weight}kg" if patient_weight is not None else "")
                + f"). {current_user_query}"
            )
        
        # Insert patient record into database
        insert_patient_record(patient_name, patient_age, patient_weight)

        # Persist patient + interactant info in session state
        try:
            await set_session_state(
                session_service,
                "session_123",
                {
                    "patient_name": patient_name,
                    "patient_age": patient_age,
                    "patient_weight": patient_weight,
                    "interactant_name": interactant_name,
                },
            )
        except Exception as e:
            logger.error(f"Error setting session state: {e}")

        first_interaction = False
        return enriched_query
    
    print("\n" + "="*60)
    print("🏥 Welcome to AI Healthcare!")
    print("Type 'exit', 'quit', 'bye', or 'tata' to end the session.")
    print("Type 'show records' to view all patient records (requires security code).")
    print("Type 'audit' to trigger A2A Government Audit Agent communication.")
    print("="*60 + "\n")
    
    first_interaction = True
    
    while True:
        try:
            user_query = input("\n📝 You: ").strip()
            
            if user_query.lower() in ["exit", "quit", "bye", "tata"]:
                print("\n👋 Thank you for using the Healthcare Agent. Goodbye!")
                break
            
            if user_query.lower() == "audit":
                print("\n🔐 Initiating A2A (Agent-to-Agent) communication with Government Audit Agent...")
                print("⏳ Please wait...\n")
                
                # Import and run the A2A audit
                try:
                    from agents.gov_audit_agent import run_audit_query, get_audit_runner
                    audit_runner, audit_session = await get_audit_runner()
                    audit_response = await run_audit_query(runner, audit_runner)
                    print(f"\n📊 Audit records available at: http://localhost:8000/audit-report\n")
                except Exception as e:
                    print(f"❌ A2A Communication Error: {e}")
                continue

            if user_query.lower() == "show session":
                try:
                    state = asyncio.run(get_session_state(session_service, "session_123"))
                except Exception:
                    # If we're already inside the event loop, await
                    state = await get_session_state(session_service, "session_123")
                print("\n🔎 Current session state:\n", state)
                continue
            
            if not user_query:
                print("⚠️  Please enter a valid question.")
                continue
            
            if "show records" in user_query.lower() or "display records" in user_query.lower() or "view records" in user_query.lower():
                root_handle_show_records()
                continue # Skip remaining logic for this turn
            
            if first_interaction:
                enriched_query = await _handle_first_interaction(user_query)
                await main(enriched_query, runner)
            else:
                await main(user_query, runner)

            
        except KeyboardInterrupt:
            print("\n\n👋 Session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    try:
        runner, session_service = asyncio.run(get_runner())
        asyncio.run(interactive_session(runner, session_service))
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        exit(1)