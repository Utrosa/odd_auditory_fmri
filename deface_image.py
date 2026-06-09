#!/usr/bin/env python3
# Time-stamp: <2025-23-02 m.utrosa@bcbl.eu>

import subprocess
import sys
from pathlib import Path

# Source: https://github.com/poldracklab/pydeface/

def deface_image(input_path, output_path=None):
    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_path is None:
        output_path = input_path.with_name(input_path.stem + "_defaced.nii.gz")

    cmd = [
        "pydeface",
        str(input_path),
        "--outfile",
        str(output_path),
        "--force"  # overwrite if exists
    ]

    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

    print(f"Defaced image saved to: {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python deface.py <input_nifti> [output_nifti]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    deface_image(input_file, output_file)