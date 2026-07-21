"""
Multi-Agent LangGraph
=====================
Orchestrates 7 specialized agents with routing, collaboration,
human approval, and long-term memory.

Graph structure:
  agent_router → [pm|developer|qa|docs|code_reviewer|scrum_master|risk_analyst]
              → collaboration (if delegated)
              → human_approval (if critical action)
              → memory_writer → response_builder
"""

from langgraph.graph import StateGraph, END

from app.agents.state import EMaosState
from app.agents.nodes import (
    agent_router_node,
    pm_node, developer_node, qa_node, docs_node,
    code_reviewer_node, scrum_master_node, risk_analyst_node,
    collaboration_node, human_approval_node,
    memory_writer_node, response_builder_node,
)
from app.agents.edges import (
    route_after_router, route_after_agent,
    route_after_collaboration, route_after_human_approval,
)


def build_emaos_graph() -> StateGraph:
    """Build the multi-agent LangGraph with all 7 specialized agents."""

    workflow = StateGraph(EMaosState)

    # ── Nodes ──────────────────────────────────────────────────────────────────
    workflow.add_node('agent_router', agent_router_node)
    workflow.add_node('pm', pm_node)
    workflow.add_node('developer', developer_node)
    workflow.add_node('qa', qa_node)
    workflow.add_node('docs', docs_node)
    workflow.add_node('code_reviewer', code_reviewer_node)
    workflow.add_node('scrum_master', scrum_master_node)
    workflow.add_node('risk_analyst', risk_analyst_node)
    workflow.add_node('collaboration', collaboration_node)
    workflow.add_node('human_approval', human_approval_node)
    workflow.add_node('memory_writer', memory_writer_node)
    workflow.add_node('response_builder', response_builder_node)

    # ── Edges ──────────────────────────────────────────────────────────────────
    workflow.set_entry_point('agent_router')

    # Router → Specialized agent
    workflow.add_conditional_edges('agent_router', route_after_router, {
        'pm': 'pm',
        'developer': 'developer',
        'qa': 'qa',
        'docs': 'docs',
        'code_reviewer': 'code_reviewer',
        'scrum_master': 'scrum_master',
        'risk_analyst': 'risk_analyst',
    })

    # Agent → Collaboration / Human Approval / Memory
    for agent in ['pm', 'developer', 'qa', 'docs', 'code_reviewer', 'scrum_master', 'risk_analyst']:
        workflow.add_conditional_edges(agent, route_after_agent, {
            'collaboration': 'collaboration',
            'human_approval': 'human_approval',
            'memory_writer': 'memory_writer',
        })

    # Collaboration → Memory / Human Approval
    workflow.add_conditional_edges('collaboration', route_after_collaboration, {
        'memory_writer': 'memory_writer',
        'human_approval': 'human_approval',
    })

    # Human Approval → Memory / Response
    workflow.add_conditional_edges('human_approval', route_after_human_approval, {
        'memory_writer': 'memory_writer',
        'response_builder': 'response_builder',
    })

    # Memory → Response
    workflow.add_edge('memory_writer', 'response_builder')

    # Response → End
    workflow.add_edge('response_builder', END)

    return workflow.compile()


# Singleton graph instance
emaos_graph = build_emaos_graph()