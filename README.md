# Multi-Agent HubSpot CRM Automation

This project implements an intelligent Multi-Agent CRM Automation System integrated with HubSpot and OpenAI, enabling automated creation, updating, and management of contacts, companies, and deals using natural language queries.

## Prerequisites

- Python 3.8+ installed
- Internet connection
- HubSpot account
- OpenAI API key
- Gmail account with App Password enabled




## Project Setup

## Step 1: Clone the Repository

```bash
git clone https://github.com/NiazAhmed1/hubspot_crm_automation.git
cd Email_MCP
```


Your structure should look like:
```
multi-agent-crm-system/
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py
│   ├── hubspot_agent.py
│   └── email_agent.py
├── main.py
├── config.json
├── requirements.txt
├── README.md
└── .gitignore
```


#### 1.2 Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

```

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Wait for installation to complete. You should see:
```
Successfully installed langchain-... langgraph-... langchain-openai-...
```



## Step 3: Get API Keys

### 3.1 OpenAI API Key

1. Go to https://platform.openai.com/
2. Sign up or log in
3. Click on your profile → "View API Keys"
4. Click "Create new secret key"
5. Name it "CRM Agent"
6. **Copy the key immediately** (you won't see it again!)
7. Example format: `sk-proj-xxxxxxxxxxxxxxxxxxxxx`


### 3.2 HubSpot API Key

#### Create HubSpot Account
1. Go to https://www.hubspot.com/
2. Click "Get started free"
3. Complete registration
4. Skip the onboarding wizard (click "Skip for now")

#### Create Private App
1. In HubSpot, click the ⚙️ settings icon (top right)
2. Navigate to: **Integrations** → **Private Apps** or **Lagacy Apps** 
3. Click **"Create a private app"**
4. Fill in:
   - **Name**: CRM Agent
   - **Description**: Multi-agent AI system
5. Go to **"Scopes"** tab
6. Enable these scopes:
   - Under **CRM**:
     - `crm.objects.contacts.read`
     - `crm.objects.contacts.write`
     - `crm.objects.deals.read`
     - `crm.objects.deals.write`
     - `crm.objects.companies.write`
     - `crm.objects.companies.read`
     - `crm.schemas.contacts.read`
     - `crm.schemas.contacts.write`
     - `crm.schemas.deals.read`
     - `crm.schemas.deals.write`
     - `crm.schemas.companies.write`
     - `crm.schemas.companies.read`

        
7. Click **"Create app"**
8. Click **"Show token"** and copy it
9. Example format: `pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### 3.3 Gmail App Password

#### Enable 2-Factor Authentication
1. Go to https://myaccount.google.com/security
2. Scroll to "2-Step Verification"
3. Click "Get Started" and follow setup

#### Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select app: **Mail**
3. Select device: **Other (Custom name)**
4. Enter: **CRM Agent**
5. Click **"Generate"**
6. Copy the 16-character password (no spaces)
7. Example format: `abcd efgh ijkl mnop` → use as `abcdefghijklmnop`





## Step 4: Configure the Application (5 minutes)

### 4.1 Create config.json

Create `config.json` in the project root with this structure:

```json
{
  "openai": {
    "api_key": "YOUR_OPENAI_API_KEY_HERE",
    "model": "gpt-4"
  },
  "hubspot": {
    "api_key": "YOUR_HUBSPOT_API_KEY_HERE",
    "base_url": "https://api.hubapi.com"
  },
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "YOUR_EMAIL@gmail.com",
    "sender_password": "YOUR_APP_PASSWORD_HERE"
  }
}
```

### 4.2 Replace placeholders

Replace these values:
- `YOUR_OPENAI_API_KEY_HERE` → Your OpenAI key
- `YOUR_HUBSPOT_API_KEY_HERE` → Your HubSpot token
- `YOUR_EMAIL@gmail.com` → Your Gmail address
- `YOUR_APP_PASSWORD_HERE` → Your Gmail app password 




## Stp 5: Run Full System Test

```bash
python main.py
```

You should see:
```
============================================================
🤖 Multi-Agent CRM System
============================================================

📋 Loading configuration...
✅ Configuration loaded successfully

🔧 Initializing agents...
✅ Agents initialized successfully

============================================================
System Ready! Enter your CRM queries below.
Type 'exit' or 'quit' to stop the application.
============================================================
```




