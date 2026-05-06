import pandas as pd
import json

# Define file mapping
case_files = {
    "BridgePower_Ltd": "case_BridgePower.json",
    "GreenTech_Solutions_Ltd": "case_greentech.json",
    "SolarScale_Ltd": "case_solarscale.json"
}

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

# Process each case
for company_id, json_path in case_files.items():
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # 1. Create Excel (using dataframes)
    flat_data = flatten_dict(data)
    df = pd.DataFrame([flat_data])
    df.to_excel(f"{company_id}_data.xlsx", index=False)
    
    # 2. Create Word-style Summary (Text)
    with open(f"{company_id}_summary.txt", "w") as f:
        f.write(f"--- UKEF CASE SUMMARY: {data['company']['name']} ---\n\n")
        for section, values in data.items():
            if isinstance(values, dict):
                f.write(f"[{section.upper()}]\n")
                for k, v in values.items():
                    f.write(f"{k.replace('_', ' ').capitalize()}: {v}\n")
                f.write("\n")

    # 3. Create PPT-style Slide (Text)
    with open(f"{company_id}_presentation_slide.txt", "w") as f:
        f.write(f"Slide 1: Executive Overview - {data['company']['name']}\n")
        f.write("="*40 + "\n")
        f.write(f"• SECTOR: {data['company'].get('sector')}\n")
        f.write(f"• AMOUNT REQUESTED: £{data['finance_request'].get('amount_gbp'):,}\n")
        f.write(f"• PURPOSE: {data['finance_request'].get('use_of_proceeds')}\n")
        f.write(f"• KEY MARKETS: {', '.join(data['export_plan'].get('target_markets', []))}\n")
        f.write(f"• ESG IMPACT: {data['strategic_pillars'].get('clean_growth_evidence')}\n")