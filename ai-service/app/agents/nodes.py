"""
Specialized Agent Nodes
=======================
7 autonomous agents for the Nexus project workspace, each with specific
capabilities, tool access, and collaboration patterns.

Agents:
  1. Project Manager (pm)     — Planning, delegation, milestone tracking
  2. Developer (developer)     — Code generation, task implementation
  3. QA (qa)                   — Test planning, bug analysis
  4. Documentation (docs)      — Doc generation, meeting notes
  5. Code Reviewer (code_reviewer) — PR review, code quality
  6. Scrum Master (scrum_master)   — Sprint management, velocity
  7. Risk Analyst (risk_analyst)   — Risk identification, mitigation
"""

import json
import logging
import re
from typing import Any

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.agents.state import EMaosState, AgentMessage, HumanApprovalRequest
from app.memory.store import memory_store
from app.prompts.templates import get_prompt
from app.services.llm import get_sync_llm

logger = logging.getLogger(__name__)
MAX_RETRIES = 3

# ── Agent Definitions ──────────────────────────────────────────────────────────

AGENT_DESCRIPTIONS = {
    'pm': 'Project Manager — plans projects, delegates tasks, tracks milestones, manages scope',
    'developer': 'Developer — implements features, writes code, fixes bugs, creates technical solutions',
    'qa': 'QA Engineer — creates test plans, analyzes bugs, ensures quality, writes test cases',
    'docs': 'Documentation Specialist — writes docs, summarizes meetings, creates guides',
    'code_reviewer': 'Code Reviewer — reviews pull requests, checks code quality, finds security issues',
    'scrum_master': 'Scrum Master — manages sprints, tracks velocity, facilitates ceremonies',
    'risk_analyst': 'Risk Analyst — identifies risks, assesses impact, suggests mitigations',
}

CRITICAL_ACTIONS = [
    'delete_project', 'remove_member', 'archive_sprint',
    'merge_pr', 'deploy_production', 'modify_production_data',
]


def _parse_numbered_list(text: str) -> list[str]:
    lines = text.strip().split('\n')
    result = []
    for line in lines:
        line = line.strip()
        if re.match(r'^\d+[\.\)]\s*', line):
            result.append(re.sub(r'^\d+[\.\)]\s*', '', line))
    return result if result else [text]


def _check_critical_action(state: EMaosState, action_description: str) -> EMaosState:
    """Check if an action requires human approval."""
    for critical in CRITICAL_ACTIONS:
        if critical in action_description.lower():
            state['requires_human_approval'] = True
            state['pending_approval'] = HumanApprovalRequest(
                action_description=action_description,
                agent=state['current_agent'],
                details={'action': action_description},
                approved=None,
            )
            break
    return state


def _get_agent_system_prompt(agent_type: str, state: EMaosState) -> str:
    """Build a system prompt for a specific agent with context."""
    try:
        # Use agent-specific prompt from registry
        prompt_template = get_prompt(f'agent_{agent_type}_v1')
        # Format the prompt with context
        formatted = prompt_template.format(
            org_id=state.get('org_id', 'N/A'),
            project_id=state.get('project_id', 'N/A'),
            user_id=state.get('user_id', 'N/A'),
        )
        return formatted
    except KeyError:
        # Fallback to generic prompt
        return f'You are the {AGENT_DESCRIPTIONS.get(agent_type, agent_type)} agent.\n\nProject ID: {state.get("project_id", "N/A")}\nOrganization ID: {state.get("org_id", "N/A")}'


# ── Agent Router ───────────────────────────────────────────────────────────────

