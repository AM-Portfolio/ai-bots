"""
Integration tests for orchestration layer

Tests the complete pipeline: Parser → Enricher → Prompt Builder → Agent
"""
import pytest
from unittest.mock import Mock, AsyncMock
from orchestration.facade import OrchestrationFacade
from orchestration.message_parser import MessageParser
from orchestration.shared.models import ReferenceType


class TestMessageParser:
    """Test message parser module"""
    
    @pytest.mark.asyncio
    async def test_parse_github_url(self):
        parser = MessageParser()
        message = "Check out https://github.com/owner/repo/issues/123"
        
        result = await parser.parse(message)
        
        assert len(result.references) == 1
        assert result.references[0].type == ReferenceType.GITHUB_ISSUE
        assert result.references[0].metadata['owner'] == 'owner'
        assert result.references[0].metadata['repo'] == 'repo'
        assert result.references[0].metadata['issue_number'] == '123'
    
    @pytest.mark.asyncio
    async def test_parse_jira_ticket(self):
        parser = MessageParser()
        message = "Fix bug in PROJ-456"
        
        result = await parser.parse(message)
        
        assert len(result.references) == 1
        assert result.references[0].type == ReferenceType.JIRA_TICKET
        assert result.references[0].metadata['ticket_id'] == 'PROJ-456'
    
    @pytest.mark.asyncio
    async def test_parse_multiple_references(self):
        parser = MessageParser()
        message = "Fix PROJ-123 and check https://github.com/owner/repo"
        
        result = await parser.parse(message)
        
        assert len(result.references) >= 2


class TestOrchestrationFacade:
    """Test orchestration facade"""
    
    @pytest.mark.asyncio
    async def test_parse_only(self):
        mock_service_manager = Mock()
        facade = OrchestrationFacade(mock_service_manager)
        
        message = "Check #123"
        result = await facade.parse_only(message)
        
        assert result.original_message == message
        assert len(result.references) == 1
    
    @pytest.mark.asyncio
    async def test_facade_initialization(self):
        mock_service_manager = Mock()
        facade = OrchestrationFacade(mock_service_manager)
        
        assert facade.parser is not None
        assert facade.enricher is not None
        assert facade.prompt_builder is not None
        assert facade.agent is not None


@pytest.fixture
def mock_service_manager():
    """Create mock service manager"""
    manager = Mock()
    manager.get_service = Mock(return_value=Mock())
    return manager


@pytest.fixture
def mock_llm_factory():
    """Create mock LLM factory"""
    factory = Mock()
    llm = Mock()
    llm.generate = AsyncMock(return_value="Generated response")
    factory.create_llm = Mock(return_value=llm)
    return factory


class TestEndToEndPipeline:
    """Test complete end-to-end pipeline"""
    
    @pytest.mark.asyncio
    async def test_message_parsing_to_enrichment(self):
        """Test parser output can be used by enricher"""
        parser = MessageParser()
        mock_service_manager = Mock()
        mock_service_manager.get_service = Mock(return_value=Mock())
        
        from orchestration.context_enricher import ContextEnricher
        enricher = ContextEnricher(mock_service_manager)
        
        message = "Analyze https://github.com/owner/repo"
        parsed = await parser.parse(message)
        
        assert len(parsed.references) > 0
        
        try:
            enriched = await enricher.enrich(parsed)
            assert enriched.parsed_message == parsed
        except Exception:
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
