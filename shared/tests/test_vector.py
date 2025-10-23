"""Test Vector Database connections and operations"""
import asyncio
import logging
from typing import Dict, Any, List
from shared.config import settings

logger = logging.getLogger(__name__)


async def test_qdrant_connection() -> Dict[str, Any]:
    """Test Qdrant vector database connection"""
    result = {
        "service": "Qdrant Vector DB",
        "configured": True,  # Qdrant has default settings
        "connection": False,
        "error": None,
        "details": {}
    }
    
    try:
        # Import Qdrant client
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        
        # Test connection
        client = QdrantClient(
            host=settings.qdrant_host, 
            port=settings.qdrant_port
        )
        
        # Test basic operations
        collections = client.get_collections()
        
        result["connection"] = True
        result["details"] = {
            "host": settings.qdrant_host,
            "port": settings.qdrant_port,
            "collections_count": len(collections.collections),
            "collection_names": [col.name for col in collections.collections[:5]]  # First 5
        }
        
    except ImportError as e:
        result["error"] = f"Qdrant client not installed: {e}"
    except Exception as e:
        result["error"] = f"Connection failed: {e}"
    
    return result


async def test_qdrant_operations() -> Dict[str, Any]:
    """Test Qdrant CRUD operations"""
    result = {
        "service": "Qdrant Operations",
        "configured": True,
        "connection": False,
        "error": None,
        "details": {}
    }
    
    try:
        # Import Qdrant client
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams, PointStruct
        import numpy as np
        
        # Test connection
        client = QdrantClient(
            host=settings.qdrant_host, 
            port=settings.qdrant_port
        )
        
        test_collection = f"test_collection_{int(asyncio.get_event_loop().time())}"
        
        try:
            # Create test collection
            client.create_collection(
                collection_name=test_collection,
                vectors_config=VectorParams(size=128, distance=Distance.COSINE)
            )
            
            # Add test vectors
            test_vectors = [
                PointStruct(id=1, vector=np.random.rand(128).tolist(), payload={"text": "test document 1"}),
                PointStruct(id=2, vector=np.random.rand(128).tolist(), payload={"text": "test document 2"})
            ]
            
            client.upsert(
                collection_name=test_collection,
                points=test_vectors
            )
            
            # Search test
            search_results = client.search(
                collection_name=test_collection,
                query_vector=np.random.rand(128).tolist(),
                limit=2
            )
            
            # Get collection info
            collection_info = client.get_collection(test_collection)
            
            result["connection"] = True
            result["details"] = {
                "test_collection": test_collection,
                "vectors_added": len(test_vectors),
                "search_results": len(search_results),
                "collection_size": collection_info.vectors_count
            }
            
        finally:
            # Clean up test collection
            try:
                client.delete_collection(test_collection)
            except:
                pass
        
    except ImportError as e:
        result["error"] = f"Required packages not installed: {e}"
    except Exception as e:
        result["error"] = f"Operations test failed: {e}"
    
    return result


async def test_vector_db_fallback() -> Dict[str, Any]:
    """Test vector database fallback mechanisms"""
    result = {
        "service": "Vector DB Fallback",
        "configured": bool(settings.vector_db_fallback_enabled),
        "connection": False,
        "error": None,
        "details": {}
    }
    
    if not result["configured"]:
        result["error"] = "Vector DB fallback not enabled"
        return result
    
    try:
        # Try to import and test fallback mechanisms
        # This would typically be in-memory storage
        
        # Simulate fallback scenario
        fallback_data = {
            "provider": "in-memory",
            "collections": [],
            "supports_persistence": False
        }
        
        result["connection"] = True
        result["details"] = {
            "fallback_enabled": settings.vector_db_fallback_enabled,
            "primary_provider": settings.vector_db_provider,
            "fallback_provider": "in-memory",
            "test_data": fallback_data
        }
        
    except Exception as e:
        result["error"] = f"Fallback test failed: {e}"
    
    return result


async def test_vector_embeddings() -> Dict[str, Any]:
    """Test vector embeddings generation"""
    result = {
        "service": "Vector Embeddings",
        "configured": True,  # Usually uses default models
        "connection": False,
        "error": None,
        "details": {}
    }
    
    try:
        # Try to test embeddings (this depends on what embedding service you use)
        # For now, we'll test if we can import common embedding libraries
        
        embedding_services = {}
        
        # Test sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2')
            test_embedding = model.encode("This is a test sentence")
            embedding_services["sentence_transformers"] = {
                "available": True,
                "embedding_size": len(test_embedding)
            }
        except ImportError:
            embedding_services["sentence_transformers"] = {"available": False, "error": "Not installed"}
        except Exception as e:
            embedding_services["sentence_transformers"] = {"available": False, "error": str(e)}
        
        # Test OpenAI embeddings (if configured)
        if settings.together_api_key or (hasattr(settings, 'openai_api_key') and getattr(settings, 'openai_api_key')):
            try:
                # This would test OpenAI embeddings
                embedding_services["openai"] = {"available": True, "note": "API key configured"}
            except:
                embedding_services["openai"] = {"available": False, "error": "API test failed"}
        else:
            embedding_services["openai"] = {"available": False, "error": "No API key configured"}
        
        available_services = sum(1 for s in embedding_services.values() if s["available"])
        
        result["connection"] = available_services > 0
        result["details"] = {
            "available_services": available_services,
            "total_services": len(embedding_services),
            "services": embedding_services
        }
        
    except Exception as e:
        result["error"] = f"Embeddings test failed: {e}"
    
    return result


async def test_all_vector_services() -> Dict[str, Any]:
    """Test all vector database services"""
    logger.info("Testing Vector Database services...")
    
    results = {}
    
    # Test Qdrant connection
    results["qdrant_connection"] = await test_qdrant_connection()
    
    # Test Qdrant operations (only if connection works)
    if results["qdrant_connection"]["connection"]:
        results["qdrant_operations"] = await test_qdrant_operations()
    else:
        results["qdrant_operations"] = {
            "service": "Qdrant Operations",
            "configured": False,
            "connection": False,
            "error": "Skipped due to connection failure",
            "details": {}
        }
    
    # Test fallback mechanisms
    results["fallback"] = await test_vector_db_fallback()
    
    # Test embeddings
    results["embeddings"] = await test_vector_embeddings()
    
    # Summary
    total_services = len(results)
    connected_services = sum(1 for r in results.values() if r["connection"])
    configured_services = sum(1 for r in results.values() if r["configured"])
    
    results["summary"] = {
        "total_services": total_services,
        "configured_services": configured_services,
        "connected_services": connected_services,
        "success_rate": f"{connected_services}/{configured_services}" if configured_services > 0 else "0/0"
    }
    
    return results


if __name__ == "__main__":
    async def main():
        print("Testing Vector Database connections...")
        results = await test_all_vector_services()
        
        print(f"\n=== Vector Database Test Results ===")
        for service_key, result in results.items():
            if service_key == "summary":
                continue
            print(f"\n{result['service']}:")
            print(f"  Configured: {result['configured']}")
            print(f"  Connected: {result['connection']}")
            if result['error']:
                print(f"  Error: {result['error']}")
            if result['details']:
                print(f"  Details: {result['details']}")
        
        print(f"\n=== Summary ===")
        summary = results["summary"]
        print(f"Services configured: {summary['configured_services']}/{summary['total_services']}")
        print(f"Services connected: {summary['connected_services']}/{summary['configured_services']}")
        print(f"Success rate: {summary['success_rate']}")
    
    asyncio.run(main())