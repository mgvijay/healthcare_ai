import os
from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig
from google.genai import types
from . import prompt
from config import MODEL_NAME

# sentinel must match root
SENTINEL_FORWARD = "__FORWARD_TO_ROOT__"

GYNEC_INSTRUCTION = (
    "When you respond as the Gynecology specialist, begin with a short introduction identifying yourself, e.g. 'Hello — I'm the Gynecology specialist. I will help with gynecological health questions.'\n\n"
    + prompt.GYNEC_INSTR
    + "\n\nSecurity routing rule: If the user requests 'show records', 'display records', or 'view records', do NOT attempt to access or describe records. Instead respond exactly with the single token: "
    + f"'{SENTINEL_FORWARD}' (no extra text, no explanation)."
    + "\n\nSession access: You have access to a 'fetch_session_state_tool' tool. Call this tool to retrieve session state containing 'patient_name' (the patient), 'interactant_name' (caller), 'patient_age', and 'patient_weight'. When greeting or addressing the caller, use 'interactant_name'. When referencing the patient's record or medical details, use 'patient_name'. Always call fetch_session_state_tool first to obtain this context before proceeding with any medical consultation."
)

retry_config = types.HttpRetryOptions(
    attempts=5,  # Maximum retry attempts
    exp_base=7,  # Delay multiplier
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

gynec_doctor_assistant = LlmAgent(
    model=MODEL_NAME,
    name="gynec_doctor_assistant",
    description="""Provide assistance to female patients on gynecological health issues,
    including menstrual health, pregnancy, contraception, and menopause.""",
    instruction=GYNEC_INSTRUCTION
)