def agent_router_node(state: EMaosState) -> dict:
    """Route the user message to the appropriate primary agent."""
    try:
        prompt = get_prompt('agent_router_v1')
    except KeyError:
        # Fallback to old behavior if prompt not found
        prompt = get_prompt('agent_router')
    
    llm = get_sync_llm()
    chain = prompt | llm

    result = chain.invoke({
        'user_message': state['user_message'],
        'agents': json.dumps(AGENT_DESCRIPTIONS),
    })

    content = result.content if hasattr(result, 'content') else str(result)
    selected = 'pm'  # default
    for agent_id in AGENT_DESCRIPTIONS:
        if agent_id in content.lower():
            selected = agent_id
            break

    return {
        'primary_agent': selected,
        'current_agent': selected,
        'agent_chain': [selected],
        'messages': [AgentMessage(sender='router', recipient=selected, content=f'Routing task to {selected}', action='delegate')],
    }


# ── Specialized Agent Nodes ────────────────────────────────────────────────────

def _agent_executor(agent_type: str, state: EMaosState) -> dict:
    """Generic executor for any specialized agent with tool calling support."""
    system_prompt = _get_agent_system_prompt(agent_type, state)
    llm = get_sync_llm()

    messages = [SystemMessage(content=system_prompt)]
    messages.append(HumanMessage(content=state['user_message']))

    # Add conversation history if available
    if state.get('messages'):
        for msg in state['messages'][-5:]:
            if msg['sender'] == 'router':
                messages.append(HumanMessage(content=f"[{msg['sender']} → {msg['recipient']}]: {msg['content']}"))
            else:
                messages.append(AIMessage(content=msg['content']))

    # Bind tools to the LLM for this agent
    tools = _get_agent_tools(agent_type, state)
    llm_with_tools = llm.bind_tools(tools) if tools else llm

    result = llm_with_tools.invoke(messages)
    content = result.content if hasattr(result, 'content') else str(result)

    # Handle tool calls if present
    tool_traces = []
    if hasattr(result, 'tool_calls') and result.tool_calls:
        for tool_call in result.tool_calls:
            tool_result = _execute_tool_call(tool_call, state)
            tool_traces.append(tool_result)
            # Append tool result to messages
            messages.append(AIMessage(content=f"Tool {tool_call['name']} returned: {tool_result}"))

    # Check for critical actions
    updates: dict = {
        'executor_output': content,
        'current_agent': agent_type,
        'tool_trace': tool_traces,
        'messages': [AgentMessage(sender=agent_type, recipient='user', content=content[:500], action='respond')],
    }

    # Parse subtasks if present
    subtasks = _parse_numbered_list(content)
    if len(subtasks) > 1:
        updates['subtasks'] = subtasks
        updates['current_subtask_index'] = 0

    # Check for delegation to other agents
    for agent_id in AGENT_DESCRIPTIONS:
        if agent_id != agent_type and f'@{agent_id}' in content.lower():
            updates['delegated_to'] = state.get('delegated_to', []) + [agent_id]
            updates['messages'] = updates.get('messages', []) + [
                AgentMessage(sender=agent_type, recipient=agent_id, content=content[:500], action='delegate')
            ]
            break

    # Check critical actions
    for critical in CRITICAL_ACTIONS:
        if critical in content.lower():
            updates['requires_human_approval'] = True
            updates['pending_approval'] = HumanApprovalRequest(
                action_description=f'{agent_type} wants to: {content[:200]}',
                agent=agent_type,
                details={'output': content[:500]},
                approved=None,
            )
            break

    return updates


def pm_node(state: EMaosState) -> dict:
    """Project Manager agent — planning, delegation, milestone tracking."""
    return _agent_executor('pm', state)


def developer_node(state: EMaosState) -> dict:
    """Developer agent — code generation, task implementation."""
    return _agent_executor('developer', state)


def qa_node(state: EMaosState) -> dict:
    """QA agent — test planning, bug analysis."""
    return _agent_executor('qa', state)


def docs_node(state: EMaosState) -> dict:
    """Documentation agent — doc generation, meeting notes."""
    return _agent_executor('docs', state)


def code_reviewer_node(state: EMaosState) -> dict:
    """Code Reviewer agent — PR review, code quality."""
    return _agent_executor('code_reviewer', state)


def scrum_master_node(state: EMaosState) -> dict:
    """Scrum Master agent — sprint management, velocity."""
    return _agent_executor('scrum_master', state)


