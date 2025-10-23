#!/usr/bin/env python3
"""
Test script for the new embedding service with Together AI and fallback
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from shared.vector_db.embedding_service import EmbeddingService


async def test_embedding_service():
    """Test the embedding service with various scenarios"""
    
    print("🧪 Testing Embedding Service with Together AI + Fallback")
    print("=" * 60)
    
    # Initialize service
    service = EmbeddingService(provider="together")
    
    # Test 1: Health check
    print("\n1️⃣ Testing Health Check...")
    health = await service.health_check()
    print(f"Health Status: {health}")
    
    # Test 2: Model info
    print("\n2️⃣ Getting Model Info...")
    model_info = service.get_model_info()
    print(f"Model Info: {model_info}")
    
    # Test 3: Single embedding
    print("\n3️⃣ Testing Single Embedding...")
    test_texts = [
        "This is a test of semantic similarity for AI development",
        "Machine learning and artificial intelligence coding patterns",
        "How to fix bugs in Python applications",
        "Error handling and exception management in software"
    ]
    
    for i, text in enumerate(test_texts):
        print(f"\nTest {i+1}: '{text}'")
        embedding = await service.generate_embedding(text)
        print(f"  Dimension: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
        print(f"  Last 5 values: {embedding[-5:]}")
        print(f"  Stats: min={min(embedding):.4f}, max={max(embedding):.4f}, mean={sum(embedding)/len(embedding):.4f}")
    
    # Test 4: Batch embeddings
    print("\n4️⃣ Testing Batch Embeddings...")
    batch_embeddings = await service.generate_embeddings_batch(test_texts)
    print(f"Batch Results: {len(batch_embeddings)} embeddings generated")
    
    # Test 5: Similarity test
    print("\n5️⃣ Testing Semantic Similarity...")
    similar_texts = [
        "AI development patterns",  # Should be similar to first text
        "artificial intelligence development patterns"  # Should also be similar
    ]
    
    for similar_text in similar_texts:
        similar_embedding = await service.generate_embedding(similar_text)
        
        # Simple cosine similarity with first test text
        original_embedding = batch_embeddings[0]
        
        dot_product = sum(a * b for a, b in zip(original_embedding, similar_embedding))
        magnitude_a = sum(a * a for a in original_embedding) ** 0.5
        magnitude_b = sum(b * b for b in similar_embedding) ** 0.5
        
        cosine_similarity = dot_product / (magnitude_a * magnitude_b) if magnitude_a * magnitude_b != 0 else 0
        
        print(f"  '{similar_text}'")
        print(f"    Similarity to '{test_texts[0]}': {cosine_similarity:.4f}")
    
    print("\n✅ Embedding service test completed!")
    
    # Test 6: Check if Together AI is working vs fallback  
    print("\n6️⃣ Testing Method Detection...")
    if service.api_available:
        print("  🌐 Together AI API is available")
        
        # Test with API disabled to force fallback
        original_client = service.client
        service.client = None
        service.api_available = False
        
        fallback_embedding = await service.generate_embedding("fallback test")
        print(f"  🔄 Fallback embedding generated (dim: {len(fallback_embedding)})")
        
        # Restore client
        service.client = original_client
        service.api_available = True
        
        api_embedding = await service.generate_embedding("fallback test")
        print(f"  🌐 API embedding generated (dim: {len(api_embedding)})")
        
        # Compare if they're different (they should be)
        are_different = api_embedding != fallback_embedding
        print(f"  📊 API vs Fallback are different: {are_different}")
        
    else:
        print("  🔄 Only fallback method available (Together AI not configured)")


async def main():
    """Main test function"""
    try:
        await test_embedding_service()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())