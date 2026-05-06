# Pulls all agent definitions from Azure AI Foundry and saves them as YAML files.
# Run: python sync_agents.py

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

load_dotenv()

ENDPOINT   = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
AGENTS_DIR = Path(__file__).parent / "agents"
AGENTS_DIR.mkdir(exist_ok=True)

client = AIProjectClient(endpoint=ENDPOINT, credential=DefaultAzureCredential())


def sync():
    agents = client.agents.list()
    count = 0
    for agent in agents:
        details = client.agents.get(agent.name)
        data = details.as_dict() if hasattr(details, "as_dict") else vars(details)
        out_path = AGENTS_DIR / f"{agent.name}.yaml"
        with open(out_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)
        print(f"✓ {agent.name} → agents/{agent.name}.yaml")
        count += 1
    print(f"\nSynced {count} agents.")


if __name__ == "__main__":
    sync()
