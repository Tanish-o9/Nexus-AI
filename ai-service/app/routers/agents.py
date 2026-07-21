"""
Agent Router
============
FastAPI router for the multi-agent system.
Provides an endpoint to invoke the LangGraph with 7 specialized agents.
"""

import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import verify_internal_secret
from app.agents import emaos_graph, EMaosState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"], dependencies=[Depends(verify_internal_secret)])


@router.post("/run", summary="Run the multi-agent system with a user request")
async def run_agents(body: dict):
    """
    Invoke the multi-agent LangGraph with a user message.
    
    The system automatically routes to the appropriate agent(s) based on
    the request content, supports multi-agent collaboration, human approval
    for critical actions, and long-term memory.
    
    Request body:
    {
        "message": "string",
        "session_id": "string (optional)",
        "user_id": "string",
        "org_id": "string (optional)",
        "project_id": "string (optional)"
    }
    """
    try:
        message = body.get('message', '').strip()
        if not message:
            raise HTTPException(status_code=422, detail='Message is required')

        initial_state: EMaosState = {
            'user_message': message,
            'session_id': body.get('session_id', str(uuid.uuid4())),
            'user_id': body.get('user_id', 'anonymous'),
            'org_id': body.get('org_id'),
            'project_id': body.get('project_id'),
            'primary_agent': '',
            'agent_chain': [],
            'subtasks': [],
            'current_subtask_index': 0,
            'executor_output': '',
            'tool_trace': [],
            'review_decision': '',
            'review_feedback': '',
            'retry_count': 0,
            'messages': [],
            'current_agent': '',
            'delegated_to': [],
            'collaboration_result': '',
            'pending_approval': None,
            'requires_human_approval': False,
            'completed_outputs': [],
            'memory_summary': '',
            'final_response': '',
        }

        result = await emaos_graph.ainvoke(initial_state)

        return {
            'response': result.get('final_response', 'No response generated'),
            'session_id': initial_state['session_id'],
            'agents_involved': result.get('agent_chain', []),
            'requires_approval': result.get('requires_human_approval', False),
            'pending_approval': result.get('pending_approval'),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception('Agent execution failed')
        raise HTTPException(status_code=500, detail=str(e))