import sys
import os
import warnings
import pytest

# Ensure repository root is on sys.path so `from config import ...` works during test collection
REPO_ROOT = os.path.dirname(__file__)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from config import MODEL_NAME

# Suppress known deprecation warnings coming from google.genai / pydantic during test collection
warnings.filterwarnings(
    "ignore",
    message=r"_UnionGenericAlias.*",
    category=DeprecationWarning,
    module=r"google\.genai\.types",
)
warnings.filterwarnings(
    "ignore",
    message=r"Using `@model_validator` with mode='after' on a classmethod is deprecated.*",
    category=DeprecationWarning,
)

# Import agents that are instantiated at module import time
from subagents.ent.agent import ent_doctor_assistant
from subagents.gynec.agent import gynec_doctor_assistant
from subagents.generalphysician.agent import general_physician_doctor_assistant
from agents.gov_audit_agent import gov_audit_agent


def agent_model_value(agent_obj):
    """Helper to obtain the underlying model value from an Agent/LlmAgent."""
    # Some ADK Agent implementations may store model as an attribute or under _model
    for attr in ("model", "_model", "_model_name"):
        if hasattr(agent_obj, attr):
            return getattr(agent_obj, attr)
    # Fallback: try attribute access that returns a string representation
    return getattr(agent_obj, "name", None)


@pytest.mark.parametrize("agent_obj", [
    ent_doctor_assistant,
    gynec_doctor_assistant,
    general_physician_doctor_assistant,
    gov_audit_agent,
])
def test_agent_uses_config_model(agent_obj):
    """Assert each agent's configured model matches `config.MODEL_NAME`."""
    model_val = agent_model_value(agent_obj)
    assert model_val == MODEL_NAME, f"Agent {getattr(agent_obj,'name',repr(agent_obj))} uses {model_val!r}, expected {MODEL_NAME!r}"
