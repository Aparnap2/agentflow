"""
Context Decision Agent - Decides what goes to global context vs local memory
Minimizes vector DB uploads and optimizes storage usage
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from loguru import logger

class ContextDecisionAgent:
    """Smart agent that decides context storage strategy"""
    
    def __init__(self):
        # Criteria for global context (vector DB)
        self.global_context_criteria = {
            "min_text_length": 100,  # Minimum text length for semantic search value
            "importance_keywords": [
                "strategy", "plan", "vision", "goal", "objective", "decision",
                "result", "outcome", "conclusion", "recommendation", "insight",
                "analysis", "summary", "key", "important", "critical", "priority"
            ],
            "content_types": {
                "vision": 0.9,      # High importance
                "plan": 0.8,        # High importance  
                "strategy": 0.8,    # High importance
                "analysis": 0.7,    # Medium-high importance
                "result": 0.7,      # Medium-high importance
                "summary": 0.6,     # Medium importance
                "update": 0.4,      # Low-medium importance
                "log": 0.2,         # Low importance
                "debug": 0.1        # Very low importance
            },
            "agent_priorities": {
                "cofounder": 0.9,   # CEO-level decisions
                "manager": 0.8,     # Project management insights
                "finance": 0.8,     # Financial analysis
                "marketing": 0.7,   # Marketing strategies
                "legal": 0.8,       # Legal compliance
                "product": 0.7,     # Product decisions
                "sales": 0.6        # Sales activities
            }
        }
        
        # Storage optimization settings
        self.max_redis_text_length = 2000  # Max text length for Redis
        self.vector_db_threshold = 0.6     # Minimum score for vector DB
        
    async def decide_storage_strategy(
        self, 
        content: Any, 
        agent_name: str, 
        memory_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Decide storage strategy for content
        Returns: {
            "strategy": "global" | "local" | "both" | "cache_only",
            "reasoning": str,
            "score": float,
            "optimized_content": Any
        }
        """
        
        # Calculate importance score
        score = await self._calculate_importance_score(content, agent_name, memory_type, metadata)
        
        # Extract and optimize content
        optimized_content = self._optimize_content_for_storage(content, memory_type)
        
        # Determine strategy based on score and content characteristics
        strategy = self._determine_strategy(score, optimized_content, memory_type)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(score, strategy, agent_name, memory_type)
        
        return {
            "strategy": strategy,
            "reasoning": reasoning,
            "score": score,
            "optimized_content": optimized_content,
            "metadata": {
                "original_size": len(str(content)),
                "optimized_size": len(str(optimized_content)),
                "agent": agent_name,
                "type": memory_type,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    async def _calculate_importance_score(
        self, 
        content: Any, 
        agent_name: str, 
        memory_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate importance score (0-1) for content"""
        
        score = 0.0
        
        # Base score from content type
        type_score = self.global_context_criteria["content_types"].get(memory_type.lower(), 0.3)
        score += type_score * 0.3
        
        # Agent priority score
        agent_score = self.global_context_criteria["agent_priorities"].get(agent_name.lower(), 0.5)
        score += agent_score * 0.2
        
        # Content analysis score
        content_score = self._analyze_content_importance(content)
        score += content_score * 0.4
        
        # Metadata boost
        if metadata:
            metadata_score = self._analyze_metadata_importance(metadata)
            score += metadata_score * 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _analyze_content_importance(self, content: Any) -> float:
        """Analyze content to determine importance"""
        
        if not content:
            return 0.0
            
        # Convert content to text for analysis
        text_content = self._extract_text_from_content(content)
        
        if not text_content or len(text_content) < 10:
            return 0.1
        
        score = 0.0
        text_lower = text_content.lower()
        
        # Length factor (longer content often more important, but with diminishing returns)
        length_score = min(len(text_content) / 1000, 0.5)  # Max 0.5 for length
        score += length_score
        
        # Keyword importance
        keyword_matches = 0
        for keyword in self.global_context_criteria["importance_keywords"]:
            if keyword in text_lower:
                keyword_matches += 1
        
        keyword_score = min(keyword_matches / len(self.global_context_criteria["importance_keywords"]), 0.3)
        score += keyword_score
        
        # Structure indicators (JSON, lists, etc.)
        if isinstance(content, dict):
            if any(key in ["result", "output", "conclusion", "decision"] for key in content.keys()):
                score += 0.2
        
        # Confidence indicator
        if isinstance(content, dict) and "confidence" in content:
            confidence = content.get("confidence", 0)
            if isinstance(confidence, (int, float)) and confidence > 0.7:
                score += 0.1
        
        return min(score, 1.0)
    
    def _analyze_metadata_importance(self, metadata: Dict[str, Any]) -> float:
        """Analyze metadata for importance indicators"""
        
        score = 0.0
        
        # High confidence boost
        if metadata.get("confidence", 0) > 0.8:
            score += 0.3
        
        # Task completion indicator
        if metadata.get("task_completed", False):
            score += 0.2
        
        # Critical flag
        if metadata.get("critical", False) or metadata.get("priority") == "high":
            score += 0.3
        
        # Shared flag
        if metadata.get("is_shared", False):
            score += 0.2
        
        return min(score, 1.0)
    
    def _extract_text_from_content(self, content: Any) -> str:
        """Extract meaningful text from various content types"""
        
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            # Extract text from common fields
            text_parts = []
            
            # Priority fields
            for field in ["content", "output", "result", "summary", "description", "text"]:
                if field in content and isinstance(content[field], str):
                    text_parts.append(content[field])
            
            # Other string values
            for key, value in content.items():
                if isinstance(value, str) and len(value) > 20 and key not in ["id", "timestamp", "agent"]:
                    text_parts.append(value)
            
            return " ".join(text_parts)
        elif isinstance(content, list):
            # Extract text from list items
            text_parts = []
            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict):
                    text_parts.append(self._extract_text_from_content(item))
            
            return " ".join(text_parts)
        else:
            return str(content)
    
    def _optimize_content_for_storage(self, content: Any, memory_type: str) -> Any:
        """Optimize content for efficient storage"""
        
        if isinstance(content, dict):
            optimized = {}
            
            # Keep essential fields
            essential_fields = ["content", "output", "result", "summary", "confidence", "type"]
            
            for field in essential_fields:
                if field in content:
                    value = content[field]
                    
                    # Truncate long text for Redis storage
                    if isinstance(value, str) and len(value) > self.max_redis_text_length:
                        optimized[field] = value[:self.max_redis_text_length] + "..."
                        optimized[f"{field}_truncated"] = True
                    else:
                        optimized[field] = value
            
            # Add metadata
            optimized["memory_type"] = memory_type
            optimized["optimized_at"] = datetime.now().isoformat()
            
            return optimized
        
        elif isinstance(content, str):
            # Truncate long strings
            if len(content) > self.max_redis_text_length:
                return {
                    "content": content[:self.max_redis_text_length] + "...",
                    "truncated": True,
                    "original_length": len(content)
                }
            return content
        
        else:
            # For other types, convert to string and truncate if needed
            str_content = str(content)
            if len(str_content) > self.max_redis_text_length:
                return {
                    "content": str_content[:self.max_redis_text_length] + "...",
                    "truncated": True,
                    "type": type(content).__name__
                }
            return content
    
    def _determine_strategy(self, score: float, content: Any, memory_type: str) -> str:
        """Determine storage strategy based on score and content"""
        
        # Very high importance - store in both
        if score >= 0.8:
            return "both"
        
        # High importance - store in global context (vector DB)
        elif score >= self.vector_db_threshold:
            return "global"
        
        # Medium importance - store locally with cache
        elif score >= 0.4:
            return "local"
        
        # Low importance - cache only
        else:
            return "cache_only"
    
    def _generate_reasoning(self, score: float, strategy: str, agent_name: str, memory_type: str) -> str:
        """Generate human-readable reasoning for the decision"""
        
        reasons = []
        
        # Score-based reasoning
        if score >= 0.8:
            reasons.append(f"High importance score ({score:.2f})")
        elif score >= 0.6:
            reasons.append(f"Medium-high importance score ({score:.2f})")
        elif score >= 0.4:
            reasons.append(f"Medium importance score ({score:.2f})")
        else:
            reasons.append(f"Low importance score ({score:.2f})")
        
        # Agent-based reasoning
        agent_priority = self.global_context_criteria["agent_priorities"].get(agent_name.lower(), 0.5)
        if agent_priority >= 0.8:
            reasons.append(f"{agent_name} is high-priority agent")
        
        # Type-based reasoning
        type_priority = self.global_context_criteria["content_types"].get(memory_type.lower(), 0.3)
        if type_priority >= 0.7:
            reasons.append(f"{memory_type} is important content type")
        
        # Strategy explanation
        strategy_explanations = {
            "both": "Storing in both global context and local memory for maximum accessibility",
            "global": "Storing in global context for cross-agent access and semantic search",
            "local": "Storing in local agent memory with Redis cache",
            "cache_only": "Storing in cache only due to low importance"
        }
        
        reasoning = f"{strategy_explanations[strategy]}. Factors: {', '.join(reasons)}"
        
        return reasoning
    
    async def should_upload_to_vector_db(self, content: Any, metadata: Dict[str, Any]) -> Tuple[bool, str]:
        """Determine if content should be uploaded to vector database"""
        
        # Check content length
        text_content = self._extract_text_from_content(content)
        if len(text_content) < self.global_context_criteria["min_text_length"]:
            return False, f"Text too short ({len(text_content)} chars, min {self.global_context_criteria['min_text_length']})"
        
        # Check importance score
        score = await self._calculate_importance_score(
            content, 
            metadata.get("agent", "unknown"), 
            metadata.get("type", "unknown"),
            metadata
        )
        
        if score < self.vector_db_threshold:
            return False, f"Importance score too low ({score:.2f}, min {self.vector_db_threshold})"
        
        return True, f"Meets criteria (score: {score:.2f}, length: {len(text_content)})"
    
    def get_storage_recommendations(self) -> Dict[str, Any]:
        """Get current storage optimization recommendations"""
        
        return {
            "global_context_criteria": {
                "min_importance_score": self.vector_db_threshold,
                "min_text_length": self.global_context_criteria["min_text_length"],
                "high_priority_agents": [
                    agent for agent, score in self.global_context_criteria["agent_priorities"].items() 
                    if score >= 0.8
                ],
                "important_content_types": [
                    content_type for content_type, score in self.global_context_criteria["content_types"].items()
                    if score >= 0.7
                ]
            },
            "optimization_settings": {
                "max_redis_text_length": self.max_redis_text_length,
                "vector_db_threshold": self.vector_db_threshold
            },
            "storage_strategies": {
                "both": "Score >= 0.8 (high importance)",
                "global": f"Score >= {self.vector_db_threshold} (medium-high importance)",
                "local": "Score >= 0.4 (medium importance)",
                "cache_only": "Score < 0.4 (low importance)"
            }
        }

# Global instance
context_decision_agent = ContextDecisionAgent()