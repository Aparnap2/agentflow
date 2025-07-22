"""
Cross-Agent Validator - Validates results across multiple agents for consistency
Enhanced version with conflict resolution database and learning capabilities
"""

import asyncio
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from datetime import datetime
from loguru import logger
import json
import re
import difflib
import numpy as np
from collections import Counter, defaultdict

class CrossAgentValidator:
    """Validates results across multiple agents for consistency"""
    
    def __init__(self, memory_manager=None, event_bus=None):
        self.memory_manager = memory_manager
        self.event_bus = event_bus
        
        # Define validation strategies for different data types
        self.validation_strategies = {
            "numerical": self._validate_numerical,
            "textual": self._validate_textual,
            "categorical": self._validate_categorical,
            "composite": self._validate_composite,
            "json": self._validate_json,
            "list": self._validate_list,
            "boolean": self._validate_boolean
        }
        
        # Define conflict resolution strategies
        self.conflict_resolution_strategies = {
            "numerical_disagreement": self._resolve_numerical_conflict,
            "textual_disagreement": self._resolve_textual_conflict,
            "categorical_disagreement": self._resolve_categorical_conflict,
            "boolean_disagreement": self._resolve_boolean_conflict,
            "json_parse_error": self._resolve_json_parse_error,
            "inconsistent_list_lengths": self._resolve_list_length_conflict
        }
        
        # Conflict resolution database for learning from past conflicts
        self.conflict_resolution_db = []
        self.max_conflict_db_size = 1000
        
        # Validation history for learning
        self.validation_history = []
        self.max_history_size = 1000
        
        # Agent reliability metrics
        self.agent_reliability = defaultdict(lambda: {
            "validations": 0,
            "consensus_matches": 0,
            "reliability_score": 0.5  # Default reliability score
        })
    
    async def validate(self, 
                     results: Dict[str, Any],
                     agents_involved: List[str],
                     validation_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate results across multiple agents
        
        Args:
            results: Dictionary mapping agent names to their results
            agents_involved: List of agent names involved in the task
            validation_type: Type of validation to perform (optional)
                If None, will attempt to auto-detect
                
        Returns:
            Dictionary containing validation results
        """
        # Check if we have results from all expected agents
        missing_agents = [agent for agent in agents_involved if agent not in results]
        if missing_agents:
            logger.warning(f"Missing results from agents: {missing_agents}")
        
        # If only one agent, no validation needed
        if len(results) <= 1:
            agent = next(iter(results.keys())) if results else None
            return {
                "is_valid": True,
                "confidence": 1.0,
                "consensus_result": results.get(agent, None),
                "consensus_agent": agent,
                "validation_type": "single_agent",
                "conflicts": [],
                "timestamp": datetime.now().isoformat()
            }
        
        # Auto-detect validation type if not provided
        if not validation_type:
            validation_type = await self._detect_validation_type(results)
            logger.info(f"Auto-detected validation type: {validation_type}")
        
        # Get validation strategy
        validation_func = self.validation_strategies.get(validation_type)
        if not validation_func:
            logger.warning(f"Unknown validation type: {validation_type}, falling back to textual")
            validation_func = self._validate_textual
        
        # Perform validation
        validation_result = await validation_func(results)
        
        # Add metadata
        validation_result["validation_type"] = validation_type
        validation_result["timestamp"] = datetime.now().isoformat()
        
        # Record validation for history
        self._record_validation(validation_type, results, validation_result)
        
        return validation_result
    
    async def _detect_validation_type(self, results: Dict[str, Any]) -> str:
        """Auto-detect validation type based on result values"""
        # Get first result for type checking
        first_agent = next(iter(results.keys()))
        first_result = results[first_agent]
        
        # Check if all results are of the same type
        result_types = set()
        for result in results.values():
            if isinstance(result, (int, float)):
                result_types.add("numerical")
            elif isinstance(result, str):
                result_types.add("textual")
            elif isinstance(result, bool):
                result_types.add("boolean")
            elif isinstance(result, list):
                result_types.add("list")
            elif isinstance(result, dict):
                # Check if it's a simple categorical result
                if all(isinstance(v, (str, int, float, bool)) for v in result.values()):
                    result_types.add("categorical")
                else:
                    result_types.add("composite")
            else:
                result_types.add("unknown")
        
        # If all results are of the same type, use that type
        if len(result_types) == 1:
            return result_types.pop()
        
        # If mixed types, check if it's JSON
        try:
            if all(isinstance(r, str) for r in results.values()):
                # Try to parse all as JSON
                if all(self._try_parse_json(r) for r in results.values()):
                    return "json"
        except:
            pass
        
        # Default to textual for mixed types
        return "textual"
    
    def _try_parse_json(self, text: str) -> bool:
        """Try to parse text as JSON"""
        try:
            if isinstance(text, str):
                json.loads(text)
                return True
        except:
            pass
        return False
    
    async def _validate_numerical(self, 
                                values: Dict[str, Union[int, float]],
                                tolerance: float = 0.1) -> Dict[str, Any]:
        """
        Validate numerical values across agents
        
        Args:
            values: Dictionary mapping agent names to numerical values
            tolerance: Relative tolerance for numerical comparison
                
        Returns:
            Dictionary containing validation results
        """
        # Convert all values to float for comparison
        float_values = {agent: float(value) for agent, value in values.items()}
        
        # Calculate statistics
        all_values = list(float_values.values())
        mean_value = sum(all_values) / len(all_values)
        max_value = max(all_values)
        min_value = min(all_values)
        range_value = max_value - min_value
        
        # Check if values are within tolerance
        relative_range = range_value / mean_value if mean_value != 0 else float('inf')
        is_valid = relative_range <= tolerance
        
        # Identify outliers (values outside 2 standard deviations)
        std_dev = np.std(all_values) if len(all_values) > 1 else 0
        outliers = {}
        for agent, value in float_values.items():
            if abs(value - mean_value) > 2 * std_dev:
                outliers[agent] = value
        
        # Find consensus value (median to avoid outlier influence)
        consensus_value = sorted(all_values)[len(all_values) // 2]
        
        # Find agent with closest value to consensus
        consensus_agent = min(float_values.items(), key=lambda x: abs(x[1] - consensus_value))[0]
        
        # Calculate confidence based on agreement
        if is_valid:
            confidence = 1.0 - (relative_range / tolerance)
        else:
            confidence = max(0.0, 1.0 - (relative_range / (tolerance * 3)))
        
        # Identify conflicts
        conflicts = []
        for agent1, value1 in float_values.items():
            for agent2, value2 in float_values.items():
                if agent1 < agent2:  # Avoid duplicate pairs
                    rel_diff = abs(value1 - value2) / max(abs(value1), abs(value2), 1e-10)
                    if rel_diff > tolerance:
                        conflicts.append({
                            "agents": [agent1, agent2],
                            "values": [value1, value2],
                            "difference": rel_diff,
                            "type": "numerical_disagreement"
                        })
        
        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "consensus_result": consensus_value,
            "consensus_agent": consensus_agent,
            "statistics": {
                "mean": mean_value,
                "min": min_value,
                "max": max_value,
                "range": range_value,
                "relative_range": relative_range,
                "std_dev": std_dev
            },
            "outliers": outliers,
            "conflicts": conflicts
        }
    
    async def _validate_textual(self, texts: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate textual content across agents
        
        Args:
            texts: Dictionary mapping agent names to text content
                
        Returns:
            Dictionary containing validation results
        """
        # Calculate similarity matrix
        agents = list(texts.keys())
        similarity_matrix = {}
        
        for i, agent1 in enumerate(agents):
            similarity_matrix[agent1] = {}
            for j, agent2 in enumerate(agents):
                if i == j:
                    similarity_matrix[agent1][agent2] = 1.0
                else:
                    # Calculate similarity using difflib
                    text1 = texts[agent1].lower()
                    text2 = texts[agent2].lower()
                    similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
                    similarity_matrix[agent1][agent2] = similarity
        
        # Calculate average similarity for each agent
        avg_similarities = {}
        for agent in agents:
            avg_similarities[agent] = sum(similarity_matrix[agent].values()) / len(agents)
        
        # Find consensus agent (highest average similarity)
        consensus_agent = max(avg_similarities.items(), key=lambda x: x[1])[0]
        consensus_text = texts[consensus_agent]
        
        # Calculate overall similarity
        overall_similarity = sum(avg_similarities.values()) / len(agents)
        
        # Determine if valid based on similarity threshold
        similarity_threshold = 0.7
        is_valid = overall_similarity >= similarity_threshold
        
        # Calculate confidence
        confidence = overall_similarity
        
        # Identify conflicts (pairs with low similarity)
        conflicts = []
        for i, agent1 in enumerate(agents):
            for j, agent2 in enumerate(agents):
                if i < j:  # Avoid duplicate pairs
                    similarity = similarity_matrix[agent1][agent2]
                    if similarity < similarity_threshold:
                        conflicts.append({
                            "agents": [agent1, agent2],
                            "similarity": similarity,
                            "type": "textual_disagreement"
                        })
        
        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "consensus_result": consensus_text,
            "consensus_agent": consensus_agent,
            "similarity_matrix": similarity_matrix,
            "avg_similarities": avg_similarities,
            "overall_similarity": overall_similarity,
            "conflicts": conflicts
        }
    
    async def _validate_categorical(self, categories: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate categorical values across agents
        
        Args:
            categories: Dictionary mapping agent names to category values
                
        Returns:
            Dictionary containing validation results
        """
        # Count occurrences of each category
        category_counts = Counter(categories.values())
        
        # Find most common category
        most_common = category_counts.most_common(1)[0]
        consensus_category = most_common[0]
        consensus_count = most_common[1]
        
        # Calculate agreement ratio
        agreement_ratio = consensus_count / len(categories)
        
        # Find agents with consensus category
        consensus_agents = [agent for agent, category in categories.items() if category == consensus_category]
        
        # Choose a representative consensus agent
        consensus_agent = consensus_agents[0] if consensus_agents else None
        
        # Determine if valid based on agreement threshold
        agreement_threshold = 0.5  # More than half should agree
        is_valid = agreement_ratio >= agreement_threshold
        
        # Calculate confidence
        confidence = agreement_ratio
        
        # Identify conflicts (agents not agreeing with consensus)
        conflicts = []
        for agent, category in categories.items():
            if category != consensus_category:
                conflicts.append({
                    "agent": agent,
                    "value": category,
                    "consensus_value": consensus_category,
                    "type": "categorical_disagreement"
                })
        
        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "consensus_result": consensus_category,
            "consensus_agent": consensus_agent,
            "category_counts": dict(category_counts),
            "agreement_ratio": agreement_ratio,
            "conflicts": conflicts
        }
    
    async def _validate_composite(self, results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate composite results across agents
        
        Args:
            results: Dictionary mapping agent names to composite results
                
        Returns:
            Dictionary containing validation results
        """
        # Extract all keys from all results
        all_keys = set()
        for result in results.values():
            all_keys.update(result.keys())
        
        # Validate each key separately
        key_validations = {}
        for key in all_keys:
            # Extract values for this key from each agent
            key_values = {}
            for agent, result in results.items():
                if key in result:
                    key_values[agent] = result[key]
            
            # Skip keys that only appear in one agent's result
            if len(key_values) <= 1:
                continue
            
            # Auto-detect validation type for this key
            key_type = await self._detect_validation_type(key_values)
            
            # Validate this key
            validation_func = self.validation_strategies.get(key_type, self._validate_textual)
            key_validations[key] = await validation_func(key_values)
        
        # Calculate overall validation metrics
        valid_keys = sum(1 for v in key_validations.values() if v["is_valid"])
        total_keys = len(key_validations)
        
        if total_keys == 0:
            # No keys to validate
            return {
                "is_valid": True,
                "confidence": 1.0,
                "consensus_result": next(iter(results.values())) if results else {},
                "consensus_agent": next(iter(results.keys())) if results else None,
                "conflicts": []
            }
        
        # Calculate validity ratio
        validity_ratio = valid_keys / total_keys
        
        # Calculate average confidence
        avg_confidence = sum(v["confidence"] for v in key_validations.values()) / total_keys
        
        # Determine if valid based on validity threshold
        validity_threshold = 0.7
        is_valid = validity_ratio >= validity_threshold
        
        # Build consensus result by taking consensus values for each key
        consensus_result = {}
        for key, validation in key_validations.items():
            consensus_result[key] = validation["consensus_result"]
        
        # Find agent with most consensus contributions
        agent_consensus_counts = {agent: 0 for agent in results.keys()}
        for key, validation in key_validations.items():
            consensus_agent = validation.get("consensus_agent")
            if consensus_agent:
                agent_consensus_counts[consensus_agent] += 1
        
        consensus_agent = max(agent_consensus_counts.items(), key=lambda x: x[1])[0] if agent_consensus_counts else None
        
        # Collect all conflicts
        all_conflicts = []
        for key, validation in key_validations.items():
            for conflict in validation.get("conflicts", []):
                conflict["key"] = key
                all_conflicts.append(conflict)
        
        return {
            "is_valid": is_valid,
            "confidence": avg_confidence,
            "consensus_result": consensus_result,
            "consensus_agent": consensus_agent,
            "key_validations": key_validations,
            "validity_ratio": validity_ratio,
            "conflicts": all_conflicts
        }
    
    async def _validate_json(self, json_texts: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate JSON strings across agents
        
        Args:
            json_texts: Dictionary mapping agent names to JSON strings
                
        Returns:
            Dictionary containing validation results
        """
        # Parse JSON strings
        parsed_jsons = {}
        parse_errors = {}
        
        for agent, text in json_texts.items():
            try:
                parsed_jsons[agent] = json.loads(text)
            except json.JSONDecodeError as e:
                parse_errors[agent] = str(e)
        
        # If any parsing errors, return them
        if parse_errors:
            return {
                "is_valid": False,
                "confidence": 0.0,
                "consensus_result": None,
                "consensus_agent": None,
                "parse_errors": parse_errors,
                "conflicts": [{"type": "json_parse_error", "errors": parse_errors}]
            }
        
        # Validate parsed JSON objects
        return await self._validate_composite(parsed_jsons)
    
    async def _validate_list(self, lists: Dict[str, List[Any]]) -> Dict[str, Any]:
        """
        Validate lists across agents
        
        Args:
            lists: Dictionary mapping agent names to lists
                
        Returns:
            Dictionary containing validation results
        """
        # Check list lengths
        lengths = {agent: len(lst) for agent, lst in lists.items()}
        
        # Find most common length
        length_counts = Counter(lengths.values())
        most_common_length = length_counts.most_common(1)[0][0]
        
        # Calculate length agreement ratio
        length_agreement = sum(1 for l in lengths.values() if l == most_common_length) / len(lists)
        
        # For lists of different lengths, it's hard to compare directly
        # We'll focus on lists with the most common length
        consistent_lists = {agent: lst for agent, lst in lists.items() if len(lst) == most_common_length}
        
        # If no consistent lists, return error
        if not consistent_lists:
            return {
                "is_valid": False,
                "confidence": 0.0,
                "consensus_result": [],
                "consensus_agent": None,
                "conflicts": [{"type": "inconsistent_list_lengths", "lengths": lengths}]
            }
        
        # For lists with same length, compare elements
        element_validations = []
        
        # Check if lists contain simple types or complex types
        first_list = next(iter(consistent_lists.values()))
        if not first_list:
            # Empty lists
            return {
                "is_valid": True,
                "confidence": 1.0,
                "consensus_result": [],
                "consensus_agent": next(iter(consistent_lists.keys())),
                "conflicts": []
            }
        
        # Check if elements are simple or complex
        if all(isinstance(item, (int, float, str, bool)) for item in first_list):
            # Simple elements - validate each position
            for i in range(most_common_length):
                position_values = {agent: lst[i] for agent, lst in consistent_lists.items()}
                element_type = await self._detect_validation_type(position_values)
                validation_func = self.validation_strategies.get(element_type, self._validate_textual)
                element_validations.append(await validation_func(position_values))
        else:
            # Complex elements - use set-based comparison
            # Convert lists to sets of serialized items
            serialized_sets = {}
            for agent, lst in consistent_lists.items():
                serialized_items = []
                for item in lst:
                    if isinstance(item, dict):
                        # Sort dict items for consistent serialization
                        serialized = json.dumps(item, sort_keys=True)
                    else:
                        serialized = str(item)
                    serialized_items.append(serialized)
                serialized_sets[agent] = set(serialized_items)
            
            # Calculate Jaccard similarity between sets
            agents = list(serialized_sets.keys())
            similarity_matrix = {}
            
            for i, agent1 in enumerate(agents):
                similarity_matrix[agent1] = {}
                for j, agent2 in enumerate(agents):
                    if i == j:
                        similarity_matrix[agent1][agent2] = 1.0
                    else:
                        set1 = serialized_sets[agent1]
                        set2 = serialized_sets[agent2]
                        # Jaccard similarity: |A ∩ B| / |A ∪ B|
                        intersection = len(set1.intersection(set2))
                        union = len(set1.union(set2))
                        similarity = intersection / union if union > 0 else 0
                        similarity_matrix[agent1][agent2] = similarity
            
            # Calculate average similarity for each agent
            avg_similarities = {}
            for agent in agents:
                avg_similarities[agent] = sum(similarity_matrix[agent].values()) / len(agents)
            
            # Find consensus agent (highest average similarity)
            consensus_agent = max(avg_similarities.items(), key=lambda x: x[1])[0]
            consensus_list = lists[consensus_agent]
            
            # Calculate overall similarity
            overall_similarity = sum(avg_similarities.values()) / len(agents)
            
            # Determine if valid based on similarity threshold
            similarity_threshold = 0.7
            is_valid = overall_similarity >= similarity_threshold
            
            return {
                "is_valid": is_valid,
                "confidence": overall_similarity,
                "consensus_result": consensus_list,
                "consensus_agent": consensus_agent,
                "similarity_matrix": similarity_matrix,
                "avg_similarities": avg_similarities,
                "overall_similarity": overall_similarity,
                "conflicts": []
            }
        
        # Calculate overall validation metrics for simple elements
        valid_elements = sum(1 for v in element_validations if v["is_valid"])
        total_elements = len(element_validations)
        
        # Calculate validity ratio
        validity_ratio = valid_elements / total_elements if total_elements > 0 else 1.0
        
        # Calculate average confidence
        avg_confidence = sum(v["confidence"] for v in element_validations) / total_elements if total_elements > 0 else 1.0
        
        # Determine if valid based on validity threshold
        validity_threshold = 0.7
        is_valid = validity_ratio >= validity_threshold
        
        # Build consensus list by taking consensus values for each position
        consensus_list = [v["consensus_result"] for v in element_validations]
        
        # Find agent with most consensus contributions
        agent_consensus_counts = {agent: 0 for agent in consistent_lists.keys()}
        for validation in element_validations:
            consensus_agent = validation.get("consensus_agent")
            if consensus_agent:
                agent_consensus_counts[consensus_agent] += 1
        
        consensus_agent = max(agent_consensus_counts.items(), key=lambda x: x[1])[0] if agent_consensus_counts else None
        
        # Collect all conflicts
        all_conflicts = []
        for i, validation in enumerate(element_validations):
            for conflict in validation.get("conflicts", []):
                conflict["position"] = i
                all_conflicts.append(conflict)
        
        return {
            "is_valid": is_valid,
            "confidence": avg_confidence,
            "consensus_result": consensus_list,
            "consensus_agent": consensus_agent,
            "element_validations": element_validations,
            "validity_ratio": validity_ratio,
            "conflicts": all_conflicts
        }
    
    async def _validate_boolean(self, booleans: Dict[str, bool]) -> Dict[str, Any]:
        """
        Validate boolean values across agents
        
        Args:
            booleans: Dictionary mapping agent names to boolean values
                
        Returns:
            Dictionary containing validation results
        """
        # Count True and False values
        true_count = sum(1 for v in booleans.values() if v)
        false_count = sum(1 for v in booleans.values() if not v)
        
        # Determine consensus value
        consensus_value = true_count >= false_count
        
        # Calculate agreement ratio
        total_count = true_count + false_count
        consensus_count = true_count if consensus_value else false_count
        agreement_ratio = consensus_count / total_count if total_count > 0 else 1.0
        
        # Find agents with consensus value
        consensus_agents = [agent for agent, value in booleans.items() if value == consensus_value]
        
        # Choose a representative consensus agent
        consensus_agent = consensus_agents[0] if consensus_agents else None
        
        # Determine if valid based on agreement threshold
        agreement_threshold = 0.5  # More than half should agree
        is_valid = agreement_ratio >= agreement_threshold
        
        # Calculate confidence
        confidence = agreement_ratio
        
        # Identify conflicts (agents not agreeing with consensus)
        conflicts = []
        for agent, value in booleans.items():
            if value != consensus_value:
                conflicts.append({
                    "agent": agent,
                    "value": value,
                    "consensus_value": consensus_value,
                    "type": "boolean_disagreement"
                })
        
        return {
            "is_valid": is_valid,
            "confidence": confidence,
            "consensus_result": consensus_value,
            "consensus_agent": consensus_agent,
            "true_count": true_count,
            "false_count": false_count,
            "agreement_ratio": agreement_ratio,
            "conflicts": conflicts
        }
    
    def _record_validation(self, validation_type: str, results: Dict[str, Any], validation_result: Dict[str, Any]) -> None:
        """Record validation for history"""
        validation_record = {
            "validation_type": validation_type,
            "agent_count": len(results),
            "is_valid": validation_result["is_valid"],
            "confidence": validation_result["confidence"],
            "conflict_count": len(validation_result.get("conflicts", [])),
            "timestamp": datetime.now().isoformat()
        }
        
        self.validation_history.append(validation_record)
        
        # Limit history size
        if len(self.validation_history) > self.max_history_size:
            self.validation_history = self.validation_history[-self.max_history_size:]
    
    async def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics from history"""
        if not self.validation_history:
            return {
                "total_validations": 0,
                "valid_percentage": 0,
                "average_confidence": 0,
                "average_conflict_count": 0
            }
        
        total = len(self.validation_history)
        valid_count = sum(1 for v in self.validation_history if v["is_valid"])
        valid_percentage = (valid_count / total) * 100 if total > 0 else 0
        
        avg_confidence = sum(v["confidence"] for v in self.validation_history) / total if total > 0 else 0
        avg_conflict_count = sum(v["conflict_count"] for v in self.validation_history) / total if total > 0 else 0
        
        # Group by validation type
        by_type = {}
        for record in self.validation_history:
            v_type = record["validation_type"]
            if v_type not in by_type:
                by_type[v_type] = {
                    "count": 0,
                    "valid_count": 0,
                    "total_confidence": 0,
                    "total_conflict_count": 0
                }
            
            by_type[v_type]["count"] += 1
            if record["is_valid"]:
                by_type[v_type]["valid_count"] += 1
            by_type[v_type]["total_confidence"] += record["confidence"]
            by_type[v_type]["total_conflict_count"] += record["conflict_count"]
        
        # Calculate statistics by type
        type_stats = {}
        for v_type, stats in by_type.items():
            count = stats["count"]
            type_stats[v_type] = {
                "count": count,
                "valid_percentage": (stats["valid_count"] / count) * 100 if count > 0 else 0,
                "average_confidence": stats["total_confidence"] / count if count > 0 else 0,
                "average_conflict_count": stats["total_conflict_count"] / count if count > 0 else 0
            }
        
        return {
            "total_validations": total,
            "valid_percentage": valid_percentage,
            "average_confidence": avg_confidence,
            "average_conflict_count": avg_conflict_count,
            "by_type": type_stats
        }    asyn
c def resolve_conflicts(self, 
                              validation_result: Dict[str, Any],
                              task_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Resolve conflicts in validation results using appropriate strategies
        
        Args:
            validation_result: Validation result from validate() method
            task_data: Optional task data for context
                
        Returns:
            Dictionary containing resolved results
        """
        conflicts = validation_result.get("conflicts", [])
        if not conflicts:
            # No conflicts to resolve
            return validation_result
            
        # Group conflicts by type
        conflicts_by_type = defaultdict(list)
        for conflict in conflicts:
            conflict_type = conflict.get("type", "unknown")
            conflicts_by_type[conflict_type].append(conflict)
            
        # Resolve each conflict type
        resolved_conflicts = []
        for conflict_type, type_conflicts in conflicts_by_type.items():
            # Get resolution strategy
            resolution_func = self.conflict_resolution_strategies.get(conflict_type)
            if resolution_func:
                # Apply resolution strategy
                resolution_result = await resolution_func(type_conflicts, validation_result, task_data)
                resolved_conflicts.extend(resolution_result.get("resolved_conflicts", []))
                
                # Update validation result with resolution
                if "updated_consensus" in resolution_result:
                    validation_result["consensus_result"] = resolution_result["updated_consensus"]
                    
                # Update confidence if provided
                if "updated_confidence" in resolution_result:
                    validation_result["confidence"] = resolution_result["updated_confidence"]
            else:
                # No resolution strategy for this conflict type
                resolved_conflicts.extend(type_conflicts)
                
        # Update validation result
        validation_result["original_conflicts"] = conflicts
        validation_result["resolved_conflicts"] = resolved_conflicts
        validation_result["mediation_applied"] = True
        
        # Record conflict resolution in database
        self._record_conflict_resolution(validation_result)
        
        return validation_result
        
    async def _resolve_numerical_conflict(self, 
                                        conflicts: List[Dict[str, Any]],
                                        validation_result: Dict[str, Any],
                                        task_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resolve numerical conflicts"""
        # Check if we have similar conflicts in the database
        similar_resolutions = await self._find_similar_resolutions(conflicts, "numerical_disagreement")
        
        if similar_resolutions:
            # Use past resolution strategy
            best_resolution = similar_resolutions[0]
            resolution_strategy = best_resolution.get("resolution_strategy", "median")
        else:
            # Default strategy: use median value
            resolution_strategy = "median"
            
        # Apply resolution strategy
        if resolution_strategy == "median":
            # Extract all values from conflicts
            all_values = []
            for conflict in conflicts:
                all_values.extend(conflict.get("values", []))
                
            # Calculate median
            if all_values:
                all_values.sort()
                median_value = all_values[len(all_values) // 2]
                
                # Update consensus
                updated_consensus = median_value
                
                # Calculate confidence based on standard deviation
                std_dev = np.std(all_values) if len(all_values) > 1 else 0
                mean_value = sum(all_values) / len(all_values)
                
                # Lower confidence for higher standard deviation
                if mean_value != 0:
                    relative_std_dev = std_dev / abs(mean_value)
                    updated_confidence = max(0.5, 1.0 - relative_std_dev)
                else:
                    updated_confidence = 0.7  # Default confidence
            else:
                # No values to resolve
                updated_consensus = validation_result.get("consensus_result")
                updated_confidence = validation_result.get("confidence", 0.7)
        else:
            # Unknown strategy, keep original consensus
            updated_consensus = validation_result.get("consensus_result")
            updated_confidence = validation_result.get("confidence", 0.7)
            
        # Mark conflicts as resolved
        resolved_conflicts = []
        for conflict in conflicts:
            resolved_conflict = conflict.copy()
            resolved_conflict["resolved"] = True
            resolved_conflict["resolution_strategy"] = resolution_strategy
            resolved_conflict["resolved_value"] = updated_consensus
            resolved_conflicts.append(resolved_conflict)
            
        return {
            "resolved_conflicts": resolved_conflicts,
            "updated_consensus": updated_consensus,
            "updated_confidence": updated_confidence,
            "resolution_strategy": resolution_strategy
        }
        
    async def _resolve_textual_conflict(self, 
                                      conflicts: List[Dict[str, Any]],
                                      validation_result: Dict[str, Any],
                                      task_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resolve textual conflicts"""
        # Check if we have similar conflicts in the database
        similar_resolutions = await self._find_similar_resolutions(conflicts, "textual_disagreement")
        
        if similar_resolutions:
            # Use past resolution strategy
            best_resolution = similar_resolutions[0]
            resolution_strategy = best_resolution.get("resolution_strategy", "highest_similarity")
        else:
            # Default strategy: use text from agent with highest average similarity
            resolution_strategy = "highest_similarity"
            
        # Keep original consensus which should already be from highest similarity agent
        updated_consensus = validation_result.get("consensus_result")
        updated_confidence = validation_result.get("confidence", 0.7)
        
        # Mark conflicts as resolved
        resolved_conflicts = []
        for conflict in conflicts:
            resolved_conflict = conflict.copy()
            resolved_conflict["resolved"] = True
            resolved_conflict["resolution_strategy"] = resolution_strategy
            resolved_conflicts.append(resolved_conflict)
            
        return {
            "resolved_conflicts": resolved_conflicts,
            "updated_consensus": updated_consensus,
            "updated_confidence": updated_confidence,
            "resolution_strategy": resolution_strategy
        }
        
    async def _resolve_categorical_conflict(self, 
                                          conflicts: List[Dict[str, Any]],
                                          validation_result: Dict[str, Any],
                                          task_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resolve categorical conflicts"""
        # Check if we have similar conflicts in the database
        similar_resolutions = await self._find_similar_resolutions(conflicts, "categorical_disagreement")
        
        if similar_resolutions:
            # Use past resolution strategy
            best_resolution = similar_resolutions[0]
            resolution_strategy = best_resolution.get("resolution_strategy", "majority_vote")
        else:
            # Default strategy: majority vote
            resolution_strategy = "majority_vote"
            
        # Keep original consensus which should already be from majority vote
        updated_consensus = validation_result.get("consensus_result")
        updated_confidence = validation_result.get("confidence", 0.7)
        
        # Mark conflicts as resolved
        resolved_conflicts = []
        for conflict in conflicts:
            resolved_conflict = conflict.copy()
            resolved_conflict["resolved"] = True
            resolved_conflict["resolution_strategy"] = resolution_strategy
            resolved_conflicts.append(resolved_conflict)
            
        return {
            "resolved_conflicts": resolved_conflicts,
            "updated_consensus": updated_consensus,
            "updated_confidence": updated_confidence,
            "resolution_strategy": resolution_strategy
        }
        
    async def _resolve_boolean_conflict(self, 
                                      conflicts: List[Dict[str, Any]],
                                      validation_result: Dict[str, Any],
                                      task_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resolve boolean conflicts"""
        # Similar to categorical, use majority vote
        return await self._resolve_categorical_conflict(conflicts, validation_result, task_data)
        
    async def _resolve_json_parse_error(self, 
                                      conflicts: List[Dict[str, Any]],
                                      validation_result: Dict[str, Any],
                                      task_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resolve JSON parse errors"""
        # Strategy: use valid JSON from agents without parse errors
        resolution_strategy = "valid_json_only"
        
        # Find agents with parse errors
        parse_errors = validation_result.get("parse_errors", {})
        
        # If all agents have parse errors, we can't resolve
        if len(parse_errors) == len(validation_result.get("results", {})):
            return {
                "resolved_conflicts": conflicts,
                "updated_consensus": None,
                "updated_confidence": 0.0,
                "resolution_strategy": resolution_strategy
            }
            
        # Find a valid JSON from an agent without parse errors
        valid_json = None
        for agent, result in validation_result.get("results", {}).items():
            if agent not in parse_errors:
                valid_json = result
                break
                
        # Mark conflicts as resolved
        resolved_conflicts = []
        for conflict in conflicts:
            resolved_conflict = conflict.copy()
            resolved_conflict["resolved"] = True
            resolved_conflict["resolution_strategy"] = resolution_strategy
            resolved_conflicts.append(resolved_conflict)
            
        return {
            "resolved_conflicts": resolved_conflicts,
            "updated_consensus": valid_json,
            "updated_confidence": 0.6,  # Lower confidence due to parse errors
            "resolution_strategy": resolution_strategy
        }
        
    async def _resolve_list_length_conflict(self, 
                                          conflicts: List[Dict[str, Any]],
                                          validation_result: Dict[str, Any],
                                          task_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Resolve list length conflicts"""
        # Strategy: use list with most common length
        resolution_strategy = "most_common_length"
        
        # Find most common length
        lengths = conflicts[0].get("lengths", {})
        length_counts = Counter(lengths.values())
        
        if not length_counts:
            return {
                "resolved_conflicts": conflicts,
                "resolution_strategy": resolution_strategy
            }
            
        most_common_length = length_counts.most_common(1)[0][0]
        
        # Find a list with the most common length
        updated_consensus = None
        for agent, length in lengths.items():
            if length == most_common_length:
                updated_consensus = validation_result.get("results", {}).get(agent)
                break
                
        # Mark conflicts as resolved
        resolved_conflicts = []
        for conflict in conflicts:
            resolved_conflict = conflict.copy()
            resolved_conflict["resolved"] = True
            resolved_conflict["resolution_strategy"] = resolution_strategy
            resolved_conflict["most_common_length"] = most_common_length
            resolved_conflicts.append(resolved_conflict)
            
        return {
            "resolved_conflicts": resolved_conflicts,
            "updated_consensus": updated_consensus,
            "updated_confidence": 0.6,  # Lower confidence due to length conflicts
            "resolution_strategy": resolution_strategy
        }
        
    async def _find_similar_resolutions(self, 
                                      conflicts: List[Dict[str, Any]],
                                      conflict_type: str) -> List[Dict[str, Any]]:
        """Find similar conflict resolutions in the database"""
        if not self.conflict_resolution_db:
            return []
            
        # Extract key features from conflicts
        conflict_features = {
            "type": conflict_type,
            "agent_count": len(set(agent for conflict in conflicts for agent in conflict.get("agents", []))),
        }
        
        # Find similar resolutions
        similar_resolutions = []
        for resolution in self.conflict_resolution_db:
            if resolution.get("conflict_type") == conflict_type:
                # Calculate similarity score
                similarity = 0
                
                # Type match
                if resolution.get("conflict_type") == conflict_features["type"]:
                    similarity += 0.5
                    
                # Agent count similarity
                agent_count_diff = abs(resolution.get("agent_count", 0) - conflict_features["agent_count"])
                if agent_count_diff == 0:
                    similarity += 0.3
                elif agent_count_diff <= 2:
                    similarity += 0.1
                    
                # Success score
                if resolution.get("success_score", 0) > 0.7:
                    similarity += 0.2
                    
                # Add to similar resolutions if similarity is high enough
                if similarity > 0.6:
                    similar_resolutions.append({
                        "resolution": resolution,
                        "similarity": similarity
                    })
                    
        # Sort by similarity
        similar_resolutions.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Return resolutions only
        return [item["resolution"] for item in similar_resolutions]
        
    def _record_conflict_resolution(self, validation_result: Dict[str, Any]) -> None:
        """Record conflict resolution in database"""
        resolution_record = {
            "conflict_type": validation_result.get("validation_type"),
            "agent_count": len(validation_result.get("results", {})),
            "conflict_count": len(validation_result.get("original_conflicts", [])),
            "resolution_strategy": validation_result.get("resolution_strategy", "unknown"),
            "confidence": validation_result.get("confidence", 0),
            "success_score": 0.5,  # Initial score, will be updated later
            "timestamp": datetime.now().isoformat()
        }
        
        self.conflict_resolution_db.append(resolution_record)
        
        # Limit database size
        if len(self.conflict_resolution_db) > self.max_conflict_db_size:
            self.conflict_resolution_db = self.conflict_resolution_db[-self.max_conflict_db_size:]
            
    async def update_resolution_success(self, 
                                      resolution_id: str, 
                                      success_score: float) -> bool:
        """
        Update success score for a conflict resolution
        
        Args:
            resolution_id: ID of the resolution to update
            success_score: Success score (0.0 to 1.0)
                
        Returns:
            True if successful, False otherwise
        """
        for resolution in self.conflict_resolution_db:
            if resolution.get("id") == resolution_id:
                resolution["success_score"] = success_score
                return True
                
        return False
        
    async def get_agent_reliability(self) -> Dict[str, float]:
        """
        Get reliability scores for all agents
        
        Returns:
            Dictionary mapping agent names to reliability scores
        """
        return {agent: data["reliability_score"] for agent, data in self.agent_reliability.items()}
        
    async def update_agent_reliability(self, 
                                     validation_result: Dict[str, Any]) -> None:
        """
        Update agent reliability based on validation result
        
        Args:
            validation_result: Validation result from validate() method
        """
        consensus_agent = validation_result.get("consensus_agent")
        if not consensus_agent:
            return
            
        # Update reliability for all agents involved
        for agent in validation_result.get("results", {}).keys():
            # Increment validation count
            self.agent_reliability[agent]["validations"] += 1
            
            # If agent matches consensus, increment consensus matches
            if agent == consensus_agent:
                self.agent_reliability[agent]["consensus_matches"] += 1
                
            # Update reliability score
            validations = self.agent_reliability[agent]["validations"]
            matches = self.agent_reliability[agent]["consensus_matches"]
            
            if validations > 0:
                # Use weighted average to prevent wild swings
                current_score = self.agent_reliability[agent]["reliability_score"]
                new_score = matches / validations
                
                # Weight more heavily toward recent performance
                self.agent_reliability[agent]["reliability_score"] = (current_score * 0.7) + (new_score * 0.3)
                
    async def mediate_conflict(self, 
                             conflict: Dict[str, Any],
                             agents_involved: List[str]) -> Dict[str, Any]:
        """
        Perform automated mediation for a conflict
        
        Args:
            conflict: Conflict data
            agents_involved: List of agent names involved in the conflict
                
        Returns:
            Dictionary containing mediation result
        """
        conflict_type = conflict.get("type", "unknown")
        
        # Check if we have a resolution strategy for this conflict type
        if conflict_type in self.conflict_resolution_strategies:
            # Create a minimal validation result for resolution
            validation_result = {
                "conflicts": [conflict],
                "results": {agent: None for agent in agents_involved}
            }
            
            # Apply resolution strategy
            resolution_func = self.conflict_resolution_strategies[conflict_type]
            resolution_result = await resolution_func([conflict], validation_result)
            
            return {
                "mediated": True,
                "resolution": resolution_result,
                "mediation_strategy": resolution_result.get("resolution_strategy", "unknown")
            }
        else:
            # No resolution strategy available
            return {
                "mediated": False,
                "reason": f"No mediation strategy available for conflict type: {conflict_type}"
            }