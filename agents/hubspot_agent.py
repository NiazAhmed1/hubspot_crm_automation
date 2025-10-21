
import json
import requests
from typing import Dict, Any, Optional, List


class HubSpotAgent:

    def __init__(self, api_key: str, base_url: str):
        """
        Initialize HubSpot Agent with API credentials
        """

        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    





    def create_object(self, object_type: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create ANY HubSpot object with ANY properties (fully dynamic)
        
        Args:
            object_type: Type of object (contacts, deals, companies, tickets, etc.)
            properties: Dictionary of ANY properties to set
            
        Returns:
            Dict containing creation result
            
        Example:
            # Create contact with any fields
            create_object("contacts", {
                "email": "john@example.com",
                "firstname": "John",
                "lastname": "Doe",
                "phone": "555-1234",
                "jobtitle": "CEO",
                "city": "New York",
                "state": "NY",
                "country": "USA",
                "website": "example.com",
                "lifecyclestage": "lead",
                "hs_lead_status": "NEW",
                "custom_field_1": "value1"  # Even custom properties!
            })
            
            # Create deal with any fields
            create_object("deals", {
                "dealname": "Big Sale",
                "amount": "50000",
                "dealstage": "appointmentscheduled",
                "closedate": "2025-12-31",
                "deal_type": "newbusiness",
                "description": "Important deal",
                "priority": "high"
            })
            
            # Create company
            create_object("companies", {
                "name": "Acme Corp",
                "domain": "acme.com",
                "industry": "Technology",
                "city": "San Francisco"
            })
        """
        try:
            url = f"{self.base_url}/crm/v3/objects/{object_type}"
            payload = {"properties": properties}
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return {
                "status": "success",
                "object_type": object_type,
                "object_id": result.get("id"),
                "message": f"{object_type.capitalize()} created successfully",
                "data": result
            }
            
        except requests.exceptions.RequestException as e:
            error_detail = self._parse_error(e)
            return {
                "status": "error",
                "object_type": object_type,
                "message": f"Failed to create {object_type}: {error_detail}"
            }
    
    


    
    
    
    def update_object(self, object_type: str, object_id: str, 
                     properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update ANY HubSpot object with ANY properties (fully dynamic)
        
        Args:
            object_type: Type of object (contacts, deals, companies, etc.)
            object_id: HubSpot object ID
            properties: Dictionary of ANY properties to update
            
        Returns:
            Dict containing update result
            
        Example:
            # Update contact with any fields
            update_object("contacts", "12345", {
                "phone": "555-9999",
                "jobtitle": "VP of Sales",
                "hs_lead_status": "QUALIFIED",
                "custom_property": "new value"
            })
        """
        try:
            url = f"{self.base_url}/crm/v3/objects/{object_type}/{object_id}"
            payload = {"properties": properties}
            
            response = requests.patch(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return {
                "status": "success",
                "object_type": object_type,
                "object_id": object_id,
                "message": f"{object_type.capitalize()} updated successfully",
                "data": result
            }
            
        except requests.exceptions.RequestException as e:
            error_detail = self._parse_error(e)
            return {
                "status": "error",
                "object_type": object_type,
                "message": f"Failed to update {object_type}: {error_detail}"
            }
    
    
    
    




    
    def search_objects(self, object_type: str, 
                      filters: List[Dict[str, Any]],
                      properties: Optional[List[str]] = None,
                      limit: int = 10) -> Dict[str, Any]:
        """
        Search for ANY objects with ANY filters (fully dynamic)
        
        Args:
            object_type: Type of object to search
            filters: List of filter conditions
            properties: List of properties to return (None = all)
            limit: Maximum results to return
            
        Returns:
            Dict containing search results
            
        Example:
            # Search contacts by email
            search_objects("contacts", [
                {"propertyName": "email", "operator": "EQ", "value": "john@example.com"}
            ])
            
            # Search deals by amount range
            search_objects("deals", [
                {"propertyName": "amount", "operator": "GTE", "value": "10000"},
                {"propertyName": "amount", "operator": "LTE", "value": "50000"}
            ])
            
            # Search companies by domain
            search_objects("companies", [
                {"propertyName": "domain", "operator": "CONTAINS", "value": "acme"}
            ])
        """
        try:
            url = f"{self.base_url}/crm/v3/objects/{object_type}/search"
            payload = {
                "filterGroups": [{"filters": filters}],
                "limit": limit
            }
            
            if properties:
                payload["properties"] = properties
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            results = result.get("results", [])
            
            return {
                "status": "success",
                "object_type": object_type,
                "found": len(results) > 0,
                "count": len(results),
                "results": results,
                "message": f"Found {len(results)} {object_type}"
            }
                
        except requests.exceptions.RequestException as e:
            error_detail = self._parse_error(e)
            return {
                "status": "error",
                "object_type": object_type,
                "message": f"Failed to search {object_type}: {error_detail}"
            }
    
    
    
    
    
    
    def get_object(self, object_type: str, object_id: str,
                   properties: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get a specific object by ID with any properties
        
        Args:
            object_type: Type of object
            object_id: Object ID
            properties: List of properties to retrieve (None = all)
            
        Returns:
            Dict containing object data
        """
        try:
            url = f"{self.base_url}/crm/v3/objects/{object_type}/{object_id}"
            
            if properties:
                url += "?properties=" + ",".join(properties)
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            return {
                "status": "success",
                "object_type": object_type,
                "object_id": object_id,
                "data": result
            }
            
        except requests.exceptions.RequestException as e:
            error_detail = self._parse_error(e)
            return {
                "status": "error",
                "message": f"Failed to get {object_type}: {error_detail}"
            }
    
    
    
    
    
    
    def delete_object(self, object_type: str, object_id: str) -> Dict[str, Any]:
        """
        Delete any object
        
        Args:
            object_type: Type of object
            object_id: Object ID to delete
            
        Returns:
            Dict containing deletion result
        """
        try:
            url = f"{self.base_url}/crm/v3/objects/{object_type}/{object_id}"
            response = requests.delete(url, headers=self.headers)
            response.raise_for_status()
            
            return {
                "status": "success",
                "object_type": object_type,
                "object_id": object_id,
                "message": f"{object_type.capitalize()} deleted successfully"
            }
            
        except requests.exceptions.RequestException as e:
            error_detail = self._parse_error(e)
            return {
                "status": "error",
                "message": f"Failed to delete {object_type}: {error_detail}"
            }
    
    
    
    
    
    def create_association(self, from_object_type: str, from_object_id: str,
                          to_object_type: str, to_object_id: str,
                          association_type_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Create association between ANY two objects
        
        Args:
            from_object_type: Source object type
            from_object_id: Source object ID
            to_object_type: Target object type
            to_object_id: Target object ID
            association_type_id: Association type (optional, HubSpot will infer)
            
        Returns:
            Dict containing result
            
        Example:
            # Associate deal with contact
            create_association("deals", "123", "contacts", "456")
            
            # Associate company with contact
            create_association("companies", "789", "contacts", "456")
        """
        try:
            if association_type_id:
                url = f"{self.base_url}/crm/v3/objects/{from_object_type}/{from_object_id}/associations/{to_object_type}/{to_object_id}/{association_type_id}"
            else:
                url = f"{self.base_url}/crm/v4/objects/{from_object_type}/{from_object_id}/associations/default/{to_object_type}/{to_object_id}"
            
            response = requests.put(url, headers=self.headers)
            response.raise_for_status()
            
            return {
                "status": "success",
                "message": f"Associated {from_object_type}:{from_object_id} with {to_object_type}:{to_object_id}"
            }
            
        except requests.exceptions.RequestException as e:
            error_detail = self._parse_error(e)
            return {
                "status": "error",
                "message": f"Failed to create association: {error_detail}"
            }
    
    
    
    
    def get_properties(self, object_type: str) -> Dict[str, Any]:
        """
        Get ALL available properties for an object type
        This allows the system to know what fields are available
        
        Args:
            object_type: Type of object
            
        Returns:
            Dict containing all available properties
        """
        try:
            url = f"{self.base_url}/crm/v3/properties/{object_type}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            result = response.json()
            properties = result.get("results", [])
            
            # Create a simple map of property names and types
            property_map = {
                prop["name"]: {
                    "label": prop.get("label"),
                    "type": prop.get("type"),
                    "fieldType": prop.get("fieldType"),
                    "description": prop.get("description")
                }
                for prop in properties
            }
            
            return {
                "status": "success",
                "object_type": object_type,
                "count": len(properties),
                "properties": property_map,
                "all_property_names": list(property_map.keys())
            }
            
        except requests.exceptions.RequestException as e:
            error_detail = self._parse_error(e)
            return {
                "status": "error",
                "message": f"Failed to get properties: {error_detail}"
            }
    
    
    
    
    
    def batch_create(self, object_type: str, 
                    objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create multiple objects in a single batch request
        
        Args:
            object_type: Type of objects to create
            objects: List of objects with their properties
            
        Returns:
            Dict containing batch creation results
            
        Example:
            batch_create("contacts", [
                {"email": "john@example.com", "firstname": "John"},
                {"email": "jane@example.com", "firstname": "Jane"}
            ])
        """
        try:
            url = f"{self.base_url}/crm/v3/objects/{object_type}/batch/create"
            payload = {
                "inputs": [{"properties": obj} for obj in objects]
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return {
                "status": "success",
                "object_type": object_type,
                "created_count": len(result.get("results", [])),
                "message": f"Created {len(result.get('results', []))} {object_type}",
                "data": result
            }
            
        except requests.exceptions.RequestException as e:
            error_detail = self._parse_error(e)
            return {
                "status": "error",
                "message": f"Failed batch create: {error_detail}"
            }
    
    
    
    
    def batch_update(self, object_type: str,
                    updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Update multiple objects in a single batch request
        
        Args:
            object_type: Type of objects to update
            updates: List of dicts with 'id' and 'properties'
            
        Returns:
            Dict containing batch update results
            
        Example:
            batch_update("contacts", [
                {"id": "123", "properties": {"phone": "555-1234"}},
                {"id": "456", "properties": {"phone": "555-5678"}}
            ])
        """
        try:
            url = f"{self.base_url}/crm/v3/objects/{object_type}/batch/update"
            payload = {"inputs": updates}
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return {
                "status": "success",
                "object_type": object_type,
                "updated_count": len(result.get("results", [])),
                "message": f"Updated {len(result.get('results', []))} {object_type}",
                "data": result
            }
            
        except requests.exceptions.RequestException as e:
            error_detail = self._parse_error(e)
            return {
                "status": "error",
                "message": f"Failed batch update: {error_detail}"
            }
    
    
    
    
    
    def _parse_error(self, exception: requests.exceptions.RequestException) -> str:
        """
        Parse error from HubSpot API response
        
        Args:
            exception: Request exception
            
        Returns:
            Human-readable error message
        """
        try:
            if hasattr(exception, 'response') and exception.response is not None:
                error_data = exception.response.json()
                return error_data.get('message', str(exception))
            return str(exception)
        except:
            return str(exception)