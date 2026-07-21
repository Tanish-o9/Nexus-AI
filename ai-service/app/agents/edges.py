"""
Agent Graph Edges
=================
Conditional routing logic for the multi-agent LangGraph.
Routes between specialized agents based on task type, delegation,
and human approval requirements.
"""

from typing import Literal

from app.agents.state import EMaosState


def route_after_router(state: EMaosState) -> Literal['pm', 'developer', 'qa', 'docs', 'code_reviewer', 'scrum_master', 'risk_analyst']:
    """Route to the appropriate primary agent based on router output."""
    agent = state.get('primary_agent', 'pm')
    return agent


def route_after_agent(state: EMaosState) -> Literal['collaboration', 'human_approval', 'memory_writer']:
    """Route after an agent completes its execution."""
    if state.get('requires_human_approval') and state.get('pending_approval', {}).get('approved') is None:
        return 'human_approval'
    if state.get('delegated_to'):
        return 'collaboration'
    return 'memory_writer'


def route_after_collaboration(state: EMaosState) -> Literal['memory_writer', 'human_approval']:
    """Route after multi-agent collaboration."""
    if state.get('requires_human_approval'):
        return 'human_approval'
    return 'memory_writer'


def route_after_human_approval(state: EMaosState) -> Literal['memory_writer', 'response_builder']:
    """Route after human approval check."""
    pending = state.get('pending_approval')
    if pending and pending.get('approved') is False:
        # Human rejected — skip to response
        return 'response_builder'
    return 'memory_writer'