#!/usr/bin/env python3
# Time-stamp: <02-12-2025 m.utrosa@bcbl.eu>
import json
from bids import BIDSLayout
from pathlib import Path

bids_root = "/home/mutrosa/Documents/projects/select_fMRI/data_MRI/sourcedata/raw"

# Initialize BIDS layout
layout = BIDSLayout(bids_root, validate=False)

# Get json files of single-band reference images
sbref_files = layout.get(suffix='sbref', extension='.json', return_type='filename')
print(f"Found {len(sbref_files)} sbref files.")

for sbref_path in sbref_files:

    # Identify the run number from file metadata
    entities = layout.parse_file_entities(sbref_path)
    run = entities.get("run", None)
    if run != "02" and run != 2:
        continue
    
    with open(sbref_path, 'r') as f:
        meta = json.load(f)

    # Modify PED only if it is exactly "j-"
    if meta.get("PhaseEncodingDirection") == "j-":
        meta["PhaseEncodingDirection"] = "i"
        with open(sbref_path, 'w') as f:
            json.dump(meta, f, indent=4)
        print(f"Updated PED in: {sbref_path}")
    else:
        print(f"Skipping {sbref_path}: PED is {meta.get('PhaseEncodingDirection')}")