# Healthcare AI Agent: Project Write-up

### Problem Statement

In the current healthcare landscape, patients often face challenges in getting timely and accurate medical information. It can be difficult to know which type of specialist to consult for a specific symptom, leading to delays in receiving appropriate care. This can cause anxiety for patients and inefficiencies in the healthcare system.

Furthermore, maintaining a secure and easily auditable record of patient interactions is a critical requirement for healthcare providers to ensure compliance, quality of care, and patient safety. Traditional systems for logging patient interactions can be fragmented and difficult to access for auditing purposes.

This project aims to solve these two key problems by providing an intelligent, conversational AI assistant that can guide patients to the right information and specialist, while also ensuring that all interactions are securely and transparently logged.

### Why agents?

An agent-based architecture is the right solution for this problem for several reasons:

*   **Natural Conversation:** Agents can engage in natural, multi-turn conversations, making it easier for patients to describe their symptoms and concerns in their own words.
*   **Task Delegation and Specialization:** A hierarchical agent system allows a "root" agent to handle initial triage and then delegate more complex or specialized queries to sub-agents with specific expertise (e.g., ENT, Gynecology). This mimics the real-world process of consulting a general practitioner who then refers you to a specialist.
*   **Tool Use:** Agents can be equipped with tools to interact with external systems. In this project, agents can access a database to store and retrieve patient information, and they can communicate with other agents (A2A) to securely request data.
*   **Scalability:** The agent-based architecture is modular and scalable. It's easy to add new specialized sub-agents to the system as the range of medical domains expands, without having to rebuild the entire system.
*   **Stateful Interactions:** Agents can maintain the context of a conversation, remembering previous interactions and patient details to provide a more personalized and coherent experience.

### What you created

The project is a hierarchical AI agent system for healthcare applications, built using the Google Agent Development Kit (ADK). The system is designed to assist with patient inquiries and manage patient data securely.

The main components of the system are:

*   **Root Agent (`agent.py`):** The primary entry point of the application. It handles user interactions, orchestrates the sub-agents, and manages the database.
*   **Sub-agents (`subagents/`):** Specialized agents for different medical domains, such as:
    *   General Physician
    *   ENT (Ear, Nose, and Throat)
    *   Gynecology
*   **Database (`healthcare.db`):** A SQLite database used to store patient records and other relevant data.
*   **Audit Server (`audit_server.py`):** A FastAPI web server that provides a read-only interface for auditing patient records from the database.
*   **Government Audit Agent (`agents/gov_audit_agent.py`):** A specialized agent that demonstrates secure Agent-to-Agent (A2A) communication for auditing purposes. It requests data from the root agent, which enforces access control.

#### Architecture Diagram

![Architecture Diagram](architecture.png)

### Demo

Here's a demonstration of how a user would interact with the Healthcare AI Agent:

1.  **Initial Interaction and Patient Registration:**
    ```
    🏥 Welcome to AI Healthcare!
    Type 'exit', 'quit', 'bye', or 'tata' to end the session.
    Type 'show records' to view all patient records (requires security code).
    Type 'audit' to trigger A2A Government Audit Agent communication.
    ============================================================

    📝 You: I have a sore throat
    📝 Are you the patient? (y/n): y
    📝 Please enter your name: John Doe
    📝 Please enter your age: 35
    📝 Please enter your weight in kg (or press Enter to skip): 75
    ✅ Patient record inserted: ID=1, Name=John Doe, Age=35, Weight=75.0

    🤖 Agent Response:
    Hello — I'm the General Physician. I can help triage symptoms and recommend next steps. I see that you have a sore throat. Can you tell me more about your symptoms? For example, when did it start, and do you have a fever?
    ```
2.  **Interaction with a Specialist Sub-agent:**
    ```
    📝 You: It started two days ago, and I don't have a fever. I also have a runny nose.

    🤖 Agent Response:
    Hello — I'm the ENT specialist. I will help with ear, nose, and throat issues. Based on your symptoms of a sore throat and runny nose without a fever, it's likely a common cold. I recommend you get plenty of rest, drink fluids, and you can take over-the-counter pain relievers for the sore throat. If your symptoms worsen or you develop a fever, please consult a doctor.
    ```
3.  **Auditing Patient Records:**
    *   An authorized user can run the `audit_server.py` to start a web server.
    *   Navigating to `http://localhost:8000/audit-report` in a web browser will display a secure, read-only view of all patient records from the `healthcare.db` database.
    *   Alternatively, the `gov_audit_agent.py` can be run to demonstrate secure A2A communication, where the audit agent requests and receives patient records from the root agent.

### The Build

This project was created using the following tools and technologies:

*   **Python:** The core programming language for the project.
*   **Google Agent Development Kit (ADK):** The framework used to build, orchestrate, and deploy the AI agents.
*   **FastAPI:** A modern, fast (high-performance) web framework for building APIs in Python, used for the `audit_server.py`.
*   **SQLAlchemy:** A SQL toolkit and Object-Relational Mapper (ORM) for Python, used for all database interactions with the SQLite database.
*   **Jinja2:** A templating engine for Python, used to separate the HTML presentation logic from the application logic in `audit_server.py`.
*   **pytest:** A testing framework for Python, used to write and run unit tests for the database functions and API endpoints.

The development process involved:

1.  **Initial Setup:** Scaffolding the project with the main agent, sub-agents, and the audit server.
2.  **Documentation and Architecture:** Creating an architecture diagram and a detailed `README.md` to explain the project.
3.  **Code Improvement:** Adding docstrings to the code to improve readability and maintainability.
4.  **Testing:** Writing unit tests for the database functions and the audit server API endpoints to ensure correctness and prevent regressions.
5.  **Refactoring:** Improving the code's structure and readability by refactoring the `interactive_session` function in `agent.py` and using Jinja2 templates in `audit_server.py`.

### If I had more time, this is what I'd do

*   **Add More Sub-agents:** Expand the system with more specialized sub-agents for other medical domains, such as dermatology, cardiology, and pediatrics.
*   **Integrate with Real Medical APIs:** Connect the agents to real-world medical APIs (e.g., for drug information, symptom checkers, or electronic health records) to provide more accurate and useful information.
*   **Improve the Audit Server UI:** Enhance the user interface of the audit server with more advanced features, such as filtering, searching, and data visualization.
*   **Add User Authentication:** Implement a proper user authentication and authorization system for both patients and auditors to enhance security.
*   **More Comprehensive Testing:** Expand the test suite to include more comprehensive end-to-end tests and tests for the agent's conversational abilities.
*   **Deployment:** Deploy the application to a cloud platform so that it can be accessed by users.
*   **Asynchronous Database:** Use an async database driver and session management for all database operations to improve performance.
