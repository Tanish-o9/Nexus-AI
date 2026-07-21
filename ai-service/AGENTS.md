# EMAOS Multi-Agent System

## Overview

EMAOS (Enterprise Multi-Agent Orchestration System) is a sophisticated AI agent framework built on LangGraph that provides 7 specialized autonomous agents for project management, development, quality assurance, and more.

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Router                              │
│              (Routes to specialized agents)                  │
└───────────────┬─────────────────────────────────────────────┘
                │
    ┌───────────┼───────────┬───────────┬───────────┬────────┐
    │           │           │           │           │        │
    ▼           ▼           ▼           ▼           ▼        ▼
┌──────┐   ┌──────────┐ ┌─────┐ ┌─────────┐ ┌──────┐ ┌────────┐
│  PM  │   │Developer │ │ QA  │ │  Docs   │ │Code  │ │Scrum   │
│      │   │          │ │     │ │         │ │Review│ │Master  │
└──┬───┘   └────┬─────┘ └──┬──┘ └────┬────┘ └──┬───┘ └───┬────┘
   │            │           │          │           │         │
   └────────────┴───────────┴──────────┴───────────┴─────────┘
                │
                ▼
    ┌───────────────────────┐
    │  Collaboration Layer  │
    │  (Multi-agent)        │
    └───────────┬───────────┘
                │
    ┌───────────┴───────────┐
    │                       │
    ▼                       ▼
┌─────────────┐   ┌────────────────┐
 │   Human     │   │  Memory Writer │
 │  Approval   │   │  (Long-term)   │
 └─────────────┘   └───────┬────────┘
                            │
                            ▼
                   ┌────────────────┐
                   │ Response       │
                   │ Builder        │
                   └────────────────┘
```

### Agent Types

1. **Project Manager (pm)**
   - Plans projects and delegates tasks
   - Tracks milestones and manages scope
   - Identifies dependencies and blockers
   - Tools: `create_milestone`, `assign_task`, `search_memory`

2. **Developer (developer)**
   - Implements features and writes code
   - Fixes bugs and creates technical solutions
   - Reviews code for quality
   - Tools: `search_code`, `get_file_contents`, `search_memory`

3. **QA Engineer (qa)**
   - Creates test plans and strategies
   - Analyzes bugs and root causes
   - Ensures quality standards
   - Tools: `create_test_plan`, `run_tests`, `search_memory`

4. **Documentation Specialist (docs)**
   - Writes documentation and guides
   - Summarizes meetings
   - Maintains knowledge base
   - Tools: `search_documents` (RAG), `search_memory`

5. **Code Reviewer (code_reviewer)**
   - Reviews pull requests
   - Checks code quality and security
   - Suggests improvements
   - Tools: `get_pr_diff`, `search_memory`

6. **Scrum Master (scrum_master)**
   - Manages sprints and tracks velocity
   - Facilitates ceremonies
   - Removes impediments
   - Tools: `get_sprint_metrics`, `search_memory`

7. **Risk Analyst (risk_analyst)**
   - Identifies and assesses risks
   - Suggests mitigations
   - Tracks risk status
   - Tools: `analyze_risk_area`, `search_memory`

## Key Features

### 1. LangGraph Orchestration

The multi-agent system uses LangGraph for stateful, cyclic workflow orchestration:

```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(EMaosState)
workflow.add_node('agent_router', agent_router_node)
workflow.add_node('pm', pm_node)
# ... add all agent nodes
workflow.add_edge('agent_router', 'pm')  # or other agents
workflow.add_edge('pm', END)
```

### 2. Shared State Management

All agents share a common state object (`EMaosState`) that includes:

- **Input**: `user_message`, `session_id`, `user_id`, `org_id`, `project_id`
- **Agent Selection**: `primary_agent`, `agent_chain`
- **Execution**: `subtasks`, `executor_output`, `tool_trace`
- **Collaboration**: `messages`, `delegated_to`, `collaboration_result`
- **Human Approval**: `pending_approval`, `requires_human_approval`
- **Memory**: `memory_summary`
- **Output**: `final_response`

### 3. Tool Calling

Agents can call tools to interact with external systems:

```python
from langchain_core.tools import tool

@tool
async def search_memory(query: str, top_k: int = 3) -> str:
    """Search long-term memory for relevant past interactions."""
    results = await memory_store.query(...)
    return '\n'.join(f"- {r.content}" for r in results)
```

Tools are bound to the LLM:

```python
tools = _get_agent_tools(agent_type, state)
llm_with_tools = llm.bind_tools(tools)
result = llm_with_tools.invoke(messages)
```

### 4. Multi-Agent Collaboration

Agents can delegate tasks to other agents using @mentions:

```
User: "Create a feature with tests and documentation"
  ↓
PM Agent: "I'll delegate this to the team"
  ↓
  ├─→ Developer: "Implement the feature"
  ├─→ QA: "Create test plan"
  └─→ Docs: "Write documentation"
  ↓
Collaboration Node: Aggregates results
  ↓
Final Response
```

### 5. Long-Term Memory

Each agent has isolated memory with semantic search:

```python
from app.memory.store import memory_store

# Write memory
memory_store.save(
    session_id=session_id,
    user_id=user_id,
    agent_id='pm',
    text='Project milestone completed',
    metadata={'project_id': project_id}
)

# Search memory
results = await memory_store.query(MemoryQueryRequest(
    agent_id='pm',
    session_id=session_id,
    user_id=user_id,
    query='project milestones',
    top_k=3
))
```

Memory is automatically evicted and summarized when it exceeds 50 entries per session.

### 6. Human Approval Workflow

Critical actions require human approval before execution:

```python
CRITICAL_ACTIONS = [
    'delete_project', 'remove_member', 'archive_sprint',
    'merge_pr', 'deploy_production', 'modify_production_data',
]

