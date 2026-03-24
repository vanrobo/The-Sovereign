
# The Sovereign (v1)

A stateful, autonomous agent framework designed to orchestrate LLM-driven task execution in sandboxed Linux environments.

### Overview
This project provides an autonomous orchestration layer that bridges natural language goals with deterministic system execution. Unlike high-level frameworks, this agent is built from first principles to provide granular control over the agentic loop, state management, and command validation.

### Key Capabilities
*   **Stateful Reasoning:** Manages multi-turn conversation history and execution outcomes to maintain task continuity.
*   **Structured Output:** Enforces strict JSON schemas for all agent plans to ensure deterministic execution.
*   **Check-Act-Verify:** Implements a multi-step execution pattern (Check existence -> Act -> Verify output) to minimize runtime failures.
*   **Sandboxed Execution:** Designed to operate within a controlled Linux VM environment, with built-in hooks for privilege-level management and audit logging.

### Architecture
The system uses a class-based orchestration approach:
*   **`Ai` Class:** The core engine. It manages the Gemini API client, maintains the session state, and implements the `with` statement context manager for lifecycle management.
*   **Memory System:** Stores and retrieves `conversation_history` and `step_outcomes` using a JSON-based persistent memory, allowing the agent to reference past actions in subsequent turns.
*   **Command Sanitization:** All shell commands are routed through the `perform_execute_shell` method, providing a central point for validation and error handling.

### Quick Start
1. Create a `.env` file with your `API_KEY`.
2. Ensure you have the `google-genai` library installed.
3. Run `python main.py` to initialize the agent.

### Current Implementation Status
*   **CLI Orchestration:** Functional.
*   **JSON-Schema Enforcement:** Active (via Gemini `response_mime_type`).
*   **Persistent State:** JSON-based history and outcome tracking implemented.
*   **Safety Layer:** Basic execution audit implemented.

---
