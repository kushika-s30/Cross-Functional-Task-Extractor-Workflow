/**
 * --------------------------------------------
 * Meeting Notes → Action Items Extractor
 * --------------------------------------------
 * This script:
 * 1. Finds the most recent Google Doc created in a given time window
 * 2. Extracts the "Suggested Next Steps" section
 * 3. Cleans and parses tasks and assignees
 * 4. Appends structured action items into a Google Sheet
 *
 * Designed for:
 * - Automated meeting follow-ups
 * - Action-item tracking
 * - Downstream integrations (e.g., Trello, Jira, n8n)
 *
 * Author: Kushika Sivaprakasam
 * Tech: Google Apps Script, Google Docs API, Google Sheets
 */

/**
 * -------------------------
 * 🔧 CONFIGURATION
 * -------------------------
 * Update these values when deploying in a new workspace.
 */
const CONFIG = {
  DRIVE_FOLDER_ID: "REPLACE_WITH_FOLDER_ID", // Folder containing meeting notes
  DOC_NAME_PREFIX: "",                       // Optional: document name prefix filter
  LOOKBACK_HOURS: 24,                        // Time window for latest doc
  SHEET_URL: "REPLACE_WITH_SHEET_URL",       // Destination Google Sheet
  CATEGORY: "Meeting Notes"                  // Generic task category
};

/**
 * Main orchestrator function
 */
function extractSuggestedNextStepsToSheet() {
  const latestDoc = getLatestMeetingDoc();

  if (!latestDoc) {
    Logger.log("❌ No recent meeting document found.");
    return;
  }

  Logger.log(`✅ Processing document: ${latestDoc.getName()}`);

  const tasks = extractSuggestedNextSteps(latestDoc.getId());

  if (!tasks.length) {
    Logger.log("❌ No action items found.");
    return;
  }

  appendTasksToSheet(tasks, latestDoc.getDateCreated());

  Logger.log(`✅ Successfully appended ${tasks.length} tasks.`);
}

/**
 * -------------------------
 * 📄 DOCUMENT DISCOVERY
 * -------------------------
 * Finds the most recent Google Doc within the configured time window
 */
function getLatestMeetingDoc() {
  const folder = DriveApp.getFolderById(CONFIG.DRIVE_FOLDER_ID);
  const files = folder.getFiles();

  const cutoffTime =
    Date.now() - CONFIG.LOOKBACK_HOURS * 60 * 60 * 1000;

  let latestFile = null;
  let latestTimestamp = 0;

  while (files.hasNext()) {
    const file = files.next();

    if (file.getMimeType() !== MimeType.GOOGLE_DOCS) continue;

    if (
      CONFIG.DOC_NAME_PREFIX &&
      !file.getName().startsWith(CONFIG.DOC_NAME_PREFIX)
    ) {
      continue;
    }

    const createdTime = file.getDateCreated().getTime();

    if (createdTime >= cutoffTime && createdTime > latestTimestamp) {
      latestTimestamp = createdTime;
      latestFile = file;
    }
  }

  return latestFile;
}

/**
 * -------------------------
 * ✂️ CONTENT EXTRACTION
 * -------------------------
 * Pulls the "Suggested Next Steps" section from the document
 */
function extractSuggestedNextSteps(docId) {
  const doc = Docs.Documents.get(docId);
  const content = doc.body.content || [];

  let inTargetSection = false;
  const tasks = [];

  for (const block of content) {
    if (!block.paragraph) continue;

    const paragraph = block.paragraph;
    const text = (paragraph.elements || [])
      .map(el => el.textRun?.content || "")
      .join("")
      .replace(/[^\x20-\x7E]/g, "")
      .trim();

    if (!text) continue;

    const lowerText = text.toLowerCase();

    // Start extracting after section header
    if (lowerText === "suggested next steps") {
      inTargetSection = true;
      continue;
    }

    // Stop when the next heading begins
    if (
      inTargetSection &&
      paragraph.paragraphStyle?.namedStyleType?.startsWith("HEADING")
    ) {
      break;
    }

    // Skip auto-generated system notes
    if (
      text.startsWith("You should review") ||
      text.startsWith("Please provide feedback")
    ) {
      continue;
    }

    if (inTargetSection) {
      tasks.push(text);
    }
  }

  return tasks;
}

/**
 * -------------------------
 * 📊 SHEET PERSISTENCE
 * -------------------------
 * Writes extracted tasks to Google Sheets
 */
function appendTasksToSheet(tasks, docDate) {
  const sheet = SpreadsheetApp
    .openByUrl(CONFIG.SHEET_URL)
    .getSheets()[0];

  const formattedDate = Utilities.formatDate(
    docDate,
    Session.getScriptTimeZone(),
    "MM/dd/yyyy"
  );

  tasks.forEach(task => {
    const assignee = extractAssignee(task);

    sheet.appendRow([
      task,               // Task description
      assignee,           // Assignee
      CONFIG.CATEGORY,    // Category
      formattedDate,      // Meeting date
      ""                  // Downstream sync flag (e.g., Trello)
    ]);
  });
}

/**
 * -------------------------
 * 👤 ASSIGNEE PARSER
 * -------------------------
 * Assumption:
 * - Assignee name appears before the word "will"
 *
 * Example:
 * "Jane Doe will follow up with the client"
 */
function extractAssignee(taskText) {
  const match = taskText.match(/^([A-Za-z\s]+?)\s+will\s+/i);
  return match ? match[1].trim() : "";
}
