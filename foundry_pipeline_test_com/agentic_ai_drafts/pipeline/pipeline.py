# pip install --pre azure-ai-projects>=2.0.0b4 python-dotenv openpyxl

import os
import sys
import json
import glob
import uuid
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()
ENDPOINT      = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
WORKFLOW_NAME = os.getenv("WORKFLOW_NAME", "UKEF-CREDIT")
BASE_DIR      = Path(__file__).parent.parent
INPUTS        = BASE_DIR / "inputs"
OUTPUTS       = BASE_DIR / "outputs"
OUTPUTS.mkdir(exist_ok=True)

project_client = AIProjectClient(endpoint=ENDPOINT, credential=DefaultAzureCredential())
openai_client  = project_client.get_openai_client()


def read_input(file_path: str) -> str:
    suffix = Path(file_path).suffix.lower()
    if suffix == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(file_path, data_only=True)
        lines = []
        for sheet in wb.worksheets:
            lines.append(f"Sheet: {sheet.title}")
            for row in sheet.iter_rows(values_only=True):
                row_text = "\t".join(str(c) if c is not None else "" for c in row)
                if row_text.strip():
                    lines.append(row_text)
        return "\n".join(lines)
    with open(file_path, "r", encoding="utf-8") as f:
        if suffix == ".json":
            return json.dumps(json.load(f), indent=2)
        return f.read()


def run_workflow_audit(file_path: str):
    name = Path(file_path).stem
    print(f"\n{'='*60}\nAUDITING: {name}\n{'='*60}")

    case = read_input(file_path)

    conversation = openai_client.conversations.create()
    print(f"Conversation ID: {conversation.id}")

    stream = openai_client.responses.create(
        conversation=conversation.id,
        extra_body={"agent_reference": {"name": WORKFLOW_NAME, "type": "agent_reference"}},
        input=f"Analyze this export finance case:\n{case}",
        stream=True,
        metadata={"x-ms-debug-mode-enabled": "1"},
    )

    final_report = ""
    for event in stream:
        t = event.type
        if t == "response.output_item.added" \
                and getattr(getattr(event, "item", None), "type", None) == "workflow_action":
            print(f"\n[STEP STARTED] {event.item.action_id}")
        elif t == "response.output_item.done" \
                and getattr(getattr(event, "item", None), "type", None) == "workflow_action":
            print(f"[STEP DONE]    {event.item.action_id} ({event.item.status})")
        elif t == "response.output_text.delta":
            print(getattr(event, "delta", ""), end="", flush=True)
        elif t == "response.output_text.done":
            final_report = getattr(event, "text", "")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    short_id  = uuid.uuid4().hex[:6]
    output_file = OUTPUTS / f"audit_{name}_{timestamp}_{short_id}.json"
    with open(output_file, "w") as f:
        json.dump({
            "case":            name,
            "conversation_id": conversation.id,
            "workflow":        WORKFLOW_NAME,
            "timestamp":       timestamp,
            "summary":         final_report,
        }, f, indent=2)

    print(f"\n\nSaved → {output_file}")
    print(f"Conversation kept: {conversation.id}")
    return conversation.id


def get_all_files():
    files = (
        glob.glob(str(INPUTS / "JSON" / "case_*.json")) +
        glob.glob(str(INPUTS / "M365" / "*.xlsx")) +
        glob.glob(str(INPUTS / "M365" / "*.txt"))
    )
    return [f for f in files if "template" not in Path(f).name.lower()
            and not Path(f).name.startswith("~$")]


def show_menu(files):
    print("\nAvailable cases:")
    for i, f in enumerate(files, 1):
        print(f"  {i}. {Path(f).name}")
    print("\nRun which case? (number or 'all'): ", end="")
    choice = input().strip().lower()
    if choice == "all":
        return files
    if choice.isdigit() and 1 <= int(choice) <= len(files):
        return [files[int(choice) - 1]]
    print("Invalid choice.")
    return []


if __name__ == "__main__":
    files = get_all_files()
    if not files:
        print("No input files found.")
        sys.exit(1)

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "all":
            selected = files
        else:
            match = [f for f in files if arg in Path(f).name]
            if not match:
                print(f"No case found matching '{arg}'")
                sys.exit(1)
            selected = match
    else:
        selected = show_menu(files)

    for i, f in enumerate(selected):
        run_workflow_audit(f)
        if i < len(selected) - 1:
            print("\nPress Enter to continue to next case...")
            input()
