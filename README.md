# Cross-Functional-Task-Extractor-Workflow

Overview

This system automates the end-to-end flow of turning Google Meet discussions into trackable action items in Trello, with Google Workspace and n8n acting as the backbone.

It eliminates manual note-taking, task copy-pasting, and follow-ups by:

Auto-generating meeting notes with action items

Extracting tasks and assignees programmatically

Persisting them in Google Sheets as a source of truth

Syncing them into Trello boards without duplication

Cleaning up stale data automatically

🧠 High-Level Flow

Tools involved

Google Meet

Google Gemini

Google Docs

Google Apps Script

Google Sheets

n8n

Trello

End-to-End Lifecycle

Weekly Meeting

Meetings are conducted on Google Meet.

AI-Generated Notes

Google Gemini auto-generates meeting notes with a section titled:

Suggested Next Steps

Notes are saved as a Google Doc in a designated Meeting Notes Drive folder.

Task Extraction (Google Apps Script)

A scheduled Apps Script:

Finds the latest “Biz Dev <>” Google Doc created in the last 24 hours

Extracts tasks from the Suggested Next Steps section

Identifies the assignee using natural language rules

Appends structured rows into a Google Sheet

Task Sync (n8n)

n8n reads new rows from the Google Sheet

Filters out tasks already sent to Trello

Maps business categories to Trello list IDs

Creates Trello cards

Marks tasks as “Sent to Trello” to prevent duplication

Data Retention

Tasks older than 1 month are automatically removed from the sheet to keep it lightweight and scalable.

🗂️ Google Sheet Schema

The Google Sheet acts as the single source of truth.

Column Name	Description
Task	Cleaned action item text
Assignee	Extracted from task sentence
Category	Business category (e.g., Biz Dev)
Date Created	Meeting doc creation date
Sent to Trello	Flag to avoid duplicate Trello cards
⚙️ Google Apps Script Details
Purpose

Extract structured action items from AI-generated meeting notes and persist them in a spreadsheet.

What the Script Does

Locate the latest meeting doc

Searches a specific Google Drive folder

Filters Google Docs named Biz Dev <>*

Only considers files created in the last 24 hours

Parse the document

Uses the Google Docs API

Finds the Suggested Next Steps section

Stops parsing when the next heading begins

Skips Gemini footer/system messages

Cleans emojis and non-ASCII characters

Extract assignees

Uses a simple NLP heuristic:

"<Name> will <do something>"


Example:

James Rodriguez will follow up with the client
→ Assignee: James Rodriguez

Append to Google Sheet

Each task becomes a new row

Automatically timestamps tasks

Initializes Sent to Trello as blank

🔁 n8n Workflow Logic
Trigger

Webhook or scheduled execution

Key Steps

Fetch spreadsheet rows

Reads all tasks from the Google Sheet

Deduplication

Filters out rows where Sent to Trello is already populated

Category Mapping

Converts human-readable categories into Trello List IDs

Example:

Biz Dev → 6966f61e68e5fc1c64fae6c1

Create Trello Cards

Task → Card title

Category → Trello list

Assignee → Optional metadata

Update Source of Truth

Marks the row as Sent to Trello = Yes

🧹 Data Retention & Scalability

Tasks older than 1 month are deleted from the Google Sheet

Prevents unbounded growth

Keeps n8n executions fast and predictable

Ensures the sheet stays operationally focused

🔐 Assumptions & Constraints

Meeting notes follow a consistent format

Action items are written as sentences with “will”

Google Gemini is enabled for Meet notes

Apps Script has access to:

Google Drive

Google Docs API

Google Sheets

n8n has authenticated access to:

Google Sheets

Trello API

✅ Benefits

Zero manual task entry

Clear ownership on every action item

No duplicate Trello cards

Clean separation of concerns:

AI → Notes

Script → Structuring

n8n → Orchestration

Easily extensible to Jira, Asana, or Slack



Workflow Diagram: 

<img width="2554" height="1332" alt="image" src="https://github.com/user-attachments/assets/24067efa-df31-4ac8-a728-accdf072f1d2" />