def risk_analyst_node(state: EMaosState) -> dict:
    """Risk Analyst agent — risk identification, mitigation."""
    return _agent_executor('risk_analyst', state)


# ── Tool Calling ────────────────────────────────────────────────────────────────

def _get_agent_tools(agent_type: str, state: EMaosState) -> list:
    """Return available tools for a specific agent type."""
    from langchain_core.tools import tool
    
    tools = []
    
    # All agents get access to memory search
    @tool
    async def search_memory(query: str, top_k: int = 3) -> str:
        """Search long-term memory for relevant past interactions."""
        try:
            from app.memory.store import memory_store
            from app.schemas.memory import MemoryQueryRequest
            results = await memory_store.query(MemoryQueryRequest(
                agent_id=agent_type,
                session_id=state['session_id'],
                user_id=state['user_id'],
                query=query,
                top_k=top_k
            ))
            if results:
                return '\n'.join(f"- {r.content}" for r in results)
            return "No relevant memories found."
        except Exception as e:
            return f"Memory search failed: {e}"
    
    tools.append(search_memory)
    
    # Project context tools (if project_id is available)
    if state.get('project_id'):
        @tool
        async def get_project_context() -> str:
            """Get current project details and context."""
            try:
                # This would integrate with the backend API
                return f"Project ID: {state['project_id']}, Org ID: {state.get('org_id', 'N/A')}"
            except Exception as e:
                return f"Failed to get project context: {e}"
        
        @tool
        async def get_project_tasks(status: str = "all") -> str:
            """Get tasks for the current project."""
            try:
                # This would integrate with the backend API
                return f"Project tasks (status: {status}): [Would fetch from backend API]"
            except Exception as e:
                return f"Failed to get tasks: {e}"
        
        tools.extend([get_project_context, get_project_tasks])
    
    # Agent-specific tools
    if agent_type == 'pm':
        @tool
        async def create_milestone(name: str, due_date: str) -> str:
            """Create a new project milestone."""
            return f"Would create milestone '{name}' due {due_date}"
        
        @tool
        async def assign_task(task_id: str, assignee: str) -> str:
            """Assign a task to a team member."""
            return f"Would assign task {task_id} to {assignee}"
        
        tools.extend([create_milestone, assign_task])
    
    elif agent_type == 'developer':
        @tool
        async def search_code(query: str) -> str:
            """Search codebase for relevant code."""
            return f"Would search codebase for: {query}"
        
        @tool
        async def get_file_contents(file_path: str) -> str:
            """Get contents of a specific file."""
            return f"Would read file: {file_path}"
        
        tools.extend([search_code, get_file_contents])
    
    elif agent_type == 'qa':
        @tool
        async def create_test_plan(feature: str) -> str:
            """Create a test plan for a feature."""
            return f"Would create test plan for: {feature}"
        
        @tool
        async def run_tests(test_suite: str) -> str:
            """Run a test suite."""
            return f"Would run tests: {test_suite}"
        
        tools.extend([create_test_plan, run_tests])
    
    elif agent_type == 'docs':
        @tool
        async def search_documents(query: str) -> str:
            """Search project documents using RAG."""
            try:
                from app.services.hybrid_search import hybrid_search
                results = await hybrid_search(query, top_k=3)
                if results:
                    return '\n'.join(f"- {r['content'][:200]}" for r in results)
                return "No documents found."
            except Exception as e:
                return f"Document search failed: {e}"
        
        tools.append(search_documents)
    
    elif agent_type == 'code_reviewer':
        @tool
        async def get_pr_diff(pr_number: int) -> str:
            """Get PR diff for review."""
            return f"Would fetch PR #{pr_number} diff"
        
        tools.append(get_pr_diff)
    
    elif agent_type == 'scrum_master':
        @tool
        async def get_sprint_metrics(sprint_id: str) -> str:
            """Get sprint metrics and velocity."""
            return f"Would fetch metrics for sprint: {sprint_id}"
        
        tools.append(get_sprint_metrics)
    
    elif agent_type == 'risk_analyst':
        @tool
        async def analyze_risk_area(area: str) -> str:
            """Analyze risks in a specific area."""
            return f"Would analyze risks in: {area}"
        
        tools.append(analyze_risk_area)
    
    return tools


