from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes
import logging

from features.context_resolver import resolve_context
from features.context_resolver.dto import ContextResolverInput
from features.issue_analyzer import analyze_issue
from shared.models import SourceType, EnrichedContext

logger = logging.getLogger(__name__)


class AIDevBot(ActivityHandler):
    async def on_message_activity(self, turn_context: TurnContext):
        text = turn_context.activity.text.strip().lower()
        
        logger.info(f"Received message: {text}")
        
        if text.startswith("analyze"):
            parts = text.split()
            if len(parts) >= 3:
                source = parts[1]
                issue_id = parts[2]
                
                await turn_context.send_activity(
                    MessageFactory.text(f"Analyzing {source} issue {issue_id}...")
                )
                
                try:
                    context_input = ContextResolverInput(
                        issue_id=issue_id,
                        source=SourceType(source),
                        repository=""
                    )
                    
                    context_result = await resolve_context(context_input)
                    
                    if context_result.success:
                        enriched_context = EnrichedContext(**context_result.enriched_data)
                        analysis = await analyze_issue(enriched_context)
                        
                        response = f"""
**Analysis Complete**

**Issue:** {analysis.issue_id}
**Root Cause:** {analysis.root_cause}
**Confidence:** {analysis.confidence_score * 100:.1f}%
**Fixes:** {len(analysis.suggested_fixes)}
"""
                        await turn_context.send_activity(MessageFactory.text(response))
                    else:
                        await turn_context.send_activity(
                            MessageFactory.text(f"Failed: {context_result.error_message}")
                        )
                
                except Exception as e:
                    logger.error(f"Analysis error: {e}")
                    await turn_context.send_activity(
                        MessageFactory.text(f"Error: {str(e)}")
                    )
            else:
                await turn_context.send_activity(
                    MessageFactory.text("Usage: analyze <source> <issue_id>")
                )
        
        elif text == "help":
            help_text = """
**AI Dev Agent Commands:**

- `analyze <source> <issue_id>` - Analyze an issue
  Example: analyze github 123
  
- `status` - Check bot status

- `help` - Show this help message
"""
            await turn_context.send_activity(MessageFactory.text(help_text))
        
        elif text == "status":
            await turn_context.send_activity(
                MessageFactory.text("AI Dev Agent is running and ready!")
            )
        
        else:
            await turn_context.send_activity(
                MessageFactory.text("Unknown command. Type 'help' for available commands.")
            )
    
    async def on_members_added_activity(
        self,
        members_added: ChannelAccount,
        turn_context: TurnContext
    ):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    MessageFactory.text(
                        "Hello! I'm the AI Dev Agent. Type 'help' to see what I can do."
                    )
                )


bot_handler = AIDevBot()
