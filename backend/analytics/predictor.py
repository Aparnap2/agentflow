"""
Minimal predictive analytics for MVP - simple trend analysis and recommendations
"""

from typing import Dict, List, Any
from datetime import datetime

class SimplePredictor:
    """Lightweight predictor using basic statistical methods"""
    
    def predict_project_success(self, agent_outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Predict project success probability"""
        
        # Extract confidence scores
        confidences = []
        for agent_data in agent_outputs.values():
            if isinstance(agent_data, dict) and 'confidence' in agent_data:
                confidences.append(agent_data['confidence'])
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.5
        success_probability = min(0.95, avg_confidence * 1.2)
        
        return {
            "success_probability": round(success_probability, 2),
            "confidence_level": "high" if success_probability > 0.8 else "medium" if success_probability > 0.6 else "low",
            "key_factors": self._identify_success_factors(agent_outputs),
            "recommendations": self._generate_recommendations(success_probability, agent_outputs)
        }
    
    def predict_revenue_trend(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simple revenue trend prediction"""
        
        projections = financial_data.get("financial_projections", {})
        if not projections:
            return {"trend": "insufficient_data"}
        
        # Extract revenue values
        revenues = []
        for year_data in projections.values():
            if isinstance(year_data, dict) and "revenue" in year_data:
                revenues.append(year_data["revenue"])
        
        if len(revenues) < 2:
            return {"trend": "insufficient_data"}
        
        growth_rate = (revenues[-1] - revenues[0]) / revenues[0] if revenues[0] > 0 else 0
        
        return {
            "trend": "growing" if growth_rate > 0.2 else "stable" if growth_rate > -0.1 else "declining",
            "growth_rate": round(growth_rate * 100, 1),
            "next_year_prediction": int(revenues[-1] * (1 + growth_rate * 0.8)),
            "confidence": 0.75
        }
    
    def predict_market_timing(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict optimal market entry timing"""
        
        timing_score = 0.7  # Base score
        market_size = market_data.get("market_opportunity", "")
        
        if "billion" in str(market_size).lower():
            timing_score += 0.1
        
        return {
            "optimal_timing": "now" if timing_score > 0.8 else "soon" if timing_score > 0.6 else "wait",
            "timing_score": round(timing_score, 2),
            "recommended_actions": self._get_timing_actions(timing_score)
        }
    
    def _identify_success_factors(self, agent_outputs: Dict[str, Any]) -> List[str]:
        """Identify key success factors"""
        factors = []
        
        if agent_outputs.get("cofounder", {}).get("confidence", 0) > 0.8:
            factors.append("Strong vision clarity")
        if agent_outputs.get("product", {}).get("confidence", 0) > 0.8:
            factors.append("Well-defined product strategy")
        if agent_outputs.get("finance", {}).get("confidence", 0) > 0.8:
            factors.append("Solid financial planning")
        
        return factors or ["Foundation building in progress"]
    
    def _generate_recommendations(self, success_prob: float, agent_outputs: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        if success_prob < 0.6:
            recommendations.append("Focus on strengthening core strategy")
        if success_prob < 0.8:
            recommendations.append("Validate assumptions with market research")
        
        return recommendations or ["Continue current execution plan"]
    
    def _get_timing_actions(self, timing_score: float) -> List[str]:
        """Get timing-based action recommendations"""
        if timing_score > 0.8:
            return ["Accelerate go-to-market", "Secure funding", "Scale team"]
        elif timing_score > 0.6:
            return ["Complete MVP", "Validate market fit", "Prepare launch"]
        else:
            return ["Strengthen product", "Research market", "Build capabilities"]