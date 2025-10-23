"""
Summary Batcher - Handles batch processing of summaries with caching
"""
import asyncio
import logging
import sys
from typing import List, Dict, Callable, Any

logger = logging.getLogger(__name__)


def _print_progress_bar(current: int, total: int, prefix: str = '', bar_length: int = 50):
    """Print a progress bar to stdout (overwrites previous line)"""
    if total == 0:
        return
    
    progress = current / total
    filled = int(bar_length * progress)
    bar = '█' * filled + '░' * (bar_length - filled)
    
    # Print with carriage return to overwrite
    sys.stdout.write(f'\r{prefix} [{bar}] {current}/{total} ({progress*100:.1f}%)')
    sys.stdout.flush()
    
    # New line when complete
    if current == total:
        sys.stdout.write('\n')
        sys.stdout.flush()


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
        
        # Show initial progress (cached items)
        if total_count > 0:
            print(f"\n� Summarizing {total_count} chunks ({len(items)} new, {total_processed} cached)")
            _print_progress_bar(total_processed, total_count, prefix='   Progress')
        else:
            print("\n� No items to process")
            return results, error_count, fallback_count
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            
            # Process batch in parallel
            tasks = [processor(item) for item in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for item, result in zip(batch, batch_results):
                item_id = item.chunk_id if hasattr(item, 'chunk_id') else str(item)
                
                if isinstance(result, Exception):
                    error_count += 1
                    # Result should be fallback from processor
                    results[item_id] = str(result)
                    fallback_count += 1
                else:
                    results[item_id] = result
                
                total_processed += 1
                
                # Update progress bar after each item
                _print_progress_bar(total_processed, total_count, prefix='   Progress')
        
        # Print summary
        print(f"✅ Complete: {total_count} summaries ({error_count} errors, {fallback_count} fallbacks)")
        
        return results, error_count, fallback_count
