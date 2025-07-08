from typing import Dict, Any, List
from agents.langgraph_base import LangGraphAgent
from datetime import datetime
from loguru import logger

class MoneyAgent(LangGraphAgent):
    """💰 Money Agent - Cash Flow, Payments, Fraud Detection"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "model": "deepseek/deepseek-chat:free",
            "temperature": 0.1,
            "expertise": ["cash flow analysis", "payment processing", "fraud detection", "financial monitoring"]
        }
        super().__init__("Money", "Financial Operations", memory_manager, approval_manager, personality)
    
    def _get_system_prompt(self) -> str:
        return """You are the Money Agent - a financial operations specialist. Your role is to:

1. CASH FLOW BOT: Monitor and forecast cash flow, track collections
2. PAYMENT BOT: Automate accounts payable, process invoices
3. FRAUD BOT: Monitor for anomalies and suspicious activities
4. FINANCIAL INTELLIGENCE: Real-time financial decision support

You are precise and security-focused. Prioritize accuracy and fraud prevention.

Structure your output as:
- Cash Flow Analysis (current position, forecasts, trends)
- Payment Processing (AP automation, approval workflows)
- Fraud Detection (anomalies, risk assessment, alerts)
- Financial Recommendations (optimization opportunities)"""
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute financial operations and monitoring"""
        task = state["task"]
        context = state["context"]
        
        task_type = task.get("type", "financial_analysis")
        
        if task_type == "cash_flow_monitoring":
            return await self._monitor_cash_flow(task, context)
        elif task_type == "payment_processing":
            return await self._process_payments(task, context)
        elif task_type == "fraud_detection":
            return await self._detect_fraud(task, context)
        else:
            return await self._analyze_financial_health(task, context)
    
    async def _monitor_cash_flow(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor and forecast cash flow"""
        financial_data = task.get("financial_data", {})
        
        cash_flow_prompt = f"""
        Analyze cash flow based on this financial data:
        
        Financial Data: {financial_data}
        Context: {context}
        
        Provide comprehensive cash flow analysis:
        1. Current Cash Position (available funds, commitments)
        2. Cash Flow Forecast (30/60/90 day projections)
        3. Collection Analysis (outstanding receivables, collection trends)
        4. Payment Obligations (upcoming payables, payment schedule)
        5. Seasonal Patterns (historical cash flow trends)
        6. Risk Assessment (cash flow risks, mitigation strategies)
        7. Optimization Recommendations (improve cash flow)
        """
        
        analysis = await self._think(cash_flow_prompt)
        return {"cash_flow_analysis": analysis, "task_type": "cash_flow_monitoring"}
    
    async def _process_payments(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process and automate payments"""
        payment_data = task.get("payment_data", {})
        
        payment_prompt = f"""
        Process these payment requests:
        
        Payment Data: {payment_data}
        Context: {context}
        
        For each payment, analyze:
        1. Document Verification (invoice accuracy, approval status)
        2. Vendor Validation (legitimate vendor, payment terms)
        3. Amount Verification (correct amounts, no duplicates)
        4. Approval Workflow (required approvals, authorization levels)
        5. Payment Method (optimal payment method, timing)
        6. Fraud Checks (suspicious patterns, validation required)
        7. Processing Recommendations (approve, reject, investigate)
        """
        
        processing = await self._think(payment_prompt)
        return {"payment_processing": processing, "task_type": "payment_processing"}
    
    async def _detect_fraud(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect fraudulent activities and anomalies"""
        transaction_data = task.get("transaction_data", {})
        
        fraud_prompt = f"""
        Analyze these transactions for fraud indicators:
        
        Transaction Data: {transaction_data}
        Context: {context}
        
        Fraud detection analysis:
        1. Anomaly Detection (unusual patterns, outliers)
        2. Transaction Validation (legitimate vs suspicious)
        3. Vendor Verification (known vs unknown vendors)
        4. Amount Analysis (unusual amounts, round numbers)
        5. Timing Patterns (off-hours, unusual frequency)
        6. Geographic Analysis (location-based anomalies)
        7. Risk Scoring (fraud probability, investigation priority)
        8. Alert Recommendations (immediate action required)
        """
        
        fraud_analysis = await self._think(fraud_prompt)
        return {"fraud_detection": fraud_analysis, "task_type": "fraud_detection"}
    
    async def _analyze_financial_health(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall financial health"""
        financial_metrics = task.get("financial_metrics", {})
        
        health_prompt = f"""
        Analyze financial health based on these metrics:
        
        Financial Metrics: {financial_metrics}
        Context: {context}
        
        Comprehensive financial health analysis:
        1. Liquidity Analysis (current ratio, quick ratio, cash position)
        2. Profitability Trends (revenue growth, margin analysis)
        3. Expense Management (cost control, spending patterns)
        4. Working Capital (inventory, receivables, payables)
        5. Debt Management (debt levels, payment capacity)
        6. Financial Ratios (key performance indicators)
        7. Risk Assessment (financial risks, mitigation strategies)
        8. Improvement Opportunities (optimization recommendations)
        """
        
        health_analysis = await self._think(health_prompt)
        return {"financial_health": health_analysis, "task_type": "financial_analysis"}
    
    def _calculate_fraud_score(self, transaction: Dict[str, Any]) -> float:
        """Calculate fraud risk score for transaction"""
        score = 0.0
        
        # Amount-based scoring
        amount = transaction.get("amount", 0)
        if amount > 10000:
            score += 0.3
        elif amount % 100 == 0:  # Round numbers
            score += 0.1
        
        # Vendor-based scoring
        vendor = transaction.get("vendor", "")
        if not vendor or len(vendor) < 3:
            score += 0.4
        
        # Timing-based scoring
        timestamp = transaction.get("timestamp", "")
        if "weekend" in timestamp.lower() or "night" in timestamp.lower():
            score += 0.2
        
        return min(1.0, score)
    
    def _generate_cash_flow_forecast(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate cash flow forecast based on historical data"""
        if not historical_data:
            return {"error": "No historical data available"}
        
        # Simple trend analysis
        recent_avg = sum(d.get("amount", 0) for d in historical_data[-3:]) / 3
        
        return {
            "30_day_forecast": recent_avg * 1.1,
            "60_day_forecast": recent_avg * 1.05,
            "90_day_forecast": recent_avg * 1.0,
            "confidence": 0.7,
            "trend": "stable"
        }