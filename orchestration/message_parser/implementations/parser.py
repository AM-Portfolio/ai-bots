"""
Message Parser Implementation

Extracts references (URLs, tickets, issue IDs) from user messages
"""
import re
from typing import List, Dict, Any
from urllib.parse import urlparse
from orchestration.shared.interfaces import IMessageParser
from orchestration.shared.models import ParsedMessage, Reference, ReferenceType


class MessageParser(IMessageParser):
    """Extracts structured references from raw user messages"""
    
    def __init__(self):
        self.patterns = {
            ReferenceType.GITHUB_URL: re.compile(
                r'https?://github\.com/([^/]+)/([^/]+)(?:/issues/(\d+)|/pull/(\d+)|/blob/([^/]+)/(.+)|/?)?'
            ),
            ReferenceType.GITHUB_ISSUE: re.compile(
                r'(?:^|\s)#(\d+)(?:\s|$)'
            ),
            ReferenceType.JIRA_URL: re.compile(
                r'https?://[^/]+\.atlassian\.net/browse/([A-Z]+-\d+)'
            ),
            ReferenceType.JIRA_TICKET: re.compile(
                r'(?:^|\s)([A-Z]+-\d+)(?:\s|$|[,.])'
            ),
            ReferenceType.CONFLUENCE_URL: re.compile(
                r'https?://[^/]+\.atlassian\.net/wiki/spaces/([^/]+)/pages/(\d+)/([^?#\s]*)'
            ),
            ReferenceType.GENERIC_URL: re.compile(
                r'https?://[^\s<>"]+'
            )
        }
    
    async def parse(self, message: str) -> ParsedMessage:
        """
        Parse message to extract all references
        
        Args:
            message: Raw user message
            
        Returns:
            ParsedMessage with extracted references
        """
        references: List[Reference] = []
        clean_message = message
        
        references.extend(self._extract_github_urls(message))
        references.extend(self._extract_github_issues(message))
        references.extend(self._extract_jira_urls(message))
        references.extend(self._extract_jira_tickets(message))
        references.extend(self._extract_confluence_urls(message))
        
        for ref in references:
            clean_message = clean_message.replace(ref.raw_text, f"[{ref.type.value}]")
        
        return ParsedMessage(
            original_message=message,
            references=references,
            clean_message=clean_message.strip(),
            metadata={'total_references': len(references)}
        )
    
    def _extract_github_urls(self, message: str) -> List[Reference]:
        """Extract GitHub URLs"""
        references = []
        for match in self.patterns[ReferenceType.GITHUB_URL].finditer(message):
            owner, repo, issue_num, pr_num, branch, file_path = match.groups()
            
            metadata: Dict[str, Any] = {
                'owner': owner,
                'repo': repo
            }
            
            if issue_num:
                metadata['issue_number'] = issue_num
                ref_type = ReferenceType.GITHUB_ISSUE
            elif pr_num:
                metadata['pr_number'] = pr_num
                ref_type = ReferenceType.GITHUB_PR
            else:
                ref_type = ReferenceType.GITHUB_URL
            
            if branch and file_path:
                metadata['branch'] = branch
                metadata['file_path'] = file_path
            
            references.append(Reference(
                type=ref_type,
                raw_text=match.group(0),
                normalized_value=f"{owner}/{repo}",
                metadata=metadata,
                confidence=1.0
            ))
        
        return references
    
    def _extract_github_issues(self, message: str) -> List[Reference]:
        """Extract GitHub issue references like #123"""
        references = []
        for match in self.patterns[ReferenceType.GITHUB_ISSUE].finditer(message):
            issue_num = match.group(1)
            references.append(Reference(
                type=ReferenceType.GITHUB_ISSUE,
                raw_text=match.group(0).strip(),
                normalized_value=f"#{issue_num}",
                metadata={'issue_number': issue_num},
                confidence=0.8
            ))
        return references
    
    def _extract_jira_urls(self, message: str) -> List[Reference]:
        """Extract Jira URLs"""
        references = []
        for match in self.patterns[ReferenceType.JIRA_URL].finditer(message):
            ticket_id = match.group(1)
            references.append(Reference(
                type=ReferenceType.JIRA_URL,
                raw_text=match.group(0),
                normalized_value=ticket_id,
                metadata={'ticket_id': ticket_id},
                confidence=1.0
            ))
        return references
    
    def _extract_jira_tickets(self, message: str) -> List[Reference]:
        """Extract Jira ticket IDs like PROJ-123"""
        references = []
        for match in self.patterns[ReferenceType.JIRA_TICKET].finditer(message):
            ticket_id = match.group(1)
            if not any(ref.normalized_value == ticket_id for ref in references):
                references.append(Reference(
                    type=ReferenceType.JIRA_TICKET,
                    raw_text=match.group(0).strip(),
                    normalized_value=ticket_id,
                    metadata={'ticket_id': ticket_id},
                    confidence=0.9
                ))
        return references
    
    def _extract_confluence_urls(self, message: str) -> List[Reference]:
        """Extract Confluence URLs"""
        references = []
        for match in self.patterns[ReferenceType.CONFLUENCE_URL].finditer(message):
            space_key, page_id, page_title = match.groups()
            references.append(Reference(
                type=ReferenceType.CONFLUENCE_URL,
                raw_text=match.group(0),
                normalized_value=page_id,
                metadata={
                    'space_key': space_key,
                    'page_id': page_id,
                    'page_title': page_title.replace('-', ' ')
                },
                confidence=1.0
            ))
        return references
