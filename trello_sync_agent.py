import os
import json
import gspread
import requests
import warnings
# Suppress Pydantic V1 warnings from LangChain
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_core._api.deprecation")

from typing import List, Dict, Optional, Any
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv()

# Configuration
SPREADSHEET_ID = "1ORI0huHb5mNMU7LsOiFaAKKVa-sHKeZg3xLO5gH6EFA"
SHEET_NAME = "Sheet1"
TRELLO_LIST_ID = "6966f2efe8c00f1fafcca5e2"

# Category Mapping
CATEGORY_MAPPING = {
    "Biz Dev": "6966f61e68e5fc1c64fae6c1",
    "Investor Relations": "6966f65393a8d4b1003807b1",
    "Product": "6966f8256adb5db949daef3c",
    "Tech Dev": "6966f878c055c9fc084c709b",
    "Ops": "6966f94b79c3f7597fe24e32"
}

def get_google_sheet_client():
    try:
        return gspread.service_account(filename="credentials.json")
    except Exception:
        return gspread.service_account()

# --- Tool Implementations ---

@tool
def fetch_unsent_tasks() -> str:
    """
    Fetches tasks from the Google Sheet where 'Sent to trello' is empty.
    Returns: JSON string of tasks.
    """
    try:
        gc = get_google_sheet_client()
        sh = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sh.worksheet(SHEET_NAME)
        records = worksheet.get_all_records()
        
        unsent_tasks = []
        for i, row in enumerate(records, start=2):
            sent_status = str(row.get("Sent to trello", "")).strip()
            if not sent_status or sent_status.lower() != "yes":
                row['_row_number'] = i 
                unsent_tasks.append(row)
                
        return json.dumps(unsent_tasks)
    except Exception as e:
        print(f"DEBUG: Full error in fetch_unsent_tasks:\n{traceback.format_exc()}")
        return f"Error fetching tasks: {str(e)}"

@tool
def create_trello_card(task_name: str, category: str) -> str:
    """
    Creates a card in Trello.
    """
    api_key = os.getenv("TRELLO_API_KEY")
    token = os.getenv("TRELLO_TOKEN")
    
    if not api_key or not token:
        return "Error: TRELLO_API_KEY and TRELLO_TOKEN must be set."

    label_id = CATEGORY_MAPPING.get(category)
    url = "https://api.trello.com/1/cards"
    query = {
        'idList': TRELLO_LIST_ID,
        'key': api_key,
        'token': token,
        'name': task_name
    }
    if label_id:
        query['idLabels'] = label_id

    try:
        response = requests.post(url, params=query)
        if response.status_code == 200:
            return response.json().get('id', 'unknown_id')
        else:
            return f"Error creating card: {response.text}"
    except Exception as e:
        return f"Error: {e}"

@tool
def mark_task_as_sent(row_number: int) -> str:
    """
    Updates the Google Sheet row to set 'Sent to trello' to 'Yes'.
    """
    try:
        gc = get_google_sheet_client()
        sh = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sh.worksheet(SHEET_NAME)
        headers = worksheet.row_values(1)
        try:
            col_index = headers.index("Sent to trello") + 1
        except ValueError:
            return "Error: Column 'Sent to trello' not found."
        worksheet.update_cell(row_number, col_index, "Yes")
        return f"Successfully updated row {row_number}"
    except Exception as e:
        return f"Error updating sheet: {str(e)}"

# --- Main Agent Logic (Manual Loop for Robustness) ---

def run_agent():
    print("Starting Trello Sync Agent (LangChain + OpenAI)...")
    
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found.")
        return

    tools = [fetch_unsent_tasks, create_trello_card, mark_task_as_sent]
    tools_map = {t.name: t for t in tools}

    # Initialize OpenAI Model
    # Using gpt-4o for best reasoning, cheap and fast.
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    llm_with_tools = llm.bind_tools(tools)

    messages = [
        SystemMessage(content=(
            "You are an automation agent.\n"
            "1. Call fetch_unsent_tasks to see what needs processing.\n"
            "2. For each task found, call create_trello_card (mapping category correctly).\n"
            "3. If successful, call mark_task_as_sent with the _row_number.\n"
            "4. Repeat until all unsent tasks are processed."
        )),
        HumanMessage(content="Sync tasks from Sheet to Trello.")
    ]

    print("Running agent loop...")
    
    for _ in range(10):  # Max turns
        try:
            ai_msg = llm_with_tools.invoke(messages)
            messages.append(ai_msg)
            
            if not ai_msg.tool_calls:
                print("Agent concluded:", ai_msg.content)
                break
            
            print(f"Agent requested {len(ai_msg.tool_calls)} tool calls...")
            for tc in ai_msg.tool_calls:
                tool_name = tc['name']
                print(f"  - Executing {tool_name}...")
                selected_tool = tools_map.get(tool_name)
                if selected_tool:
                    try:
                        res = selected_tool.invoke(tc['args'])
                        print(f"    Result: {str(res)[:50]}...") # Truncate log
                        messages.append(ToolMessage(tool_call_id=tc['id'], content=str(res)))
                    except Exception as tool_err:
                        err_msg = f"Tool Execution Error: {tool_err}"
                        print(f"    {err_msg}")
                        messages.append(ToolMessage(tool_call_id=tc['id'], content=err_msg))
            
        except Exception as e:
            print(f"CRITICAL ERROR during generation: {e}")
            break

if __name__ == "__main__":
    run_agent()
