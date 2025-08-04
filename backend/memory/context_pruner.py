"""
Context Pruner - Optimizes context size for LLM calls to reduce token usage
"""

import json
import tiktoken
from typing import Dict, Any, List, Set
from loguru import logger

class ContextPruner:
    """Prunes context to fit within token limits for LLM calls"""
    
    def __init__(self, max_tokens=4000):
        self.max_tokens = max_tokens
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")  # OpenAI's encoding
        except Exception as e:
            logger.warning(f"Failed to load tiktoken: {e}. Using fallback token estimation.")
            self.tokenizer = None
    
    def prune_context(self, context: Dict[str, Any], query: str = None) -> Dict[str, Any]:
        """Prune context to fit within token limit"""
        # Count tokens in context
        token_count = self._count_tokens(context)
        
        if token_count <= self.max_tokens:
            return context
            
        logger.info(f"Context size ({token_count} tokens) exceeds limit ({self.max_tokens}). Pruning...")
        
        # If we have a query, use it to prioritize relevant content
        if query:
            return self._prune_with_query(context, query)
        else:
            return self._prune_by_priority(context)
    
    def _count_tokens(self, obj: Any) -> int:
        """Count tokens in an object"""
        if self.tokenizer:
            # Use tiktoken for accurate counting
            return len(self.tokenizer.encode(json.dumps(obj)))
        else:
            # Fallback: rough estimation (4 chars ≈ 1 token)
            return len(json.dumps(obj)) // 4
    
    def _prune_with_query(self, context: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Prune context based on relevance to query"""
        # Calculate relevance scores
        scored_items = []
        for key, value in context.items():
            if isinstance(value, str):
                similarity = self._calculate_similarity(query, value)
                scored_items.append((key, value, similarity))
            elif isinstance(value, dict):
                # For dictionaries, score based on values
                avg_similarity = 0
                count = 0
                for k, v in value.items():
                    if isinstance(v, str):
                        avg_similarity += self._calculate_similarity(query, v)
                        count += 1
                if count > 0:
                    avg_similarity /= count
                scored_items.append((key, value, avg_similarity))
            elif isinstance(value, list) and len(value) > 0:
                # For lists, score based on string items
                avg_similarity = 0
                count = 0
                for item in value:
                    if isinstance(item, str):
                        avg_similarity += self._calculate_similarity(query, item)
                        count += 1
                if count > 0:
                    avg_similarity /= count
                scored_items.append((key, value, avg_similarity))
            else:
                # Non-string values get default medium score
                scored_items.append((key, value, 0.5))
        
        # Sort by relevance
        scored_items.sort(key=lambda x: x[2], reverse=True)
        
        # Build pruned context
        pruned_context = {}
        current_tokens = 0
        
        for key, value, _ in scored_items:
            value_tokens = self._count_tokens({key: value})
            if current_tokens + value_tokens <= self.max_tokens:
                pruned_context[key] = value
                current_tokens += value_tokens
            else:
                # Try to include partial content for lists and dicts
                if isinstance(value, list) and len(value) > 1:
                    pruned_list = self._prune_list(value, self.max_tokens - current_tokens)
                    if pruned_list:
                        pruned_context[key] = pruned_list
                        current_tokens += self._count_tokens({key: pruned_list})
                elif isinstance(value, dict) and len(value) > 1:
                    pruned_dict = self._prune_dict(value, self.max_tokens - current_tokens)
                    if pruned_dict:
                        pruned_context[key] = pruned_dict
                        current_tokens += self._count_tokens({key: pruned_dict})
        
        # Add metadata about pruning
        pruned_context["_context_pruned"] = {
            "original_keys": list(context.keys()),
            "kept_keys": list(pruned_context.keys()),
            "original_tokens": token_count,
            "pruned_tokens": current_tokens
        }
        
        return pruned_context
    
    def _prune_by_priority(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prune context based on field priority"""
        # Define priority fields
        priority_fields = [
            "task", "goal", "objective", "query", "question",  # Task-related
            "recent_actions", "current_step", "plan",          # Action-related
            "user_input", "user_request", "instructions",      # User-related
            "agent_name", "agent_role", "expertise"            # Agent-related
        ]
        
        pruned_context = {}
        current_tokens = 0
        
        # First add priority fields
        for field in priority_fields:
            if field in context:
                pruned_context[field] = context[field]
                current_tokens += self._count_tokens({field: context[field]})
        
        # Then add other fields until we hit the limit
        for key, value in context.items():
            if key not in pruned_context and key != "_context_pruned":
                value_tokens = self._count_tokens({key: value})
                if current_tokens + value_tokens <= self.max_tokens:
                    pruned_context[key] = value
                    current_tokens += value_tokens
                elif isinstance(value, (list, dict)) and len(value) > 1:
                    # Try to include partial content for lists and dicts
                    remaining_tokens = self.max_tokens - current_tokens
                    if remaining_tokens > 100:  # Only if we have reasonable space left
                        if isinstance(value, list):
                            pruned_value = self._prune_list(value, remaining_tokens)
                            if pruned_value:
                                pruned_context[key] = pruned_value
                                current_tokens += self._count_tokens({key: pruned_value})
                        else:  # dict
                            pruned_value = self._prune_dict(value, remaining_tokens)
                            if pruned_value:
                                pruned_context[key] = pruned_value
                                current_tokens += self._count_tokens({key: pruned_value})
        
        # Add metadata about pruning
        pruned_context["_context_pruned"] = {
            "original_keys": list(context.keys()),
            "kept_keys": list(pruned_context.keys()),
            "original_tokens": self._count_tokens(context),
            "pruned_tokens": current_tokens
        }
        
        return pruned_context
    
    def _prune_list(self, lst: List[Any], max_tokens: int) -> List[Any]:
        """Prune a list to fit within token limit"""
        if not lst:
            return []
            
        pruned_list = []
        current_tokens = 0
        
        for item in lst:
            item_tokens = self._count_tokens(item)
            if current_tokens + item_tokens <= max_tokens:
                pruned_list.append(item)
                current_tokens += item_tokens
            else:
                break
                
        if not pruned_list and lst:
            # If we couldn't add any items but the list is not empty,
            # try to add at least one item with truncation
            first_item = lst[0]
            if isinstance(first_item, str) and len(first_item) > 100:
                # Truncate string
                chars_to_keep = int(max_tokens * 4)  # Rough estimate: 4 chars ≈ 1 token
                truncated = first_item[:chars_to_keep] + "..."
                if self._count_tokens(truncated) <= max_tokens:
                    pruned_list.append(truncated)
            elif isinstance(first_item, dict) and len(first_item) > 1:
                # Try to keep some dict keys
                pruned_dict = self._prune_dict(first_item, max_tokens)
                if pruned_dict:
                    pruned_list.append(pruned_dict)
        
        return pruned_list
    
    def _prune_dict(self, d: Dict[str, Any], max_tokens: int) -> Dict[str, Any]:
        """Prune a dictionary to fit within token limit"""
        if not d:
            return {}
            
        pruned_dict = {}
        current_tokens = 0
        
        # First try to keep id, name, type fields if they exist
        priority_keys = ["id", "name", "type", "key", "title"]
        for key in priority_keys:
            if key in d:
                value = d[key]
                key_value_tokens = self._count_tokens({key: value})
                if current_tokens + key_value_tokens <= max_tokens:
                    pruned_dict[key] = value
                    current_tokens += key_value_tokens
        
        # Then add other keys
        for key, value in d.items():
            if key not in pruned_dict:
                key_value_tokens = self._count_tokens({key: value})
                if current_tokens + key_value_tokens <= max_tokens:
                    pruned_dict[key] = value
                    current_tokens += key_value_tokens
        
        return pruned_dict
    
    def _calculate_similarity(self, query: str, text: str) -> float:
        """Calculate semantic similarity between query and text"""
        # Simple implementation using TF-IDF and cosine similarity
        query_words = set(query.lower().split())
        text_words = set(text.lower().split())
        
        if not query_words or not text_words:
            return 0.0
            
        # Calculate word overlap
        intersection = query_words.intersection(text_words)
        
        # Simple Jaccard similarity
        return len(intersection) / (len(query_words) + len(text_words) - len(intersection))