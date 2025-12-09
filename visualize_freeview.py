#!/usr/bin/env python3
import argparse, glob, os
from pathlib import Path

def find_bids_files(bids_dir, sub, ses, modalities, acq=None, task=None, direction=None, echo=None, suffix=None):
    """
    BIDS-style selective grabber without pybids.
    Only returns files matching the provided BIDS entities.
    """

    base = Path(bids_dir) / f"sub-{sub}" / f"ses-{ses}"
    all_matches = []

    # Map modalities to BIDS folders + expected suffixes
    modality_to_folder = {
        "t1w": ("anat", "T1w"),
        "t1":  ("anat", "T1w"),
        "fmap": ("fmap", "epi"),
        "bold": ("func", "bold"),
        "sbref": ("func", "sbref"),
    }

    for mod in modalities:
        m = mod.lower()

        if m not in modality_to_folder:
            print(f"⚠ Unknown modality: {m}")
            continue

        folder, default_suffix = modality_to_folder[m]

        # If the user explicitly provided a suffix, override
        suffix_used = suffix if suffix else default_suffix

        # Grab EVERYTHING with that suffix first
        pattern = base / folder / f"sub-{sub}_ses-{ses}_*_{suffix_used}.nii.gz"
        candidates = glob.glob(str(pattern))

        filtered = []
        for f in candidates:
            fname = Path(f).name

            # Apply strict BIDS entity checks
            if acq and f"acq-{acq}" not in fname:
                continue
            if task and f"task-{task}" not in fname:
                continue
            if direction and f"dir-{direction}" not in fname:
                continue
            if echo and f"echo-{echo}" not in fname:
                continue

            filtered.append(f)

        all_matches.extend(filtered)

    return sorted(all_matches)

def launch_freeview(file_list, bids_dir, sub):
    """Launch Freeview with os.system."""
    if not file_list:
        print("\n❌ No matching BIDS files found.")
        return

    print("\n🧠 Launching Freeview with files:")
    for f in file_list:
        print("  ", f)

    # Add the explicit T1w file
    t1_file = f"{bids_dir}/sub-{sub}/ses-01/anat/sub-{sub}_ses-01_T1w.nii.gz"
    if t1_file not in file_list:
        file_list.append(t1_file)

    cmd = "freeview " + " ".join(file_list)
    os.system(cmd)

def main():
    parser = argparse.ArgumentParser(description="Visualize BIDS MRI files in Freeview.")
    parser.add_argument("--bids_dir", required=True, help="Path to BIDS root directory.")
    parser.add_argument("--sub", required=True, help="Subject ID (without 'sub-').")
    parser.add_argument("--ses", required=True, help="Session ID (without 'ses-').")
    parser.add_argument("--acq", required=False, help="Acquisition label (optional).")
    parser.add_argument(
        "--modalities",
        nargs="+",
        required=True,
        help="Modalities to load: fmap, bold, sbref."
    )

    args = parser.parse_args()

    files = find_bids_files(
        bids_dir=args.bids_dir,
        sub=args.sub,
        ses=args.ses,
        modalities=args.modalities,
        acq=args.acq
    )

    launch_freeview(files, bids_dir=args.bids_dir, sub=args.sub)


if __name__ == "__main__":
    main()