"""MongoDB service implementation using base architecture"""

from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient

from shared.services.base import BaseService, ServiceConfig, ServiceStatus
from shared.logger import get_logger

logger = get_logger(__name__)


class MongoDBService(BaseService):
    """MongoDB integration with LLM wrapper support"""
    
    async def connect(self) -> bool:
        """Connect to MongoDB"""
        try:
            connection_string = self.config.config.get('connection_string')
            database_name = self.config.config.get('database_name', 'default_db')
            
            if not connection_string:
                self._set_error("MongoDB connection string not provided")
                return False
            
            self._client = AsyncIOMotorClient(connection_string)
            self._db = self._client[database_name]
            
            # Test connection
            await self._client.server_info()
            logger.info(f"Connected to MongoDB database: {database_name}")
            
            self._set_connected()
            return True
            
        except Exception as e:
            self._set_error(str(e))
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from MongoDB"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
        self.status = ServiceStatus.DISCONNECTED
        return True
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test MongoDB connection"""
        try:
            if not self._client:
                return {"success": False, "error": "Not connected"}
            
            info = await self._client.server_info()
            collections = await self._db.list_collection_names()
            
            return {
                "success": True,
                "version": info.get('version'),
                "collections_count": len(collections)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute MongoDB actions"""
        actions = {
            "insert": self._insert,
            "find": self._find,
            "update": self._update,
            "delete": self._delete,
            "aggregate": self._aggregate,
            "list_collections": self._list_collections
        }
        
        handler = actions.get(action)
        if not handler:
            return {"success": False, "error": f"Unknown action: {action}"}
        
        return await handler(**kwargs)
    
    async def get_capabilities(self) -> List[str]:
        """Get MongoDB service capabilities"""
        return [
            "Document Operations",
            "Aggregation",
            "Indexing",
            "Collections Management",
            "Transactions"
        ]
    
    # Action handlers
    async def _insert(
        self,
        collection: str,
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Insert a document"""
        try:
            result = await self._db[collection].insert_one(document)
            return {
                "success": True,
                "inserted_id": str(result.inserted_id)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _find(
        self,
        collection: str,
        query: Dict[str, Any],
        limit: int = 10
    ) -> Dict[str, Any]:
        """Find documents"""
        try:
            cursor = self._db[collection].find(query).limit(limit)
            documents = await cursor.to_list(length=limit)
            
            # Convert ObjectId to string
            for doc in documents:
                if '_id' in doc:
                    doc['_id'] = str(doc['_id'])
            
            return {
                "success": True,
                "documents": documents,
                "count": len(documents)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _update(
        self,
        collection: str,
        query: Dict[str, Any],
        update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update documents"""
        try:
            result = await self._db[collection].update_many(query, {"$set": update})
            return {
                "success": True,
                "matched": result.matched_count,
                "modified": result.modified_count
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _delete(
        self,
        collection: str,
        query: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Delete documents"""
        try:
            result = await self._db[collection].delete_many(query)
            return {
                "success": True,
                "deleted": result.deleted_count
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _aggregate(
        self,
        collection: str,
        pipeline: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run aggregation pipeline"""
        try:
            cursor = self._db[collection].aggregate(pipeline)
            results = await cursor.to_list(length=100)
            
            return {
                "success": True,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _list_collections(self) -> Dict[str, Any]:
        """List all collections"""
        try:
            collections = await self._db.list_collection_names()
            return {
                "success": True,
                "collections": collections,
                "count": len(collections)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
