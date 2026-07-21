from typing import TypedDict, Annotated, Literal
import operator


class ToolCallTrace(TypedDict):
    tool_name: str
    ok: bool
    error_code: str | None


class AgentMessage(TypedDict):
    """A message from one agent to another in the multi-agent system."""
    sender: str
    recipient: str
    content: str
    action: str  # 'delegate', 'respond', 'request_approval', 'approve', 'reject'


class HumanApprovalRequest(TypedDict):
    """Request for human approval before a critical action."""
    action_description: str
    agent: str
    details: dict
    approved: bool | None  # None = pending, True = approved, False = rejected


class EMaosState(TypedDict):
    # ── Input (set once at graph entry) ──────────────────────────────────────
    user_message: str
    session_id: str
    user_id: str
    org_id: str | None
    project_id: str | None

    # ── Agent Selection ──────────────────────────────────────────────────────
    primary_agent: str  # Which agent to route to: 'pm', 'developer', 'qa', 'docs', 'code_reviewer', 'scrum_master', 'risk_analyst'
    agent_chain: Annotated[list[str], operator.add]  # Which agents have been involved

    # ── Planner output ────────────────────────────────────────────────────────
    subtasks: list[str]
    current_subtask_index: int

    # ── Executor output ───────────────────────────────────────────────────────
    executor_output: str
    tool_trace: Annotated[list[ToolCallTrace], operator.add]

    # ── Reviewer output ───────────────────────────────────────────────────────
    review_decision: str         # 'APPROVED' | 'RETRY'
    review_feedback: str
    retry_count: int

    # ── Multi-Agent Communication ─────────────────────────────────────────────
    messages: Annotated[list[AgentMessage], operator.add]
    current_agent: str           # Which agent is currently active
    delegated_to: list[str]      # Agents that have been delegated tasks
    collaboration_result: str    # Result after multi-agent collaboration

    # ── Human Approval ────────────────────────────────────────────────────────
    pending_approval: HumanApprovalRequest | None
    requires_human_approval: bool

    # ── Accumulated results ───────────────────────────────────────────────────
    completed_outputs: Annotated[list[str], operator.add]

    # ── Memory writer output ──────────────────────────────────────────────────
    memory_summary: str

    # ── Final response ────────────────────────────────────────────────────────
    final_response: str