import os
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig
from google.genai import types
from . import prompt
from config import MODEL_NAME

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

general_physician_doctor_assistant = LlmAgent(
    model=MODEL_NAME,
    name="general_physician_doctor_assistant",
    description="""Provide assistance to patients with general health concerns, triage symptoms, and recommend next steps.""",
    instruction=(
        "When you respond as the General Physician, begin with a short introduction identifying yourself, e.g. 'Hello — I'm the General Physician. I can help triage symptoms and recommend next steps.'\n\n"
        + prompt.GENERAL_PHYSICIAN_INSTR
        + "\n\nSession access: You have access to a 'fetch_session_state_tool' tool. Call this tool to retrieve session state containing 'patient_name' (the patient), 'interactant_name' (caller), 'patient_age', and 'patient_weight'. When greeting or addressing the caller, use 'interactant_name'. When referencing the patient's record or medical details, use 'patient_name'. Always call fetch_session_state_tool first to obtain this context before proceeding with any medical consultation."
    )
)