## 🎮 Step 6: Run Your First Query (5 minutes)

### 6.1 Create a Contact

At the prompt, enter:
```
Create a contact for Test User with email testuser@example.com
```

Expected flow:
1. System processes query
2. Creates contact in HubSpot
3. Sends email notification
4. Shows success message

### 6.2 Verify in HubSpot

1. Go to your HubSpot account
2. Click **Contacts** in the left menu
3. You should see "Test User" in the list!

### 6.3 Check Your Email

You should receive an email with:
- Subject: "✅ New Contact Created: Test User"
- Contact details
- Contact ID




## Step 7: Understanding the Code (15 minutes)

### 7.1 System Flow

```
User Input
    ↓
main.py (Entry Point)
    ↓
GlobalOrchestrator (Brain)
    ↓
├── Understand Query (LLM)
├── Execute HubSpot Operation
├── Send Email Notification
└── Generate Response
```

### 7.2 Key Components

**1. Global Orchestrator (agents/orchestrator.py)**
- Uses LangGraph to create a workflow
- Coordinates between agents
- Uses OpenAI to understand queries
- Extracts intent and parameters

**2. HubSpot Agent (agents/hubspot_agent.py)**
- Interacts with HubSpot API
- Methods: create_contact, update_contact, create_deal, update_deal
- Handles API errors gracefully

**3. Email Agent (agents/email_agent.py)**
- Sends SMTP emails
- Templates for different notification types
- HTML formatting for better presentation

**4. Main Application (main.py)**
- Loads configuration
- Interactive CLI
- Error handling

### 7.3 LangGraph Workflow

The workflow in `orchestrator.py` defines:

```python
workflow.add_node("understand_query", self._understand_query)
workflow.add_node("execute_hubspot", self._execute_hubspot_operation)
workflow.add_node("send_notification", self._send_email_notification)
workflow.add_node("generate_response", self._generate_final_response)

# Flow: understand → execute → notify → respond
workflow.set_entry_point("understand_query")
workflow.add_edge("understand_query", "execute_hubspot")
workflow.add_edge("execute_hubspot", "send_notification")
workflow.add_edge("send_notification", "generate_response")
workflow.add_edge("generate_response", END)
```

Each node processes the state and passes it to the next node.

---






## Step 8: Common Operations & Examples

### 8.1 Contact Operations

**Create Contact (Basic):**
```
Create a contact for John Smith with email john.smith@company.com
```

**Create Contact (Full Details):**
```
Create a contact for Sarah Johnson with email sarah@tech.com phone 555-0123 and company TechCorp
```


**get Contact:**
```
List all contact
```

**get Contact along with object id:**
```
List contact having firstname is ciris
```


**Update Contact:**
```
Update contact 234567 with email john.smith@company.com with phone 555-9876
```


### 8.2 Deal Operations

**Create Deal (Basic):**
```
Create a deal called Enterprise Sale for $50000 in appointmentscheduled stage
```

**Create Deal (With Close Date):**
```
Create a deal called Q4 Contract for $75000 in qualifiedtobuy stage with closedate 2025-12-31
```

**get Contact along with object id:**
```
show deal having name is gt932
```

**Update Deal:**
```
Update deal 12345678 with amount 85000
```

**Update Deal Stage:**
```
Update deal 12345678 with dealstage closedwon
```





## Step 9: Troubleshooting Common Issues (15 minutes)

### Issue 1: "Configuration file not found"

**Error:**
```
❌ Error: Configuration file 'config.json' not found.
```

**Solution:**
```bash
# Check if file exists
ls config.json

# If not, create it
config.json
# Then add your configuration
```

### Issue 2: HubSpot 401 Unauthorized

**Error:**
```
Failed to create contact: 401 Client Error: Unauthorized
```

**Solutions:**

