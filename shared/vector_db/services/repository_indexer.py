"""
Repository Indexing Service
Indexes GitHub repository content into vector database
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib

from ..base import VectorDBProvider, DocumentMetadata
from ..embedding_service import EmbeddingService
from shared.clients.wrappers.github_wrapper import GitHubWrapper

logger = logging.getLogger(__name__)


class RepositoryIndexer:
    """Service for indexing GitHub repositories into vector database"""
    
    def __init__(
        self,
        vector_db: VectorDBProvider,
        embedding_service: EmbeddingService,
        github_client: Optional[GitHubWrapper] = None
    ):
        """
        Initialize repository indexer
        
        Args:
            vector_db: Vector database provider
            embedding_service: Embedding generation service
            github_client: GitHub API client
        """
        self.vector_db = vector_db
        self.embedding_service = embedding_service
        self.github_client = github_client
        logger.info("📚 Repository Indexer initialized")
    
    async def index_repository(
        self,
        owner: str,
        repo: str,
        branch: str = "main",
        collection_name: str = "github_repos"
    ) -> Dict[str, Any]:
        """
        Index entire repository into vector database
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: Branch to index
            collection_name: Vector DB collection name
            
        Returns:
            Indexing results with statistics
        """
        logger.info(f"🔍 Starting to index repository: {owner}/{repo}")
        logger.info(f"   📋 Repository: {owner}/{repo}")
        logger.info(f"   🌿 Branch: {branch}")
        logger.info(f"   📦 Collection: {collection_name}")
        
        if not self.github_client:
            logger.error("❌ GitHub client not configured")
            return {'success': False, 'error': 'GitHub client not configured'}
        
        try:
            # Get repository tree
            logger.info(f"📂 Fetching repository tree from GitHub...")
            tree = await self._get_repository_tree(owner, repo, branch)
            
            if not tree:
                logger.error("❌ Failed to fetch repository tree")
                return {'success': False, 'error': 'Failed to fetch repository tree'}
            
            logger.info(f"✅ Retrieved {len(tree)} items from repository")
            
            # Filter files to index (code, docs, markdown)
            logger.info(f"🔍 Filtering indexable files...")
            files_to_index = self._filter_indexable_files(tree)
            
            logger.info(f"📝 Found {len(files_to_index)} files to index out of {len(tree)} total files")
            if len(files_to_index) > 0:
                logger.info(f"   📄 File types: {', '.join(set(f.get('path', '').split('.')[-1] for f in files_to_index if '.' in f.get('path', '')))}")
            
            # Fetch file contents and create documents
            logger.info(f"📥 Processing {len(files_to_index)} files and fetching content...")
            documents = []
            metadatas = []
            processed_count = 0
            skipped_count = 0
            
            for i, file_info in enumerate(files_to_index):
                if (i + 1) % 10 == 0 or i == 0:
                    logger.info(f"   📊 Processing file {i + 1}/{len(files_to_index)}: {file_info.get('path', 'unknown')}")
                
                doc, metadata = await self._process_file(
                    owner, repo, file_info, branch
                )
                if doc and metadata:
                    documents.append(doc)
                    metadatas.append(metadata)
                    processed_count += 1
                else:
                    skipped_count += 1
            
            logger.info(f"✅ Content processing complete: {processed_count} processed, {skipped_count} skipped")
            
            if not documents:
                return {'success': False, 'error': 'No documents to index'}
            
            # Generate embeddings
            logger.info(f"🎯 Generating embeddings for {len(documents)} documents...")
            logger.info(f"   🤖 Using embedding service: {self.embedding_service.provider_name}")
            logger.info(f"   📐 Model: {self.embedding_service.embedding_model}")
            logger.info(f"   📏 Dimensions: {self.embedding_service.get_dimension()}")
            
            start_time = datetime.now()
            embeddings = await self.embedding_service.generate_embeddings_batch(documents)
            end_time = datetime.now()
            
            duration = (end_time - start_time).total_seconds()
            logger.info(f"✅ Embedding generation completed in {duration:.2f} seconds")
            logger.info(f"   ⚡ Average: {duration/len(documents):.3f}s per document")
            
            # Add to vector database
            logger.info(f"💾 Adding documents to vector database...")
            logger.info(f"   📊 Collection: {collection_name}")
            logger.info(f"   📄 Documents: {len(documents)}")
            logger.info(f"   🎯 Embeddings: {len(embeddings)}")
            
            start_time = datetime.now()
            success = await self.vector_db.add_documents(
                collection=collection_name,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )
            end_time = datetime.now()
            
            db_duration = (end_time - start_time).total_seconds()
            logger.info(f"✅ Vector DB storage completed in {db_duration:.2f} seconds")
            
            if success:
                logger.info(f"✅ Successfully indexed {len(documents)} documents from {owner}/{repo}")
                return {
                    'success': True,
                    'repository': f"{owner}/{repo}",
                    'branch': branch,
                    'documents_indexed': len(documents),
                    'collection': collection_name
                }
            else:
                return {'success': False, 'error': 'Failed to add documents to vector DB'}
                
        except Exception as e:
            logger.error(f"❌ Failed to index repository: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_repository_tree(
        self,
        owner: str,
        repo: str,
        branch: str
    ) -> Optional[List[Dict[str, Any]]]:
        """Get repository file tree"""
        try:
            if not self.github_client:
                logger.error("❌ GitHub client not configured")
                return None
            
            # Get repository tree using GitHub API
            repo_name = f"{owner}/{repo}"
            tree = await self.github_client.get_repository_tree(
                repo_name=repo_name,
                branch=branch,
                recursive=True
            )
            
            if tree:
                logger.info(f"📂 Successfully retrieved {len(tree)} items from {repo_name}")
            else:
                logger.warning(f"⚠️  No tree returned for {repo_name}")
            
            return tree
            
        except Exception as e:
            logger.error(f"❌ Failed to get repository tree: {e}", exc_info=True)
            return None
    
    def _filter_indexable_files(self, tree: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter files that should be indexed"""
        indexable_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs',
            '.c', '.cpp', '.h', '.hpp', '.cs', '.rb', '.php', '.swift',
            '.md', '.rst', '.txt', '.yaml', '.yml', '.json', '.toml'
        }
        
        filtered = []
        for item in tree:
            if item.get('type') == 'blob':  # It's a file
                path = item.get('path', '')
                extension = '.' + path.split('.')[-1] if '.' in path else ''
                
                if extension.lower() in indexable_extensions:
                    filtered.append(item)
        
        return filtered
    
    async def _process_file(
        self,
        owner: str,
        repo: str,
        file_info: Dict[str, Any],
        branch: str
    ) -> tuple[Optional[str], Optional[DocumentMetadata]]:
        """Process a single file for indexing"""
        try:
            file_path = file_info.get('path', '')
            repo_name = f"{owner}/{repo}"
            
            # Fetch actual file content from GitHub
            if not self.github_client:
                logger.error("❌ GitHub client not configured")
                return None, None
            
            content = await self.github_client.get_file_content(
                repo_name=repo_name,
                file_path=file_path,
                branch=branch
            )
            
            if not content:
                logger.warning(f"⚠️  Could not fetch content for {file_path}")
                return None, None
            
            # Skip very large files (>500KB)
            if len(content) > 500_000:
                logger.warning(f"⏭️  Skipping large file {file_path} ({len(content):,} bytes > 500KB limit)")
                return None, None
            
            # Skip empty files
            if len(content.strip()) == 0:
                logger.debug(f"⏭️  Skipping empty file {file_path}")
                return None, None
            
            # Create unique document ID
            doc_id = hashlib.sha256(
                f"{owner}/{repo}/{branch}/{file_path}".encode()
            ).hexdigest()[:16]
            
            # Determine language from extension
            language = self._detect_language(file_path)
            
            # Create metadata
            metadata = DocumentMetadata(
                doc_id=doc_id,
                source='github',
                repo_name=repo_name,
                file_path=file_path,
                commit_sha=file_info.get('sha'),
                content_type='code' if language else 'text',
                language=language,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            logger.debug(f"✅ Processed {file_path} ({len(content)} bytes)")
            return content, metadata
            
        except Exception as e:
            logger.error(f"❌ Failed to process file {file_info.get('path')}: {e}")
            return None, None
    
    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect programming language from file extension"""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cs': 'csharp',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift'
        }
        
        extension = '.' + file_path.split('.')[-1] if '.' in file_path else ''
        return extension_map.get(extension.lower())
