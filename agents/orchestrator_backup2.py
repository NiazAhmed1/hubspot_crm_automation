"""
Autonomous Orchestrator - Handles operations without requiring IDs
Automatically finds objects and manages CRM intelligently
"""
from typing import Dict, Any
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from agents.hubspot_agent import AutonomousHubSpotAgent
from agents.email_agent import EmailAgent
import json
import re


class AutonomousState(TypedDict):
    """State for autonomous operations"""
    user_query: str
    intent: str
    operation: str
    identifier: str  # email, dealname, domain, etc.
    properties: Dict[str, Any]
    link_to: str  # For associations
    hubspot_result: Dict[str, Any]
    email_result: Dict[str, Any]
    final_response: str


class AutonomousOrchestrator:
    """
    Fully autonomous orchestrator that doesn't need object IDs
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize LLM
        # self.llm = ChatOpenAI(
        #     model=config["openai"]["model"],
        #     api_key=config["openai"]["api_key"],
        #     temperature=0
        # )

        from langchain_groq import ChatGroq
        
        self.llm = ChatGroq(
            model=config["openai"]["model"],
            api_key=config["openai"]["api_key"],
            temperature=0
        )
        # Initialize autonomous HubSpot agent
        self.hubspot_agent = AutonomousHubSpotAgent(
            api_key=config["hubspot"]["api_key"],
            base_url=config["hubspot"]["base_url"]
        )
        
        # Initialize email agent
        self.email_agent = EmailAgent(
            smtp_server=config["email"]["smtp_server"],
            smtp_port=config["email"]["smtp_port"],
            sender_email=config["email"]["sender_email"],
            sender_password=config["email"]["sender_password"]
        )
        
        self.notification_email = config["email"]["sender_email"]
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build autonomous workflow"""
        workflow = StateGraph(AutonomousState)
        
        workflow.add_node("understand_query", self._understand_query)
        workflow.add_node("execute_smart_operation", self._execute_smart_operation)
        workflow.add_node("send_notification", self._send_notification)
        workflow.add_node("generate_response", self._generate_final_response)
        
        workflow.set_entry_point("understand_query")
        workflow.add_edge("understand_query", "execute_smart_operation")
        workflow.add_edge("execute_smart_operation", "send_notification")
        workflow.add_edge("send_notification", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    def _understand_query(self, state: AutonomousState) -> AutonomousState:
        """
        Understand query and extract information WITHOUT requiring IDs
        """
        try:
            query = state["user_query"]
            
            # Extract email, dealname, domain using regex (fallback)
            email = self._extract_email(query)
            dealname = self._extract_dealname(query)
            domain = self._extract_domain(query)
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an AI that understands CRM queries WITHOUT requiring object IDs.
                Extract operation and properties. The system will automatically find objects.
                
                Return JSON with:
                {
                  "operation": "create_or_update_contact | create_or_update_deal | create_or_update_company | link_objects | search",
                  "identifier": "email or dealname or domain (the unique key)",
                  "properties": {"all fields mentioned"},
                  "link_to": "if linking, the other object identifier"
                }
                
                Examples:
                
                "Create or update contact john@test.com with name John Doe and phone 555-1234"
                {{
                  "operation": "create_or_update_contact",
                  "identifier": "john@test.com",
                  "properties": {{"email": "john@test.com", "firstname": "John", "lastname": "Doe", "phone": "555-1234"}}
                }}
                
                "Update deal Big Sale with amount 75000"
                {{
                  "operation": "create_or_update_deal",
                  "identifier": "Big Sale",
                  "properties": {{"dealname": "Big Sale", "amount": "75000"}}
                }}
                
                "Create deal Enterprise Sale for contact john@test.com amount 100000"
                {{
                  "operation": "create_or_update_deal",
                  "identifier": "Enterprise Sale",
                  "properties": {{"dealname": "Enterprise Sale", "amount": "100000"}},
                  "link_to": "john@test.com"
                }}
                
                "Link contact john@test.com to company acme.com"
                {{
                  "operation": "link_objects",
                  "identifier": "john@test.com",
                  "link_to": "acme.com"
                }}
                
                NO IDs needed! System finds objects automatically.
                """),
                ("user", "{query}")
            ])
            
            try:
                chain = prompt | self.llm
                response = chain.invoke({"query": query})
                
                content = response.content.strip()
                if "```" in content:
                    parts = content.split("```")
                    for part in parts:
                        if "{" in part and "}" in part:
                            content = part.replace("json", "").strip()
                            break
                
                parsed = json.loads(content)
                
                state["operation"] = parsed.get("operation", "unknown")
                state["identifier"] = parsed.get("identifier", email or dealname or domain)
                state["properties"] = parsed.get("properties", {})
                state["link_to"] = parsed.get("link_to", "")
                
            except Exception as e:
                print(f"⚠️ GPT parsing failed, using fallback: {e}")
                
                # Fallback parsing
                query_lower = query.lower()
                
                if "contact" in query_lower:
                    state["operation"] = "create_or_update_contact"
                    state["identifier"] = email
                    firstname, lastname = self._extract_name(query)
                    state["properties"] = {
                        "email": email,
                        "firstname": firstname,
                        "lastname": lastname
                    }
                elif "deal" in query_lower:
                    state["operation"] = "create_or_update_deal"
                    state["identifier"] = dealname
                    amount = self._extract_amount(query)
                    state["properties"] = {
                        "dealname": dealname,
                        "amount": amount
                    }
                elif "company" in query_lower:
                    state["operation"] = "create_or_update_company"
                    state["identifier"] = domain
                    state["properties"] = {"domain": domain}
                else:
                    state["operation"] = "unknown"
            
            state["intent"] = f"User wants to {state['operation']}"
            
        except Exception as e:
            state["operation"] = "error"
            state["error"] = f"Failed to understand: {str(e)}"
        
        return state
    
    def _execute_smart_operation(self, state: AutonomousState) -> AutonomousState:
        """
        Execute operation WITHOUT needing IDs - automatically finds objects
        """
        try:
            operation = state["operation"]
            identifier = state["identifier"]
            properties = state["properties"]
            link_to = state.get("link_to", "")
            
            if operation == "create_or_update_contact":
                result = self.hubspot_agent.create_or_update_contact(
                    identifier,
                    **properties
                )
            
            elif operation == "create_or_update_deal":
                # Extract contact email if mentioned
                contact_email = link_to if "@" in link_to else None
                result = self.hubspot_agent.create_or_update_deal(
                    identifier,
                    contact_email=contact_email,
                    **properties
                )
            
            elif operation == "create_or_update_company":
                result = self.hubspot_agent.create_or_update_company(
                    identifier,
                    **properties
                )
            
            elif operation == "link_objects":
                # Determine object types from identifiers
                if "@" in identifier and "." in link_to and "@" not in link_to:
                    # Contact to company
                    result = self.hubspot_agent.link_contact_to_company(
                        identifier, link_to
                    )
                else:
                    result = {
                        "status": "error",
                        "message": "Could not determine object types for linking"
                    }
            
            else:
                result = {
                    "status": "error",
                    "message": f"Unknown operation: {operation}"
                }
            
            state["hubspot_result"] = result
            
        except Exception as e:
            state["hubspot_result"] = {
                "status": "error",
                "message": f"Operation failed: {str(e)}"
            }
        
        return state
    
    def _send_notification(self, state: AutonomousState) -> AutonomousState:
        """Send email notification"""
        try:
            result = state["hubspot_result"]
            
            if result["status"] == "success":
                operation_type = result.get("operation", state["operation"])
                object_type = result.get("object_type", "object")
                
                subject = f"✅ CRM Operation: {operation_type.replace('_', ' ').title()}"
                body = f"""
                <strong>Operation completed successfully!</strong><br><br>
                
                <strong>Type:</strong> {object_type}<br>
                <strong>Identifier:</strong> {state.get('identifier', 'N/A')}<br>
                <strong>Operation:</strong> {operation_type}<br>
                """
                
                if "object_id" in result:
                    body += f"<strong>Object ID:</strong> {result['object_id']}<br>"
                
                if state.get("properties"):
                    body += "<br><strong>Properties:</strong><br>"
                    for key, value in state["properties"].items():
                        body += f"• {key}: {value}<br>"
                
                email_result = self.email_agent.send_notification(
                    recipient=self.notification_email,
                    subject=subject,
                    body=body,
                    action_type="Autonomous CRM Operation"
                )
            else:
                email_result = self.email_agent.send_error_notification(
                    recipient=self.notification_email,
                    error_message=result.get("message", "Unknown error"),
                    operation=state["operation"]
                )
            
            state["email_result"] = email_result
            
        except Exception as e:
            state["email_result"] = {
                "status": "error",
                "message": f"Email failed: {str(e)}"
            }



    def _generate_final_response(self, state: AutonomousState) -> AutonomousState:
        """Generate final response"""
        hubspot_result = state["hubspot_result"]
        email_result = state["email_result"]
        
        if hubspot_result["status"] == "success":
            response = f"✅ {hubspot_result.get('message', 'Operation completed successfully')}\n"
            
            # Add specific details based on operation
            if state["operation"] == "search_object" and "count" in hubspot_result:
                response += f"📊 Found {hubspot_result['count']} results\n"
                if hubspot_result.get("results"):
                    response += "\nFirst result:\n"
                    first = hubspot_result["results"][0]
                    response += f"  ID: {first.get('id')}\n"
                    if "properties" in first:
                        for key, value in list(first["properties"].items())[:5]:
                            response += f"  {key}: {value}\n"
            
            elif state["operation"] == "get_properties" and "count" in hubspot_result:
                response += f"📋 Found {hubspot_result['count']} available properties\n"
                if "all_property_names" in hubspot_result:
                    response += f"\nSome examples: {', '.join(hubspot_result['all_property_names'][:10])}"
            
            elif "object_id" in hubspot_result:
                response += f"🆔 Object ID: {hubspot_result['object_id']}\n"
            
            if email_result.get("status") == "success":
                response += "📧 Notification email sent successfully."
            else:
                response += f"⚠️ Note: Email notification failed - {email_result.get('message', '')}"
        else:
            response = f"❌ Operation failed: {hubspot_result.get('message', 'Unknown error')}"
        
        state["final_response"] = response
        return state
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process ANY user query dynamically
        """
        initial_state = AutonomousState(
            user_query=user_query,
            intent="",
            operation="",
            object_type="",
            properties={},
            object_id="",
            filters=[],
            hubspot_result={},
            email_result={},
            final_response="",
            error=""
        )
        
        final_state = self.workflow.invoke(initial_state)
        
        return {
            "query": user_query,
            "operation": final_state["operation"],
            "object_type": final_state.get("object_type", ""),
            "properties": final_state.get("properties", {}),
            "hubspot_result": final_state["hubspot_result"],
            "email_result": final_state["email_result"],
            "response": final_state["final_response"]
        }