1. **Check API Key Format:**
```python
# Key should start with 'pat-'
# Example: pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

2. **Verify Scopes:**
   - Go to HubSpot → Settings → Private Apps
   - Click your app
   - Check "Scopes" tab
   - Ensure all CRM scopes are enabled

3. **Regenerate Key:**
   - In Private Apps, click "Regenerate token"
   - Update config.json with new token

### Issue 3: Email Sending Failed

**Error:**
```
Failed to send email: (535, b'5.7.8 Username and Password not accepted')
```

**Solutions:**

1. **Use App Password (Not Regular Password):**
```json
{
  "email": {
    "sender_password": "abcdefghijklmnop"  
  }
}
```

2. **Enable 2FA:**
   - Gmail requires 2FA for app passwords
   - Go to: https://myaccount.google.com/security
   - Enable "2-Step Verification"

3. **Check SMTP Settings:**
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",  // Correct
    "smtp_port": 587,                 // Correct for TLS
  }
}
```

4. **For Other Email Providers:**
   - **Outlook:** `smtp-mail.outlook.com`, port 587
   - **Yahoo:** `smtp.mail.yahoo.com`, port 587
   - **Custom SMTP:** Check your provider's documentation

### Issue 4: OpenAI API Error

**Error:**
```
Error: Incorrect API key provided
```

**Solutions:**

1. **Verify Key Format:**
```
Should start with: sk-proj- or sk-
Should be ~50-60 characters long
```

2. **Check API Credits:**
   - Go to: https://platform.openai.com/usage
   - Ensure you have available credits

3. **Try Different Model:**
```json
{
  "openai": {
    "model": "gpt-4-mini"  // Cheaper alternative
  }
}
```

### Issue 5: Contact Not Found When Updating

**Error:**
```
Contact not found
```

**Solutions:**

1. **Use Exact Email:**
```
# Wrong
Update contact john@company with phone 555-1234

# Correct
Update contact john@company.com with phone 555-1234
```

2. **Search in HubSpot First:**
   - Go to Contacts
   - Find the contact
   - Copy exact email
   - Use in query

3. **Use Contact ID Instead:**
```
Update contact 12345678 with phone 555-1234
```

### Issue 6: Deal Stage Not Recognized

**Error:**
```
Failed to create deal: Invalid dealstage
```

**Solutions:**

1. **Check Stage Names in HubSpot:**
   - Go to Settings → Objects → Deals
   - Click "Pipelines"
   - View stage internal names

2. **Use Correct Format:**
```
# Stage names are usually lowercase with no spaces
appointmentscheduled  ✓
appointment scheduled ✗
Appointment Scheduled ✗
```

3. **Common Stages:**
```
appointmentscheduled
qualifiedtobuy
presentationscheduled
decisionmakerboughtin
contractsent
closedwon
closedlost
```

---



## Step 10: Testing Checklist (5 minutes)

Run through this checklist to ensure everything works:

- [ ] **Configuration**
  - [ ] config.json exists and is valid JSON
  - [ ] All API keys are filled in
  - [ ] .gitignore includes config.json

- [ ] **Contact Operations**
  - [ ] Create contact with basic info
  - [ ] Create contact with all fields
  - [ ] Update existing contact
  - [ ] Search for contact

- [ ] **Deal Operations**
  - [ ] Create deal with basic info
  - [ ] Create deal with close date
  - [ ] Update deal amount
  - [ ] Update deal stage0

- [ ] **Email Notifications**
  - [ ] Receive contact creation email
  - [ ] Receive contact update email
  - [ ] Receive deal creation email
  - [ ] Receive error notification email

- [ ] **Error Handling**
  - [ ] Invalid query handled gracefully
  - [ ] API error shows helpful message
  - [ ] Missing config shows clear error

---


## ⚠️ Important Restriction: Object ID Requirement

To **update** or **delete** any **contact**, **company**, or **deal**, you **must know its object ID** in HubSpot.  
If you don't know the ID, you can **filter data first** to find it.

---

### 🔍 Example — Find Contact ID

**Example query:**
```bash
Return a contact having first name as Zaid
```

✅ **Output includes:**
```json
{
  "firstname": "Zaid",
  "lastname": "Khan",
  "email": "zaid@example.com",
  "objectId": "123456789"
}
```

Now you can use this `objectId` to update or delete:
```bash
Update contact 123456789 with phone 555-1234
Delete contact 123456789
```
