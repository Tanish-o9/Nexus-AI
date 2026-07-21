"""
Tests for the multi-agent system
=================================
Tests for agent routing, tool calling, collaboration, and memory.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.agents.state import EMaosState, AgentMessage, HumanApprovalRequest
from app.agents.nodes import (
    agent_router_node,
    pm_node, developer_node, qa_node, docs_node,
    code_reviewer_node, scrum_master_node, risk_analyst_node,
    collaboration_node, human_approval_node,
    memory_writer_node, response_builder_node,
    _get_agent_tools, _execute_tool_call,
)
from app.agents.edges import (
    route_after_router,
    route_after_agent,
    route_after_collaboration,
    route_after_human_approval,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def base_state() -> EMaosState:
    """Base state for testing."""
    return {
        'user_message': 'Test message',
        'session_id': 'test-session-123',
        'user_id': 'test-user-456',
        'org_id': 'test-org-789',
        'project_id': 'test-project-101',
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


@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    mock = Mock()
    mock.content = 'pm'
    mock.tool_calls = None
    return mock


# ── Agent Router Tests ─────────────────────────────────────────────────────────

class TestAgentRouter:
    def test_route_to_pm(self, base_state, mock_llm):
        """Test routing to Project Manager agent."""
        mock_chain = Mock()
        mock_chain.invoke.return_value = Mock(content='pm')
        
        with patch('app.agents.nodes.get_sync_llm', return_value=mock_llm):
            with patch('app.agents.nodes.get_prompt') as mock_get_prompt:
                mock_prompt = Mock()
                mock_prompt.__or__ = Mock(return_value=mock_chain)
                mock_get_prompt.return_value = mock_prompt
                
                result = agent_router_node(base_state)
                
                assert result['primary_agent'] == 'pm'
                assert result['current_agent'] == 'pm'
                assert 'pm' in result['agent_chain']
                assert len(result['messages']) == 1
                assert result['messages'][0]['sender'] == 'router'
                assert result['messages'][0]['recipient'] == 'pm'

    def test_route_to_developer(self, base_state):
        """Test routing to Developer agent."""
        mock_llm = Mock()
        mock_chain = Mock()
        mock_chain.invoke.return_value = Mock(content='developer')
        
        with patch('app.agents.nodes.get_sync_llm', return_value=mock_llm):
            with patch('app.agents.nodes.get_prompt') as mock_get_prompt:
                mock_prompt = Mock()
                mock_prompt.__or__ = Mock(return_value=mock_chain)
                mock_get_prompt.return_value = mock_prompt
                
                result = agent_router_node(base_state)
                
                assert result['primary_agent'] == 'developer'


# ── Agent Executor Tests ───────────────────────────────────────────────────────

class TestAgentExecutors:
    def test_pm_node(self, base_state, mock_llm):
        """Test PM agent execution."""
        mock_llm_with_tools = Mock()
        mock_llm_with_tools.content = 'I will plan the project milestones.'
        mock_llm_with_tools.tool_calls = []
        mock_llm_with_tools.invoke.return_value = mock_llm_with_tools
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        
        with patch('app.agents.nodes.get_sync_llm', return_value=mock_llm):
            with patch('app.agents.nodes.get_prompt') as mock_get_prompt:
                mock_prompt = Mock()
                mock_prompt.format.return_value = "PM system prompt"
                mock_get_prompt.return_value = mock_prompt
                
                result = pm_node(base_state)
                
                assert result['current_agent'] == 'pm'
                assert 'executor_output' in result
                assert len(result['messages']) == 1
                assert result['messages'][0]['sender'] == 'pm'

    def test_developer_node(self, base_state, mock_llm):
        """Test Developer agent execution."""
        mock_llm_with_tools = Mock()
        mock_llm_with_tools.content = 'I will implement the feature.'
        mock_llm_with_tools.tool_calls = []
        mock_llm_with_tools.invoke.return_value = mock_llm_with_tools
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        
        with patch('app.agents.nodes.get_sync_llm', return_value=mock_llm):
            with patch('app.agents.nodes.get_prompt') as mock_get_prompt:
                mock_prompt = Mock()
                mock_prompt.format.return_value = "Developer system prompt"
                mock_get_prompt.return_value = mock_prompt
                
                result = developer_node(base_state)
                
                assert result['current_agent'] == 'developer'
                assert 'executor_output' in result

    def test_qa_node(self, base_state, mock_llm):
        """Test QA agent execution."""
        mock_llm_with_tools = Mock()
        mock_llm_with_tools.content = 'I will create test cases.'
        mock_llm_with_tools.tool_calls = []
        mock_llm_with_tools.invoke.return_value = mock_llm_with_tools
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        
        with patch('app.agents.nodes.get_sync_llm', return_value=mock_llm):
            with patch('app.agents.nodes.get_prompt') as mock_get_prompt:
                mock_prompt = Mock()
                mock_prompt.format.return_value = "QA system prompt"
                mock_get_prompt.return_value = mock_prompt
                
                result = qa_node(base_state)
                
                assert result['current_agent'] == 'qa'


# ── Tool Calling Tests ─────────────────────────────────────────────────────────

class TestToolCalling:
    def test_get_agent_tools(self, base_state):
        """Test that agents get appropriate tools."""
        # PM should get project management tools
        pm_tools = _get_agent_tools('pm', base_state)
        assert len(pm_tools) > 0
        tool_names = [tool.name for tool in pm_tools]
        assert 'search_memory' in tool_names
        
        # Developer should get development tools
        dev_tools = _get_agent_tools('developer', base_state)
        assert len(dev_tools) > 0
        
        # QA should get testing tools
        qa_tools = _get_agent_tools('qa', base_state)
        assert len(qa_tools) > 0

    def test_tools_with_project_context(self, base_state):
        """Test that tools include project context when project_id is available."""
        tools = _get_agent_tools('pm', base_state)
        tool_names = [tool.name for tool in tools]
        
        # Should have project context tools
        assert 'get_project_context' in tool_names
        assert 'get_project_tasks' in tool_names

    def test_tools_without_project_context(self, base_state):
        """Test tools when no project context is available."""
        base_state['project_id'] = None
        tools = _get_agent_tools('pm', base_state)
        tool_names = [tool.name for tool in tools]
        
        # Should not have project context tools
        assert 'get_project_context' not in tool_names
        assert 'get_project_tasks' not in tool_names

    def test_execute_tool_call_memory_search(self, base_state):
        """Test executing memory search tool."""
        tool_call = {
            'name': 'search_memory',
            'args': {'query': 'test query', 'top_k': 3}
        }
        
        with patch('app.memory.store.memory_store.query') as mock_query:
            mock_memory = Mock()
            mock_memory.content = 'Previous conversation about testing'
            mock_query.return_value = [mock_memory]
            
            result = _execute_tool_call(tool_call, base_state)
            
            assert 'Previous conversation about testing' in result
            mock_query.assert_called_once()


# ── Collaboration Tests ────────────────────────────────────────────────────────

class TestCollaboration:
    def test_collaboration_with_delegation(self, base_state):
        """Test collaboration node with delegated agents."""
        base_state['delegated_to'] = ['developer', 'qa']
        base_state['messages'] = [
            AgentMessage(sender='pm', recipient='developer', content='Implement feature', action='delegate'),
            AgentMessage(sender='developer', recipient='user', content='Feature implemented', action='respond'),
        ]
        base_state['executor_output'] = 'PM plan'
        
        result = collaboration_node(base_state)
        
        assert 'collaboration_result' in result
        assert 'developer' in result['collaboration_result']

    def test_collaboration_without_delegation(self, base_state):
        """Test collaboration node without delegation."""
        base_state['executor_output'] = 'Solo agent output'
        
        result = collaboration_node(base_state)
        
        assert result['collaboration_result'] == 'Solo agent output'


# ── Human Approval Tests ───────────────────────────────────────────────────────

class TestHumanApproval:
    def test_approval_required(self, base_state):
        """Test human approval node when approval is required."""
        base_state['requires_human_approval'] = True
        base_state['pending_approval'] = HumanApprovalRequest(
            action_description='delete_project',
            agent='pm',
            details={'action': 'delete_project'},
            approved=None,
        )
        
        result = human_approval_node(base_state)
        
        assert 'final_response' in result
        assert 'HUMAN APPROVAL REQUIRED' in result['final_response']
        assert 'pm' in result['final_response']

    def test_no_approval_required(self, base_state):
        """Test human approval node when no approval is needed."""
        base_state['requires_human_approval'] = False
        base_state['pending_approval'] = None
        
        result = human_approval_node(base_state)
        
        assert result == {}


# ── Memory Writer Tests ────────────────────────────────────────────────────────

class TestMemoryWriter:
    def test_memory_write_success(self, base_state):
        """Test successful memory write."""
        base_state['executor_output'] = 'Test output to remember'
        base_state['current_agent'] = 'pm'
        
        with patch('app.agents.nodes.memory_store.write') as mock_write:
            result = memory_writer_node(base_state)
            
            assert 'memory_summary' in result
            assert result['memory_summary'] == 'Test output to remember'
            mock_write.assert_called_once()

    def test_memory_write_failure(self, base_state):
        """Test memory write failure handling."""
        base_state['executor_output'] = 'Test output'
        
        async def mock_write_failure(*args, **kwargs):
            raise Exception('DB error')
        
        with patch('app.agents.nodes.memory_store.write', side_effect=mock_write_failure):
            result = memory_writer_node(base_state)
            
            assert 'memory_summary' in result
            assert result['memory_summary'] == ''


# ── Response Builder Tests ─────────────────────────────────────────────────────

class TestResponseBuilder:
    def test_build_response_with_collaboration(self, base_state):
        """Test response builder with collaboration result."""
        base_state['agent_chain'] = ['pm', 'developer']
        base_state['collaboration_result'] = 'Collaborative output'
        
        result = response_builder_node(base_state)
        
        assert 'final_response' in result
        assert 'Agents involved: pm, developer' in result['final_response']
        assert 'Collaborative output' in result['final_response']

    def test_build_response_with_approval_warning(self, base_state):
        """Test response builder includes approval warning."""
        base_state['agent_chain'] = ['pm']
        base_state['executor_output'] = 'Output'
        base_state['requires_human_approval'] = True
        
        result = response_builder_node(base_state)
        
        assert 'approval' in result['final_response']

    def test_build_response_with_final_response(self, base_state):
        """Test response builder respects existing final_response."""
        base_state['final_response'] = 'Pre-built response'
        
        result = response_builder_node(base_state)
        
        assert result == {}


# ── Edge Routing Tests ─────────────────────────────────────────────────────────

class TestEdgeRouting:
    def test_route_after_router(self, base_state):
        """Test routing after router node."""
        base_state['primary_agent'] = 'developer'
        assert route_after_router(base_state) == 'developer'
        
        base_state['primary_agent'] = 'qa'
        assert route_after_router(base_state) == 'qa'

    def test_route_after_agent_requires_approval(self, base_state):
        """Test routing when human approval is required."""
        base_state['requires_human_approval'] = True
        base_state['pending_approval'] = HumanApprovalRequest(
            action_description='test', agent='pm', details={}, approved=None
        )
        
        assert route_after_agent(base_state) == 'human_approval'

    def test_route_after_agent_delegation(self, base_state):
        """Test routing when delegation occurred."""
        base_state['requires_human_approval'] = False
        base_state['delegated_to'] = ['developer']
        
        assert route_after_agent(base_state) == 'collaboration'

    def test_route_after_agent_normal(self, base_state):
        """Test normal routing after agent."""
        base_state['requires_human_approval'] = False
        base_state['delegated_to'] = []
        
        assert route_after_agent(base_state) == 'memory_writer'

    def test_route_after_collaboration(self, base_state):
        """Test routing after collaboration."""
        base_state['requires_human_approval'] = True
        assert route_after_collaboration(base_state) == 'human_approval'
        
        base_state['requires_human_approval'] = False
        assert route_after_collaboration(base_state) == 'memory_writer'

    def test_route_after_human_approval_rejected(self, base_state):
        """Test routing after human approval is rejected."""
        base_state['pending_approval'] = HumanApprovalRequest(
            action_description='test', agent='pm', details={}, approved=False
        )
        
        assert route_after_human_approval(base_state) == 'response_builder'

    def test_route_after_human_approval_pending(self, base_state):
        """Test routing after human approval is pending."""
        base_state['pending_approval'] = HumanApprovalRequest(
            action_description='test', agent='pm', details={}, approved=None
        )
        
        assert route_after_human_approval(base_state) == 'memory_writer'


# ── Integration Tests ──────────────────────────────────────────────────────────

class TestAgentIntegration:
    def test_full_agent_chain(self, base_state, mock_llm):
        """Test a full agent chain execution."""
        mock_llm.content = 'I will plan the project.'
        mock_llm_with_tools = Mock()
        mock_llm_with_tools.content = 'I will plan the project.'
        mock_llm_with_tools.tool_calls = []
        mock_llm_with_tools.invoke.return_value = mock_llm_with_tools
        mock_llm.bind_tools.return_value = mock_llm_with_tools
        
        # Mock for router
        mock_chain_router = Mock()
        mock_chain_router.invoke.return_value = Mock(content='pm')
        
        with patch('app.agents.nodes.get_sync_llm', return_value=mock_llm):
            with patch('app.agents.nodes.get_prompt') as mock_get_prompt:
                mock_prompt = Mock()
                mock_prompt.__or__ = Mock(side_effect=[mock_chain_router, mock_chain_router])
                mock_prompt.format.return_value = "system prompt"
                mock_get_prompt.return_value = mock_prompt
                
                # Router
                router_result = agent_router_node(base_state)
                assert router_result['primary_agent'] == 'pm'
                
                # Update state with router result
                base_state.update(router_result)
                
                # Agent execution
                agent_result = pm_node(base_state)
                assert agent_result['current_agent'] == 'pm'
                
                # Collaboration
                base_state.update(agent_result)
                collab_result = collaboration_node(base_state)
                assert 'collaboration_result' in collab_result
                
                # Memory writer
                base_state.update(collab_result)
                with patch('app.agents.nodes.memory_store.write'):
                    memory_result = memory_writer_node(base_state)
                    assert 'memory_summary' in memory_result
                
                # Response builder
                base_state.update(memory_result)
                response_result = response_builder_node(base_state)
                assert 'final_response' in response_result
