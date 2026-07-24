import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_ROOT = ROOT / "sample_data"
INPUT_PATH = SAMPLE_ROOT / "extraction_outputs" / "extracted_fields.json"
OUTPUT_PATH = SAMPLE_ROOT / "mapping_outputs" / "mapped_evidence.json"

REQUIREMENTS = ["C3.2.1", "C5.1.3", "C6.3.2", "C7.1.1", "C1.2.1"]
DEPARTMENTS = ["CSE", "AIML", "AIDS", "Mechanical"]

def map_evidence():
    if not INPUT_PATH.exists():
        print(f"Input file not found: {INPUT_PATH}")
        return

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    mapped_data = []
    
    for item in data:
        file_path = item.get("file", "")
        extracted_fields = item.get("extracted_fields", {})
        
        # Mapping signals
        signals = []
        
        # 1. Folder/Filename mapping
        detected_reqs = [r for r in REQUIREMENTS if r in file_path]
        if detected_reqs:
            signals.append(detected_reqs[0])
            
        # 2. Extracted Fields mapping
        extracted_req = extracted_fields.get("mapped_requirement") or extracted_fields.get("requirement")
        if extracted_req:
            # simple check if any requirement matches
            for r in REQUIREMENTS:
                if r in extracted_req:
                    signals.append(r)
                    break
                    
        # Determine likely requirement
        likely_requirement = None
        confidence = 0.0
        
        if signals:
            # Most common signal
            likely_requirement = max(set(signals), key=signals.count)
            # Simple confidence calculation
            match_ratio = signals.count(likely_requirement) / len(signals)
            confidence = round(0.5 + (0.5 * match_ratio), 2)
        
        # Adjust confidence for empty/unknown
        if not likely_requirement:
            confidence = 0.0
            
        item["mapping"] = {
            "likely_requirement": likely_requirement,
            "confidence": confidence,
            "signals": signals
        }
        
        mapped_data.append(item)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(mapped_data, f, indent=2)

    print(f"Mapped {len(mapped_data)} documents into {OUTPUT_PATH}")

if __name__ == "__main__":
    map_evidence()
