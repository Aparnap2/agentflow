from typing import Dict, Any, List
from agents.langgraph_base import LangGraphAgent
from datetime import datetime
from loguru import logger

class AssistantAgent(LangGraphAgent):
    """📧 Assistant Agent - Email Management, Calendar, Bookings"""
    
    def __init__(self, memory_manager, approval_manager):
        personality = {
            "model": "deepseek/deepseek-chat:free", 
            "temperature": 0.3,
            "expertise": ["email management", "calendar optimization", "travel booking", "task automation"]
        }
        super().__init__("Assistant", "Executive Assistant", memory_manager, approval_manager, personality)
    
    def _get_system_prompt(self) -> str:
        return """You are the Assistant Agent - an executive assistant specialist. Your role is to:

1. EMAIL SORTING: Summarize, respond to, and categorize messages
2. CALENDAR MANAGEMENT: Schedule optimization and meeting preparation  
3. BOOKINGS: Travel, dining, and appointment coordination
4. TASK AUTOMATION: Streamline repetitive administrative tasks

You are efficient and detail-oriented. Focus on time-saving and productivity.

Structure your output as:
- Email Summary (priority, actions needed)
- Calendar Optimization (scheduling recommendations)
- Booking Coordination (travel/meeting arrangements)
- Task Automation (workflow improvements)"""
    
    async def _execute_actions(self, state) -> Dict[str, Any]:
        """Execute assistant-specific administrative tasks"""
        task = state["task"]
        context = state["context"]
        
        task_type = task.get("type", "general_assistance")
        
        if task_type == "email_management":
            return await self._handle_email_management(task, context)
        elif task_type == "calendar_optimization":
            return await self._handle_calendar_management(task, context)
        elif task_type == "booking_coordination":
            return await self._handle_booking_coordination(task, context)
        else:
            return await self._handle_general_assistance(task, context)
    
    async def _handle_email_management(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle email sorting and management"""
        emails = task.get("emails", [])
        
        email_prompt = f"""
        I need to process and categorize these emails:
        
        Emails: {emails}
        Context: {context}
        
        For each email, provide:
        1. Priority Level (High/Medium/Low)
        2. Category (Financial/Project/Opportunity/Admin)
        3. Required Action (Reply/Forward/File/Schedule)
        4. Summary (key points)
        5. Suggested Response (if reply needed)
        
        Focus on revenue-generating activities and urgent matters.
        """
        
        analysis = await self._think(email_prompt)
        return {"email_analysis": analysis, "task_type": "email_management"}
    
    async def _handle_calendar_management(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle calendar optimization and scheduling"""
        calendar_data = task.get("calendar_data", {})
        
        calendar_prompt = f"""
        Optimize this calendar for maximum productivity:
        
        Calendar: {calendar_data}
        Context: {context}
        
        Provide:
        1. Schedule Optimization (time blocks, focus periods)
        2. Meeting Preparation (research, agendas, materials)
        3. Travel Time Buffers (realistic scheduling)
        4. Priority Rebalancing (revenue-focused activities)
        5. Conflict Resolution (overlapping commitments)
        """
        
        optimization = await self._think(calendar_prompt)
        return {"calendar_optimization": optimization, "task_type": "calendar_management"}
    
    async def _handle_booking_coordination(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle travel and booking coordination"""
        booking_request = task.get("booking_request", {})
        
        booking_prompt = f"""
        Coordinate this booking request:
        
        Request: {booking_request}
        Context: {context}
        
        Research and provide:
        1. Flight Options (times, prices, preferences)
        2. Hotel Recommendations (location, amenities, rates)
        3. Ground Transportation (airport transfers, local travel)
        4. Dining Reservations (business-appropriate venues)
        5. Meeting Venues (if business travel)
        6. Itinerary Summary (complete schedule)
        """
        
        coordination = await self._think(booking_prompt)
        return {"booking_coordination": coordination, "task_type": "booking_coordination"}
    
    async def _handle_general_assistance(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general administrative assistance"""
        assistance_prompt = f"""
        Provide executive assistance for:
        
        Task: {task}
        Context: {context}
        
        Analyze and provide:
        1. Task Prioritization (urgent vs important)
        2. Workflow Automation (repetitive task identification)
        3. Resource Allocation (time and attention optimization)
        4. Follow-up Actions (next steps and deadlines)
        5. Efficiency Improvements (process optimization)
        """
        
        assistance = await self._think(assistance_prompt)
        return {"general_assistance": assistance, "task_type": "general_assistance"}