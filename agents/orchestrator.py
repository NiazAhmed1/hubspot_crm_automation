
from typing import Dict, Any, List
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END
from agents.hubspot_agent import HubSpotAgent
from agents.email_agent import EmailAgent




class DynamicAgentState(TypedDict):
    """State shared across agents"""
    user_query: str
    intent: str
    operation: str
    object_type: str
    properties: Dict[str, Any]
    object_id: str
    filters: List[Dict[str, Any]]
    hubspot_result: Dict[str, Any]
    email_result: Dict[str, Any]
    final_response: str
    error: str


class DynamicGlobalOrchestrator:

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Dynamic Orchestrator with configuration
        
        Args:
            config: Configuration dictionary with API keys
        """
        self.config = config
        
        #Initialize LLM
        self.llm = ChatOpenAI(
            model=config["openai"]["model"],
            api_key=config["openai"]["api_key"],
        )
        


        
        # Initialize dynamic HubSpot agent
        self.hubspot_agent = HubSpotAgent(
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
        # Build workflow
        self.workflow = self._build_workflow()
    


    #design workflow
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(DynamicAgentState)
        
        workflow.add_node("understand_query", self._understand_query)
        workflow.add_node("execute_hubspot", self._execute_hubspot_operation)
        workflow.add_node("send_notification", self._send_email_notification)
        workflow.add_node("generate_response", self._generate_final_response)
        
        workflow.set_entry_point("understand_query")
        workflow.add_edge("understand_query", "execute_hubspot")
        workflow.add_edge("execute_hubspot", "send_notification")
        workflow.add_edge("send_notification", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    



    def _understand_query(self, state: DynamicAgentState) -> DynamicAgentState:
        """
        Understand ANY user query dynamically
        """
        try:
            query = state["user_query"]
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an AI assistant that understands HubSpot CRM queries.
                Extract the following from the user's query:
                
                1. **operation**: One of:
                   - create_object: Create new record
                   - update_object: Update existing record
                   - search_object: Search for records
                   - get_object: Get specific record by ID
                   - delete_object: Delete a record
                   - batch_create: Create multiple records
                   - batch_update: Update multiple records
                   - create_association: Link two objects
                   - get_properties: Get available properties for object type
                
                2. **object_type**: The HubSpot object (contacts, deals, companies, tickets, notes, tasks, etc.)
                
                3. **properties**: Dictionary of ALL properties mentioned (ANY field names)
                
                4. **object_id**: If updating/getting/deleting specific object
                
                5. **filters**: For search operations
                
                Return ONLY a valid JSON object. Be flexible with field names - use whatever the user mentions.
                
                Examples:
                
                Query: "Create a contact for John Doe with email john@example.com, phone 555-1234, job title CEO, and city New York"
                {{
                  "operation": "create_object",
                  "object_type": "contacts",
                  "properties": {{
                    "email": "john@example.com",
                    "firstname": "John",
                    "lastname": "Doe",
                    "phone": "555-1234",
                    "jobtitle": "CEO",
                    "city": "New York"
                  }}
                }}
                
                Query: "Update contact 12345 with phone 555-9999, job title VP Sales, and lead status qualified"
                {{
                  "operation": "update_object",
                  "object_type": "contacts",
                  "object_id": "12345",
                  "properties": {{
                    "phone": "555-9999",
                    "jobtitle": "VP Sales",
                    "hs_lead_status": "QUALIFIED"
                  }}
                }}
                
                Query: "Create a deal called Enterprise Sale for $100000 in qualified stage with priority high and deal type new business"
                {{
                  "operation": "create_object",
                  "object_type": "deals",
                  "properties": {{
                    "dealname": "Enterprise Sale",
                    "amount": "100000",
                    "dealstage": "qualifiedtobuy",
                    "priority": "high",
                    "deal_type": "newbusiness"
                  }}
                }}
                
                Query: "Create a company called Acme Corp with domain acme.com, industry Technology, and city San Francisco"
                {{
                  "operation": "create_object",
                  "object_type": "companies",
                  "properties": {{
                    "name": "Acme Corp",
                    "domain": "acme.com",
                    "industry": "Technology",
                    "city": "San Francisco"
                  }}
                }}
                
                Query: "Search for contacts with email containing @acme.com"
                {{
                  "operation": "search_object",
                  "object_type": "contacts",
                  "filters": [
                    {{"propertyName": "email", "operator": "CONTAINS", "value": "@acme.com"}}
                  ]
                }}
                
                Query: "Find deals with amount greater than 50000"
                {{
                  "operation": "search_object",
                  "object_type": "deals",
                  "filters": [
                    {{"propertyName": "amount", "operator": "GTE", "value": "50000"}}
                  ]
                }}
                
                Query: "Associate deal 123 with contact 456"
                {{
                  "operation": "create_association",
                  "from_object_type": "deals",
                  "from_object_id": "123",
                  "to_object_type": "contacts",
                  "to_object_id": "456"
                }}
                
                Query: "What properties are available for contacts"
                {{
                  "operation": "get_properties",
                  "object_type": "contacts"
                }}
                
                Be creative and extract ANY field the user mentions. HubSpot supports many properties.
                Common contact fields: email, firstname, lastname, phone, jobtitle, company, city, state, country, website, lifecyclestage, hs_lead_status
                Common deal fields: dealname, amount, dealstage, closedate, priority, deal_type, description
                Common company fields: name, domain, industry, city, state, country, phone, website
                """),
                ("user", "{query}")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({"query": query})
            
            # Parse response
            import json
            content = response.content.strip()
            
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:].strip()
            
            parsed = json.loads(content)
            
            state["operation"] = parsed.get("operation", "unknown")
            state["object_type"] = parsed.get("object_type", "")
            state["properties"] = parsed.get("properties", {})
            state["object_id"] = parsed.get("object_id", "")
            state["filters"] = parsed.get("filters", [])
            state["intent"] = f"User wants to {parsed.get('operation', 'unknown')} {parsed.get('object_type', '')}"
            
            # Handle association fields
            if state["operation"] == "create_association":
                state["from_object_type"] = parsed.get("from_object_type", "")
                state["from_object_id"] = parsed.get("from_object_id", "")
                state["to_object_type"] = parsed.get("to_object_type", "")
                state["to_object_id"] = parsed.get("to_object_id", "")
            
        except Exception as e:
            state["error"] = f"Failed to understand query: {str(e)}"
            state["operation"] = "error"
        
        return state
    
    
    
    
    
    def _execute_hubspot_operation(self, state: DynamicAgentState) -> DynamicAgentState:
        """
        Execute ANY HubSpot operation dynamically
        """
        try:
            operation = state["operation"]
            
            if operation == "create_object":
                result = self.hubspot_agent.create_object(
                    object_type=state["object_type"],
                    properties=state["properties"]
                )
            
            elif operation == "update_object":
                # Try to find object if email provided for contacts
                if state["object_type"] == "contacts" and not state["object_id"] and "email" in state["properties"]:
                    search_result = self.hubspot_agent.search_objects(
                        "contacts",
                        [{"propertyName": "email", "operator": "EQ", "value": state["properties"]["email"]}]
                    )
                    if search_result["found"] and search_result["count"] > 0:
                        state["object_id"] = search_result["results"][0]["id"]
                        # Remove email from properties to update
                        state["properties"].pop("email", None)
                
                if state["object_id"]:
                    result = self.hubspot_agent.update_object(
                        object_type=state["object_type"],
                        object_id=state["object_id"],
                        properties=state["properties"]
                    )
                else:
                    result = {"status": "error", "message": "Object ID required for update"}
            
            elif operation == "search_object":
                result = self.hubspot_agent.search_objects(
                    object_type=state["object_type"],
                    filters=state["filters"]
                )
            
            elif operation == "get_object":
                result = self.hubspot_agent.get_object(
                    object_type=state["object_type"],
                    object_id=state["object_id"]
                )
            
            elif operation == "delete_object":
                result = self.hubspot_agent.delete_object(
                    object_type=state["object_type"],
                    object_id=state["object_id"]
                )
            
            elif operation == "create_association":
                result = self.hubspot_agent.create_association(
                    from_object_type=state.get("from_object_type", ""),
                    from_object_id=state.get("from_object_id", ""),
                    to_object_type=state.get("to_object_type", ""),
                    to_object_id=state.get("to_object_id", "")
                )
            
            elif operation == "get_properties":
                result = self.hubspot_agent.get_properties(
                    object_type=state["object_type"]
                )
            
            else:
                result = {"status": "error", "message": f"Unknown operation: {operation}"}
            
            state["hubspot_result"] = result
            
        except Exception as e:
            state["hubspot_result"] = {
                "status": "error",
                "message": f"HubSpot operation failed: {str(e)}"
            }
        
        return state
    
    
    
    
    def _send_email_notification(self, state: DynamicAgentState) -> DynamicAgentState:
        """Send email notification"""
        try:
            operation = state["operation"]
            hubspot_result = state["hubspot_result"]
            
            if hubspot_result["status"] == "success":
                subject = f"✅ {operation.replace('_', ' ').title()}: {state['object_type']}"
                body = f"Operation completed successfully.<br><br>"
                body += f"<strong>Operation:</strong> {operation}<br>"
                body += f"<strong>Object Type:</strong> {state['object_type']}<br>"
                
                if "object_id" in hubspot_result:
                    body += f"<strong>Object ID:</strong> {hubspot_result['object_id']}<br>"
                
                if state.get("properties"):
                    body += f"<br><strong>Properties:</strong><br>"
                    for key, value in state["properties"].items():
                        body += f"• {key}: {value}<br>"
                
                email_result = self.email_agent.send_notification(
                    recipient=self.notification_email,
                    subject=subject,
                    body=body,
                    action_type=operation.replace('_', ' ').title()
                )
            else:
                email_result = self.email_agent.send_error_notification(
                    recipient=self.notification_email,
                    error_message=hubspot_result.get("message", "Unknown error"),
                    operation=f"{operation} on {state['object_type']}"
                )
            
            state["email_result"] = email_result
            
        except Exception as e:
            state["email_result"] = {
                "status": "error",
                "message": f"Email notification failed: {str(e)}"
            }
        
        return state
    
    
    
    
    def _generate_final_response(self, state: DynamicAgentState) -> DynamicAgentState:
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
        initial_state = DynamicAgentState(
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