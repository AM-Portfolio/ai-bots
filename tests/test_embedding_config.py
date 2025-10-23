#!/usr/bin/env python3
"""
Test script to show current embedding configuration
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.llm import llm_client
from shared.vector_db.embedding_service import EmbeddingService

async def test_embedding_config():
    """Test current embedding configuration"""
    
    print("🧠 EMBEDDING CONFIGURATION TEST\n" + "="*50)
    
    # Test unified LLM client
    print("1️⃣ **Unified LLM Client Embeddings**")
    provider_info = llm_client.get_provider_info()
    print(f"   • Provider: {provider_info.get('provider', 'Unknown')}")
    print(f"   • Enhanced Features: {provider_info.get('enhanced_features', False)}")
    
    if hasattr(llm_client.provider, 'embeddings_model'):
        print(f"   • Embeddings Model: {llm_client.provider.embeddings_model}")
    
    # Test embeddings generation
    try:
        test_text = "This is a test for embedding generation"
        embeddings = await llm_client.generate_embeddings([test_text])
        
        if embeddings and len(embeddings) > 0:
            print(f"   • ✅ Embeddings Generated: {len(embeddings[0])} dimensions")
            print(f"   • Sample values: {embeddings[0][:5]}...")
        else:
            print("   • ❌ No embeddings generated")
            
    except Exception as e:
        print(f"   • ❌ Error: {e}")
    
    print("\n2️⃣ **Vector DB Embedding Service**")
    
    # Test embedding service
    embedding_service = EmbeddingService()
    
    try:
        embedding = await embedding_service.generate_embedding(test_text)
        print(f"   • ✅ Embedding Generated: {len(embedding)} dimensions")
        print(f"   • Sample values: {embedding[:5]}...")
        
        # Check if it's using hash fallback (all values would be similar pattern)
        if len(set(str(x)[:6] for x in embedding[:10])) == 1:
            print("   • ⚠️  Using hash-based fallback (not LLM embeddings)")
        else:
            print("   • ✅ Using LLM-generated embeddings")
            
    except Exception as e:
        print(f"   • ❌ Error: {e}")
    
    print("\n3️⃣ **Configuration Summary**")
    print(f"   • Default Provider: {os.getenv('LLM_PROVIDER', 'azure')}")
    print(f"   • Azure Embeddings Model: {os.getenv('AZURE_OPENAI_EMBEDDINGS_MODEL', 'text-embedding-ada-002')}")
    print(f"   • Together API Available: {'✅' if os.getenv('TOGETHER_API_KEY') else '❌'}")
    print(f"   • Azure API Available: {'✅' if os.getenv('AZURE_OPENAI_API_KEY') else '❌'}")

if __name__ == "__main__":
    asyncio.run(test_embedding_config())