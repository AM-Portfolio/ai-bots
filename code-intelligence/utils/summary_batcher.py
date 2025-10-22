"""
Summary Batcher - Handles batch processing of summaries with caching
"""
import asyncio
import logging
from typing import List, Dict, Callable, Any

logger = logging.getLogger(__name__)


class SummaryBatcher:
    """Processes summaries in batches with progress tracking"""
    
    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
    
    def check_cache(
        self,
        items: List[Any],
        cache_getter: Callable,
        use_cache: bool = True
    ) -> tuple[List[Any], Dict[str, str]]:
        """
        Check cache for existing summaries.
        
        Args:
            items: List of items to process
            cache_getter: Function to get cached summary for an item
            use_cache: Whether to use cache
            
        Returns:
            Tuple of (items_to_process, cached_results)
        """
        if not use_cache:
            return items, {}
        
        cache_hits = 0
        items_to_process = []
        cached_results = {}
        
        for item in items:
            cached_state = cache_getter(item)
            if cached_state and hasattr(cached_state, 'summary') and cached_state.summary:
                cache_hits += 1
                item_id = item.chunk_id if hasattr(item, 'chunk_id') else str(item)
                cached_results[item_id] = cached_state.summary
            else:
                items_to_process.append(item)
        
        if cache_hits > 0:
            total = len(items)
            logger.info(f"   💾 Cache: {cache_hits}/{total} items already processed")
            logger.info(f"   🔄 Will process {len(items_to_process)} new items")
        
        return items_to_process, cached_results
    
    async def process_batches(
        self,
        items: List[Any],
        processor: Callable,
        total_count: int
    ) -> tuple[Dict[str, Any], int, int]:
        """
        Process items in batches with progress tracking.
        
        Args:
            items: Items to process
            processor: Async function to process a single item
            total_count: Total count for progress calculation
            
        Returns:
            Tuple of (results_dict, error_count, fallback_count)
        """
        results = {}
        error_count = 0
        fallback_count = 0
        total_processed = total_count - len(items)  # Already cached
        
        logger.info(f"   ⏳ Processing {len(items)} items in batches of {self.batch_size}...")
        logger.info(f"   📊 Starting: {total_processed}/{total_count} complete ({(total_processed/total_count)*100:.1f}%)")
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_start_time = asyncio.get_event_loop().time()
            
            # Process batch in parallel
            tasks = [processor(item) for item in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for item, result in zip(batch, batch_results):
                item_id = item.chunk_id if hasattr(item, 'chunk_id') else str(item)
                
                if isinstance(result, Exception):
                    error_count += 1
                    logger.debug(f"   ✗ Failed to process {item_id}: {result}")
                    # Result should be fallback from processor
                    results[item_id] = str(result)
                    fallback_count += 1
                else:
                    results[item_id] = result
                
                total_processed += 1
            
            # Calculate progress and ETA
            progress_pct = (total_processed / total_count) * 100
            batch_time = asyncio.get_event_loop().time() - batch_start_time
            avg_time_per_item = batch_time / len(batch)
            remaining_items = total_count - total_processed
            eta_seconds = remaining_items * avg_time_per_item
            eta_minutes = eta_seconds / 60
            
            # Log progress with ETA
            logger.info(
                f"   📊 Progress: {total_processed}/{total_count} items "
                f"({progress_pct:.1f}% complete) - "
                f"ETA: {eta_minutes:.1f} min"
            )
        
        return results, error_count, fallback_count
