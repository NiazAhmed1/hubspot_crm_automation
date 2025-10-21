"""
Autonomous HubSpot Agent - Fully automatic CRM management
No need for IDs - automatically finds and manages objects
"""
import json
import requests
from typing import Dict, Any, Optional, List


class AutonomousHubSpotAgent:
    """
    Fully autonomous HubSpot agent that:
    - Automatically finds objects before updating
    - Creates if not exists
    - Handles duplicates intelligently
    - Manages associations automatically
    """
    
    def __init__(self, api_key: str, base_url: str):
        """
        Initialize Autonomous HubSpot Agent
        
        Args:
            api_key: HubSpot Private App token (pat-na1-...)
            base_url: HubSpot API base URL
        """
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def smart_contact_operation(self, email: str, properties: Dict[str, Any], 
                                create_if_missing: bool = True) -> Dict[str, Any]:
        """
        Smart contact operation - automatically creates or updates
        
        Args:
            email: Contact email (unique identifier)
            properties: All properties to set (including email)
            create_if_missing: If True, creates contact if not found
            
        Returns:
            Dict with operation result
            
        Example:
            # Automatically creates or updates
            smart_contact_operation("john@test.com", {
                "email": "john@test.com",
                "firstname": "John",
                "lastname": "Doe",
                "phone": "555-1234",
                "jobtitle": "CEO"
            })
        """
        # Ensure email is in properties
        properties["email"] = email
        
        # Try to find existing contact
        search_result = self._find_contact_by_email(email)
        
        if search_result["found"]:
            # Contact exists - update it
            contact_id = search_result["contact_id"]
            return self._update_object("contacts", contact_id, properties, 
                                      operation_type="update_existing")
        else:
            # Contact doesn't exist
            if create_if_missing:
                # Create new contact
                return self._create_object("contacts", properties, 
                                          operation_type="create_new")
            else:
                return {
                    "status": "error",
                    "message": f"Contact with email {email} not found"
                }
    
    def smart_deal_operation(self, dealname: str, properties: Dict[str, Any],
                            contact_email: Optional[str] = None,
                            create_if_missing: bool = True) -> Dict[str, Any]:
        """
        Smart deal operation - automatically creates or updates
        Can auto-associate with contact by email
        
        Args:
            dealname: Deal name (used to find existing)
            properties: All deal properties
            contact_email: Optional contact email to associate
            create_if_missing: If True, creates deal if not found
            
        Returns:
            Dict with operation result
            
        Example:
            # Automatically creates or updates and associates
            smart_deal_operation("Big Sale", {
                "dealname": "Big Sale",
                "amount": "50000",
                "dealstage": "appointmentscheduled"
            }, contact_email="john@test.com")
        """
        # Ensure dealname is in properties
        properties["dealname"] = dealname
        
        # Try to find existing deal
        search_result = self._find_deal_by_name(dealname)
        
        if search_result["found"]:
            # Deal exists - update it
            deal_id = search_result["deal_id"]
            result = self._update_object("deals", deal_id, properties,
                                        operation_type="update_existing")
        else:
            # Deal doesn't exist
            if create_if_missing:
                result = self._create_object("deals", properties,
                                            operation_type="create_new")
                deal_id = result.get("object_id")
            else:
                return {
                    "status": "error",
                    "message": f"Deal '{dealname}' not found"
                }
        
        # Auto-associate with contact if provided
        if contact_email and result["status"] == "success":
            contact_result = self._find_contact_by_email(contact_email)
            if contact_result["found"]:
                self._auto_associate(
                    "deals", deal_id,
                    "contacts", contact_result["contact_id"]
                )
                result["associated_with_contact"] = contact_email
        
        return result
    
    def smart_company_operation(self, domain: str, properties: Dict[str, Any],
                               create_if_missing: bool = True) -> Dict[str, Any]:
        """
        Smart company operation - automatically creates or updates by domain
        
        Args:
            domain: Company domain (unique identifier)
            properties: All company properties
            create_if_missing: If True, creates if not found
            
        Returns:
            Dict with operation result
            
        Example:
            smart_company_operation("acme.com", {
                "domain": "acme.com",
                "name": "Acme Corp",
                "industry": "Technology"
            })
        """
        properties["domain"] = domain
        
        search_result = self._find_company_by_domain(domain)
        
        if search_result["found"]:
            company_id = search_result["company_id"]
            return self._update_object("companies", company_id, properties,
                                      operation_type="update_existing")
        else:
            if create_if_missing:
                return self._create_object("companies", properties,
                                          operation_type="create_new")
            else:
                return {
                    "status": "error",
                    "message": f"Company with domain {domain} not found"
                }
    
    def create_or_update_contact(self, email: str, **kwargs) -> Dict[str, Any]:
        """
        Simpler interface - create or update contact by email
        
        Example:
            create_or_update_contact(
                "john@test.com",
                firstname="John",
                lastname="Doe",
                phone="555-1234",
                jobtitle="CEO"
            )
        """
        properties = {"email": email, **kwargs}
        return self.smart_contact_operation(email, properties)
    
    def create_or_update_deal(self, dealname: str, contact_email: Optional[str] = None, 
                             **kwargs) -> Dict[str, Any]:
        """
        Simpler interface - create or update deal
        
        Example:
            create_or_update_deal(
                "Big Sale",
                contact_email="john@test.com",
                amount="50000",
                dealstage="appointmentscheduled"
            )
        """
        properties = {"dealname": dealname, **kwargs}
        return self.smart_deal_operation(dealname, properties, contact_email)
    
    def create_or_update_company(self, domain: str, **kwargs) -> Dict[str, Any]:
        """
        Simpler interface - create or update company
        
        Example:
            create_or_update_company(
                "acme.com",
                name="Acme Corp",
                industry="Technology"
            )
        """
        properties = {"domain": domain, **kwargs}
        return self.smart_company_operation(domain, properties)
    
    def link_contact_to_company(self, contact_email: str, company_domain: str,
                               create_missing: bool = True) -> Dict[str, Any]:
        """
        Automatically link contact to company by email and domain
        Creates objects if they don't exist
        
        Args:
            contact_email: Contact email
            company_domain: Company domain
            create_missing: Create objects if they don't exist
            
        Returns:
            Dict with result
        """
        # Find or create contact
        contact_result = self._find_contact_by_email(contact_email)
        if not contact_result["found"]:
            if create_missing:
                contact_create = self._create_object("contacts", {"email": contact_email})
                contact_id = contact_create.get("object_id")
            else:
                return {"status": "error", "message": "Contact not found"}
        else:
            contact_id = contact_result["contact_id"]
        
        # Find or create company
        company_result = self._find_company_by_domain(company_domain)
        if not company_result["found"]:
            if create_missing:
                company_create = self._create_object("companies", {"domain": company_domain})
                company_id = company_create.get("object_id")
            else:
                return {"status": "error", "message": "Company not found"}
        else:
            company_id = company_result["company_id"]
        
        # Create association
        return self._auto_associate("contacts", contact_id, "companies", company_id)
    
    # ========== INTERNAL HELPER METHODS ==========
    
    def _find_contact_by_email(self, email: str) -> Dict[str, Any]:
        """Find contact by email address"""
        try:
            url = f"{self.base_url}/crm/v3/objects/contacts/search"
            payload = {
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "email",
                        "operator": "EQ",
                        "value": email
                    }]
                }],
                "limit": 1
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            results = result.get("results", [])
            
            if results:
                return {
                    "found": True,
                    "contact_id": results[0]["id"],
                    "data": results[0]
                }
            else:
                return {"found": False}
                
        except Exception as e:
            return {"found": False, "error": str(e)}
    
    def _find_deal_by_name(self, dealname: str) -> Dict[str, Any]:
        """Find deal by name"""
        try:
            url = f"{self.base_url}/crm/v3/objects/deals/search"
            payload = {
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "dealname",
                        "operator": "EQ",
                        "value": dealname
                    }]
                }],
                "limit": 1
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            results = result.get("results", [])
            
            if results:
                return {
                    "found": True,
                    "deal_id": results[0]["id"],
                    "data": results[0]
                }
            else:
                return {"found": False}
                
        except Exception as e:
            return {"found": False, "error": str(e)}
    
    def _find_company_by_domain(self, domain: str) -> Dict[str, Any]:
        """Find company by domain"""
        try:
            url = f"{self.base_url}/crm/v3/objects/companies/search"
            payload = {
                "filterGroups": [{
                    "filters": [{
                        "propertyName": "domain",
                        "operator": "EQ",
                        "value": domain
                    }]
                }],
                "limit": 1
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            results = result.get("results", [])
            
            if results:
                return {
                    "found": True,
                    "company_id": results[0]["id"],
                    "data": results[0]
                }
            else:
                return {"found": False}
                
        except Exception as e:
            return {"found": False, "error": str(e)}
    
    def _create_object(self, object_type: str, properties: Dict[str, Any],
                      operation_type: str = "create") -> Dict[str, Any]:
        """Internal method to create any object"""
        try:
            url = f"{self.base_url}/crm/v3/objects/{object_type}"
            payload = {"properties": properties}
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return {
                "status": "success",
                "operation": operation_type,
                "object_type": object_type,
                "object_id": result.get("id"),
                "message": f"{object_type.capitalize()} created successfully",
                "data": result
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "object_type": object_type,
                "message": f"Failed to create {object_type}: {self._parse_error(e)}"
            }
    
    def _update_object(self, object_type: str, object_id: str,
                      properties: Dict[str, Any],
                      operation_type: str = "update") -> Dict[str, Any]:
        """Internal method to update any object"""
        try:
            url = f"{self.base_url}/crm/v3/objects/{object_type}/{object_id}"
            payload = {"properties": properties}
            
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return {
                "status": "success",
                "operation": operation_type,
                "object_type": object_type,
                "object_id": object_id,
                "message": f"{object_type.capitalize()} updated successfully",
                "data": result
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "object_type": object_type,
                "message": f"Failed to update {object_type}: {self._parse_error(e)}"
            }
    
    def _auto_associate(self, from_type: str, from_id: str,
                       to_type: str, to_id: str) -> Dict[str, Any]:
        """Internal method to create association"""
        try:
            # Try v4 API first (default associations)
            url = f"{self.base_url}/crm/v4/objects/{from_type}/{from_id}/associations/default/{to_type}/{to_id}"
            response = requests.put(url, headers=self.headers)
            
            if response.status_code == 404:
                # Fallback to v3 with association type
                association_types = {
                    ("deals", "contacts"): 3,
                    ("contacts", "companies"): 1,
                    ("deals", "companies"): 5
                }
                assoc_type = association_types.get((from_type, to_type), 1)
                url = f"{self.base_url}/crm/v3/objects/{from_type}/{from_id}/associations/{to_type}/{to_id}/{assoc_type}"
                response = requests.put(url, headers=self.headers)
            
            response.raise_for_status()
            
            return {
                "status": "success",
                "message": f"Associated {from_type}:{from_id} with {to_type}:{to_id}"
            }
            
        except Exception as e:
            return {
                "status": "warning",
                "message": f"Failed to create association: {str(e)}"
            }
    
    def _parse_error(self, exception: requests.exceptions.RequestException) -> str:
        """Parse error from API response"""
        try:
            if hasattr(exception, 'response') and exception.response is not None:
                error_data = exception.response.json()
                return error_data.get('message', str(exception))
            return str(exception)
        except:
            return str(exception)
    
    # ========== ADDITIONAL SMART OPERATIONS ==========
    
    def bulk_upsert_contacts(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Bulk create or update multiple contacts
        Automatically determines if each contact exists
        
        Args:
            contacts: List of contact dicts with 'email' and other properties
            
        Returns:
            Summary of operations
            
        Example:
            bulk_upsert_contacts([
                {"email": "john@test.com", "firstname": "John"},
                {"email": "jane@test.com", "firstname": "Jane"}
            ])
        """
        results = {
            "created": [],
            "updated": [],
            "failed": []
        }
        
        for contact in contacts:
            email = contact.get("email")
            if not email:
                results["failed"].append({"data": contact, "reason": "No email"})
                continue
            
            result = self.smart_contact_operation(email, contact)
            
            if result["status"] == "success":
                if result.get("operation") == "create_new":
                    results["created"].append(email)
                else:
                    results["updated"].append(email)
            else:
                results["failed"].append({"email": email, "reason": result.get("message")})
        
        return {
            "status": "success",
            "summary": f"Created: {len(results['created'])}, Updated: {len(results['updated'])}, Failed: {len(results['failed'])}",
            "details": results
        }
    
    def smart_search(self, object_type: str, search_term: str,
                    search_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Smart search across multiple fields
        
        Args:
            object_type: Type of object (contacts, deals, companies)
            search_term: Term to search for
            search_fields: Fields to search (auto-detected if None)
            
        Returns:
            Search results
        """
        if not search_fields:
            # Auto-detect fields based on object type
            field_map = {
                "contacts": ["email", "firstname", "lastname", "phone"],
                "deals": ["dealname", "amount"],
                "companies": ["name", "domain"]
            }
            search_fields = field_map.get(object_type, ["name"])
        
        filters = [
            {"propertyName": field, "operator": "CONTAINS_TOKEN", "value": search_term}
            for field in search_fields
        ]
        
        try:
            url = f"{self.base_url}/crm/v3/objects/{object_type}/search"
            payload = {
                "filterGroups": [{"filters": [f]} for f in filters],
                "limit": 20
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            results = result.get("results", [])
            
            return {
                "status": "success",
                "found": len(results) > 0,
                "count": len(results),
                "results": results
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Search failed: {str(e)}"
            }