def _execute_tool_call(tool_call: dict, state: EMaosState) -> str:
    """Execute a tool call and return the result."""
    try:
        tool_name = tool_call['name']
        tool_args = tool_call.get('args', {})
        
        # Import and execute the tool
        # This is a simplified version - in production, you'd have proper tool registry
        if tool_name == 'search_memory':
            from app.memory.store import memory_store
            from app.schemas.memory import MemoryQueryRequest
            import asyncio
            
            results = asyncio.run(memory_store.query(MemoryQueryRequest(
                agent_id=state.get('current_agent', 'system'),
                session_id=state['session_id'],
                user_id=state['user_id'],
                query=tool_args.get('query', ''),
                top_k=tool_args.get('top_k', 3)
            )))
            return '\n'.join(f"- {r.content}" for r in results) if results else "No memories found"
        
        # Add more tool implementations here
        return f"Tool {tool_name} executed with args: {tool_args}"
    except Exception as e:
        return f"Tool execution failed: {e}"


# ── Collaboration Node ─────────────────────────────────────────────────────────

def collaboration_node(state: EMaosState) -> dict:
    """Facilitate multi-agent collaboration by aggregating results."""
    messages = state.get('messages', [])
    delegated = state.get('delegated_to', [])

    if not delegated:
        return {'collaboration_result': state.get('executor_output', '')}

    # Summarize collaboration
    summary_parts = []
    for msg in messages:
        if msg['action'] == 'respond':
            summary_parts.append(f"{msg['sender']}: {msg['content'][:300]}")

    return {
        'collaboration_result': '\n\n'.join(summary_parts) if summary_parts else state.get('executor_output', ''),
    }


# ── Human Approval Node ────────────────────────────────────────────────────────

def human_approval_node(state: EMaosState) -> dict:
    """Check if human approval is needed and handle the pending request."""
    if not state.get('requires_human_approval') or not state.get('pending_approval'):
        return {}

    pending = state['pending_approval']
    # In a real system, this would wait for a human response via WebSocket/polling
    # For now, we flag it and include it in the response
    return {
        'final_response': (
            f"[HUMAN APPROVAL REQUIRED]\n"
            f"Agent: {pending['agent']}\n"
            f"Action: {pending['action_description']}\n"
            f"Please review and approve/reject this action."
        ),
    }


# ── Memory Writer ──────────────────────────────────────────────────────────────

def memory_writer_node(state: EMaosState) -> dict:
    """Persist conversation summary to long-term memory."""
    try:
        summary = state.get('executor_output', '')[:500]
        if summary:
            import asyncio
            asyncio.run(memory_store.write(
                agent_id=state.get('current_agent', 'system'),
                session_id=state['session_id'],
                user_id=state['user_id'],
                content=summary,
                metadata={
                    'project_id': state.get('project_id'),
                    'org_id': state.get('org_id'),
                    'agent_chain': state.get('agent_chain', []),
                },
            ))
        return {'memory_summary': summary}
    except Exception as e:
        logger.warning('Memory write failed: %s', e)
        return {'memory_summary': ''}


# ── Response Builder ───────────────────────────────────────────────────────────

def response_builder_node(state: EMaosState) -> dict:
    """Build the final response from agent outputs."""
    if state.get('final_response'):
        return {}

    parts = []
    agent_chain = state.get('agent_chain', [])
    if agent_chain:
        parts.append(f"Agents involved: {', '.join(agent_chain)}")

    if state.get('collaboration_result'):
        parts.append(state['collaboration_result'])
    elif state.get('executor_output'):
        parts.append(state['executor_output'])

    if state.get('requires_human_approval'):
        parts.append('\n⚠️ Some actions require your approval before proceeding.')

    return {'final_response': '\n\n'.join(parts)}