# In agent execution
for critical in CRITICAL_ACTIONS:
    if critical in content.lower():
        state['requires_human_approval'] = True
        state['pending_approval'] = HumanApprovalRequest(...)
        break
```

### 7. RAG Integration

The Documentation agent can search project documents using hybrid search:

```python
@tool
async def search_documents(query: str) -> str:
    """Search project documents using RAG."""
    from app.services.hybrid_search import hybrid_search
    results = await hybrid_search(query, top_k=3)
    return '\n'.join(f"- {r['content'][:200]}" for r in results)
```

## Usage

### API Endpoint

```bash
POST /api/agents/run
Content-Type: application/json

{
  "message": "Plan a new feature for user authentication",
  "session_id": "session-123",
  "user_id": "user-456",
  "org_id": "org-789",
  "project_id": "project-101"
}
```

### Response

```json
{
  "response": "I'll help you plan the authentication feature...",
  "session_id": "session-123",
  "agents_involved": ["pm", "developer"],
  "requires_approval": false,
  "pending_approval": null
}
```

### Python Usage

```python
from app.agents import emaos_graph, EMaosState

initial_state: EMaosState = {
    'user_message': 'Create a test plan for the login feature',
    'session_id': 'session-123',
    'user_id': 'user-456',
    'org_id': 'org-789',
    'project_id': 'project-101',
    # ... other fields
}

result = await emaos_graph.ainvoke(initial_state)
print(result['final_response'])
```

## Configuration

### Environment Variables

```bash
# AI Service Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.7

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/nexus

# Memory
EMBEDDING_DIMENSION=1536
```

### Agent-Specific Settings

```python
# ai-service/app/config.py
class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0.7
    EMBEDDING_DIMENSION: int = 1536
    MAX_MEMORY_ENTRIES: int = 50
    MEMORY_EVICTION_KEEP: int = 10
```

## Testing

Run the agent tests:

```bash
cd ai-service
pytest tests/test_agents.py -v
```

Run all tests:

```bash
cd ai-service
pytest tests/ -v
```

## Extending the System

### Adding a New Agent

1. **Add agent description** in `app/agents/nodes.py`:

```python
AGENT_DESCRIPTIONS['new_agent'] = 'New Agent — description here'
```

2. **Add system prompt** in `app/prompts/templates.py`:

```python
SYSTEM_AGENT_NEW_AGENT_V1 = """\
You are the New Agent...
"""

PROMPT_REGISTRY['agent_new_agent_v1'] = ChatPromptTemplate.from_messages([
    ('system', SYSTEM_AGENT_NEW_AGENT_V1),
    MessagesPlaceholder(variable_name='history'),
    ('human', '{message}'),
])
```

3. **Add agent node** in `app/agents/nodes.py`:

```python
def new_agent_node(state: EMaosState) -> dict:
    """New agent description."""
    return _agent_executor('new_agent', state)
```

4. **Add to graph** in `app/agents/graph.py`:

```python
workflow.add_node('new_agent', new_agent_node)

# Add routing
for agent in ['pm', 'developer', ..., 'new_agent']:
    workflow.add_conditional_edges(agent, route_after_agent, {...})
```

5. **Add tools** in `app/agents/nodes.py`:

```python
elif agent_type == 'new_agent':
    @tool
    async def new_tool(param: str) -> str:
        """Tool description."""
        return f"Result: {param}"
    
    tools.append(new_tool)
```

### Adding a New Tool

```python
@tool
async def my_tool(param1: str, param2: int = 10) -> str:
    """
    Brief description of what the tool does.
    
    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)
    
    Returns:
        Description of return value
    """
    # Implementation
    result = do_something(param1, param2)
    return result
```

## Best Practices

1. **Agent Isolation**: Each agent has its own memory space. Agent A cannot read Agent B's memories.

2. **Tool Design**: Tools should be:
   - Single-purpose
   - Well-documented with docstrings
   - Idempotent when possible
   - Return descriptive error messages

3. **Prompt Versioning**: Always use versioned prompts (e.g., `agent_pm_v1`) to avoid breaking old sessions.

4. **Critical Actions**: Always flag destructive operations for human approval.

5. **Memory Management**: Monitor memory usage and adjust eviction policies based on session length.

6. **Error Handling**: Wrap tool calls in try-except blocks and return meaningful error messages.

## Monitoring

### Metrics

- Agent routing accuracy
- Tool call success rate
- Memory search relevance
- Human approval rate
- Multi-agent collaboration frequency
- Response latency

### Logging

```python
logger.info(f"Agent {agent_type} executed", extra={
    'session_id': state['session_id'],
    'user_id': state['user_id'],
    'tool_calls': tool_traces,
})
```

## Troubleshooting

### Agent Not Routing Correctly

Check the router prompt in `app/prompts/templates.py` and ensure agent descriptions are clear.

### Tool Calls Failing

Verify tool implementations in `_get_agent_tools()` and `_execute_tool_call()`.

### Memory Not Persisting

Check database connection and ensure `memory_store.save()` is called in `memory_writer_node()`.

### Human Approval Not Triggering

Verify `CRITICAL_ACTIONS` list in `app/agents/nodes.py` includes the action.

## Future Enhancements

- [ ] Streaming responses for real-time agent output
- [ ] Agent performance metrics and A/B testing
- [ ] Custom agent creation UI
- [ ] Agent marketplace for sharing tools
- [ ] Multi-modal agents (image, audio, video)
- [ ] Distributed agent execution
- [ ] Agent learning from human feedback
- [ ] Advanced memory summarization with LLM

## License

Part of the Nexus PM platform.