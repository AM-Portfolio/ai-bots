"""
Intent Classifier for Voice Assistant

Uses LLM to understand user intent and route to appropriate orchestration.
"""

import logging
from typing import Dict, Optional, Any
from pydantic import BaseModel

from shared.llm_providers.resilient_orchestrator import ResilientLLMOrchestrator

logger = logging.getLogger(__name__)


class Intent(BaseModel):
    """Classified user intent"""
    type: str  # 'commit', 'github_query', 'general', 'help'
    confidence: float
    entities: Dict[str, Any] = {}  # Extracted entities (repo, branch, etc.)
    orchestration: str  # Which orchestration to use


class IntentClassifier:
    """
    Classifies user voice input to determine appropriate orchestration
    
    Intent Types:
    - commit: User wants to commit code ("commit my changes to repo X")
    - github_query: User asks about code/repo ("what's in the auth service?")
    - general: General question or conversation
    - help: User needs assistance
    """
    
    def __init__(self, llm_orchestrator: ResilientLLMOrchestrator):
        self.llm = llm_orchestrator
        logger.info("✅ IntentClassifier initialized")
    
    async def classify(self, user_input: str, conversation_history: list = None) -> Intent:
        """
        Classify user intent from speech transcript
        
        Args:
            user_input: Transcribed speech from user
            conversation_history: Previous conversation for context
            
        Returns:
            Intent object with type, confidence, and extracted entities
        """
        logger.info(f"🔍 Classifying intent for: '{user_input[:100]}...'")
        
        # Build prompt for intent classification
        prompt = self._build_classification_prompt(user_input, conversation_history)
        
        try:
            # Use chat completion instead of generate
            result, metadata = await self.llm.chat_completion_with_fallback(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Low temperature for consistent classification
                max_retries=1
            )
            
            # Parse LLM response
            intent = self._parse_intent_response(result if result else "", user_input)
            
            logger.info(f"✅ Classified as '{intent.type}' (confidence: {intent.confidence:.2f})")
            return intent
            
        except Exception as e:
            logger.error(f"❌ Intent classification failed: {e}")
            # Fallback to general intent
            return Intent(
                type="general",
                confidence=0.5,
                orchestration="general_llm"
            )
    
    def _build_classification_prompt(self, user_input: str, history: list = None) -> str:
        """Build LLM prompt for intent classification"""
        prompt = """You are an intent classifier for a voice-controlled AI development assistant.

Analyze the user's speech and classify their intent into ONE of these categories:

1. **commit** - User wants to commit code to GitHub
   Examples: "commit my changes", "commit to repository X", "push my code"
   
2. **github_query** - User asks about code, repositories, or documentation
   Examples: "what's in the auth service?", "show me the API endpoints", "explain this repo"
   
3. **general** - General questions, chitchat, or other topics
   Examples: "how are you?", "what's the weather?", "tell me a joke"
   
4. **help** - User needs assistance or doesn't know what to do
   Examples: "help", "what can you do?", "I don't know what to say"

Also extract relevant entities:
- repository: Repository name if mentioned
- branch: Branch name if mentioned
- action: Specific action requested

Respond in this exact format:
INTENT: <type>
CONFIDENCE: <0.0-1.0>
REPOSITORY: <name or "none">
BRANCH: <name or "none">
ACTION: <specific action or "none">

"""
        
        if history:
            prompt += "\nRecent conversation:\n"
            for turn in history[-3:]:  # Last 3 turns
                prompt += f"{turn['role']}: {turn['content']}\n"
        
        prompt += f"\nUser: {user_input}\n\nClassify this intent:"
        return prompt
    
    def _parse_intent_response(self, llm_response: str, original_input: str) -> Intent:
        """Parse LLM classification response"""
        lines = llm_response.strip().split("\n")
        
        intent_type = "general"
        confidence = 0.7
        entities = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith("INTENT:"):
                intent_type = line.split(":", 1)[1].strip().lower()
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                except ValueError:
                    confidence = 0.7
            elif line.startswith("REPOSITORY:"):
                repo = line.split(":", 1)[1].strip()
                if repo.lower() != "none":
                    entities["repository"] = repo
            elif line.startswith("BRANCH:"):
                branch = line.split(":", 1)[1].strip()
                if branch.lower() != "none":
                    entities["branch"] = branch
            elif line.startswith("ACTION:"):
                action = line.split(":", 1)[1].strip()
                if action.lower() != "none":
                    entities["action"] = action
        
        # Map intent to orchestration
        orchestration_map = {
            "commit": "commit_workflow",
            "github_query": "github_llm",
            "general": "general_llm",
            "help": "general_llm"
        }
        
        orchestration = orchestration_map.get(intent_type, "general_llm")
        
        return Intent(
            type=intent_type,
            confidence=confidence,
            entities=entities,
            orchestration=orchestration
        )
