# MeetingOps

# Overview

This system automates the end-to-end flow of turning Google Meet discussions into trackable action items in Trello, with Google Workspace and n8n acting as the backbone.

It eliminates manual note-taking, task copy-pasting, and follow-ups by:

- Auto-generating meeting notes with action items  
- Extracting tasks and assignees programmatically  
- Persisting them in Google Sheets as a source of truth  
- Syncing them into Trello boards without duplication  
- Cleaning up stale data automatically  

---

## 🧠 High-Level Flow

### Tools Involved

- Google Meet  
- Google Gemini  
- Google Docs  
- Google Apps Script  
- Google Sheets  
- n8n  
- Trello  

---

## End-to-End Lifecycle

### 1. Weekly Meeting
Meetings are conducted on Google Meet.

### 2. AI-Generated Notes
Google Gemini auto-generates meeting notes with a section titled:

**Suggested Next Steps**

Notes are saved as a Google Doc in a designated *Meeting Notes* Drive folder.

### 3. Task Extraction (Google Apps Script)

A scheduled Apps Script:

- Finds the latest **“Biz Dev <>”** Google Doc created in the last 24 hours  
- Extracts tasks from the **Suggested Next Steps** section  
- Identifies the assignee using natural language rules  
- Appends structured rows into a Google Sheet  

### 4. Task Sync (n8n)

- n8n reads new rows from the Google Sheet  
- Filters out tasks already sent to Trello  
- Maps business categories to Trello list IDs  
- Creates Trello cards  
- Marks tasks as **“Sent to Trello”** to prevent duplication  

### 5. Data Retention

Tasks older than **1 month** are automatically removed from the sheet to keep it lightweight and scalable.

Workflow Diagram: 

<img width="2554" height="1332" alt="image" src="https://github.com/user-attachments/assets/24067efa-df31-4ac8-a728-accdf072f1d2" />

## 🗂️ Google Sheet Schema

The Google Sheet acts as the single source of truth.

| Column Name       | Description                                   |
|-------------------|-----------------------------------------------|
| Task              | Cleaned action item text                      |
| Assignee          | Extracted from task sentence                  |
| Category          | Business category (e.g., Biz Dev)             |
| Date Created      | Meeting doc creation date                    |
| Sent to Trello    | Flag to avoid duplicate Trello cards          |



## ⚙️ Google Apps Script Details

### Purpose
Extract structured action items from AI-generated meeting notes and persist them in a spreadsheet.

### What the Script Does

#### Locate the Latest Meeting Doc
- Searches a specific Google Drive folder  
- Filters Google Docs with the Meeting Notes file name  
- Only considers files created in the last 24 hours  

#### Parse the Document
- Uses the Google Docs API  
- Finds the **Suggested Next Steps** section  
- Stops parsing when the next heading begins  
- Skips Gemini footer/system messages  
- Cleans emojis and non-ASCII characters  

#### Extract Assignees
Uses a simple NLP heuristic:

#### Append to Google Sheet
- Each task becomes a new row  
- Automatically timestamps tasks  
- Initializes **Sent to Trello** as blank

#### n8n Workflow

## 1. Manual Trigger

**Node:** When clicking **Execute workflow**

The workflow only runs when you manually click **Execute workflow** in n8n.

---

## 2. Read Tasks from Google Sheets

**Node:** Get row(s) in sheet

Reads all rows from a Google Sheet called **“Tasks List”** (`Sheet1`).

Each row represents a task with fields such as:
- **Task**
- **Category**
- **Sent to trello**
- **row_number**

---

## 3. Filter Tasks Not Yet Sent to Trello

**Node:** If

Checks the following condition:
- **“Sent to trello” is empty**

Only rows that haven’t been sent to Trello continue in the workflow.  
Rows already marked as sent are ignored.

---

## 4. Convert Category Names to Trello Label IDs

**Node:** Code (JavaScript)

Takes the task’s **Category** (text) and converts it into a Trello **label ID**.

**Mapping example:**
- `"Biz Dev"` → `6966f61e68e5fc1c64fae6c1`
- `"Investor Relations"` → `6966f65393a8d4b1003807b1`
- `"Product"` → `6966f8256adb5db949daef3c`
- `"Tech Dev"` → `6966f878c055c9fc084c709b`
- `"Ops"` → `6966f94b79c3f7597fe24e32`

This is required because Trello expects **label IDs**, not label names.

---

## 5. Create a Trello Card

**Node:** Create a card

Creates a card in a specific Trello list:
- **listId:** `6966f2efe8c00f1fafcca5e2`

**Card details:**
- **Card name:** value from **Task**
- **Label:** mapped **Category** label ID

---

## 6. Mark Task as Sent in Google Sheets

**Node:** Update row in sheet

Updates the same row in Google Sheets:
- Sets **“Sent to trello” = "Yes"**
- Uses **row_number** to ensure the correct row is updated

This prevents the same task from being added to Trello again in future runs.

