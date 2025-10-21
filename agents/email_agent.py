"""
Email Agent - Handles email notifications
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List


class EmailAgent:
    def __init__(self, smtp_server: str, smtp_port: int, 
                 sender_email: str, sender_password: str):
        """
        Initialize Email Agent with SMTP credentials
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            sender_email: Sender email address
            sender_password: Sender email password/app password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
    
    def send_notification(self, recipient: str, subject: str, 
                         body: str, action_type: str = "CRM Operation") -> Dict[str, Any]:
        """
        Send email notification
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            body: Email body content
            action_type: Type of action performed
            
        Returns:
            Dict containing email sending result
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.sender_email
            message["To"] = recipient
            
            # Create HTML body
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <h2 style="color: #2c3e50;">🔔 {action_type} Notification</h2>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="color: #34495e; line-height: 1.6;">{body}</p>
                    </div>
                    <hr style="border: 1px solid #ecf0f1; margin: 20px 0;">
                    <p style="color: #7f8c8d; font-size: 12px;">
                        This is an automated notification from your CRM Agent System.
                    </p>
                </body>
            </html>
            """
            
            # Attach HTML body
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(message)
            
            return {
                "status": "success",
                "message": f"Email notification sent to {recipient}",
                "recipient": recipient,
                "subject": subject
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to send email: {str(e)}"
            }
    
    def send_contact_creation_notification(self, recipient: str, 
                                          contact_name: str, 
                                          contact_email: str,
                                          contact_id: str) -> Dict[str, Any]:
        """
        Send notification for contact creation
        
        Args:
            recipient: Email recipient
            contact_name: Name of created contact
            contact_email: Email of created contact
            contact_id: HubSpot contact ID
            
        Returns:
            Dict containing result
        """
        subject = f"✅ New Contact Created: {contact_name}"
        body = f"""
        A new contact has been successfully created in HubSpot CRM.
        
        <strong>Contact Details:</strong><br>
        • Name: {contact_name}<br>
        • Email: {contact_email}<br>
        • Contact ID: {contact_id}<br>
        
        The contact is now available in your HubSpot CRM dashboard.
        """
        
        return self.send_notification(recipient, subject, body, "Contact Creation")
    
    def send_contact_update_notification(self, recipient: str,
                                        contact_id: str,
                                        updated_fields: List[str]) -> Dict[str, Any]:
        """
        Send notification for contact update
        
        Args:
            recipient: Email recipient
            contact_id: HubSpot contact ID
            updated_fields: List of updated field names
            
        Returns:
            Dict containing result
        """
        subject = f"🔄 Contact Updated: {contact_id}"
        fields_list = "<br>".join([f"• {field}" for field in updated_fields])
        body = f"""
        A contact has been successfully updated in HubSpot CRM.
        
        <strong>Update Details:</strong><br>
        • Contact ID: {contact_id}<br>
        
        <strong>Updated Fields:</strong><br>
        {fields_list}
        
        The changes are now reflected in your HubSpot CRM.
        """
        
        return self.send_notification(recipient, subject, body, "Contact Update")
    
    def send_deal_creation_notification(self, recipient: str,
                                       deal_name: str,
                                       deal_amount: float,
                                       deal_id: str) -> Dict[str, Any]:
        """
        Send notification for deal creation
        
        Args:
            recipient: Email recipient
            deal_name: Name of the deal
            deal_amount: Deal amount
            deal_id: HubSpot deal ID
            
        Returns:
            Dict containing result
        """
        subject = f"💰 New Deal Created: {deal_name}"
        body = f"""
        A new deal has been successfully created in HubSpot CRM.
        
        <strong>Deal Details:</strong><br>
        • Deal Name: {deal_name}<br>
        • Amount: ${deal_amount:,.2f}<br>
        • Deal ID: {deal_id}<br>
        
        The deal is now available in your HubSpot pipeline.
        """
        
        return self.send_notification(recipient, subject, body, "Deal Creation")
    
    def send_deal_update_notification(self, recipient: str,
                                     deal_id: str,
                                     updated_fields: List[str]) -> Dict[str, Any]:
        """
        Send notification for deal update
        
        Args:
            recipient: Email recipient
            deal_id: HubSpot deal ID
            updated_fields: List of updated field names
            
        Returns:
            Dict containing result
        """
        subject = f"🔄 Deal Updated: {deal_id}"
        fields_list = "<br>".join([f"• {field}" for field in updated_fields])
        body = f"""
        A deal has been successfully updated in HubSpot CRM.
        
        <strong>Update Details:</strong><br>
        • Deal ID: {deal_id}<br>
        
        <strong>Updated Fields:</strong><br>
        {fields_list}
        
        The changes are now reflected in your HubSpot pipeline.
        """
        
        return self.send_notification(recipient, subject, body, "Deal Update")
    
    def send_error_notification(self, recipient: str, 
                               error_message: str,
                               operation: str) -> Dict[str, Any]:
        """
        Send notification for errors
        
        Args:
            recipient: Email recipient
            error_message: Error description
            operation: Operation that failed
            
        Returns:
            Dict containing result
        """
        subject = f"⚠️ CRM Operation Failed: {operation}"
        body = f"""
        An error occurred while performing a CRM operation.
        
        <strong>Operation:</strong> {operation}<br>
        
        <strong>Error Details:</strong><br>
        <div style="background-color: #ffe6e6; padding: 10px; border-radius: 3px;">
            {error_message}
        </div>
        
        Please check your configuration and try again.
        """
        
        return self.send_notification(recipient, subject, body, "Error Alert")