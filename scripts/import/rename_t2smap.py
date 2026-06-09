#!/usr/bin/env python
# Time-stamp: <10-02-2026 m.utrosa@bcbl.eu>
import shutil, sys
from pathlib import Path

def rename_t2smap(homePath):
    '''
    Copy and rename T2smap files.

    Parameters:
       homePath: Project root directory.
    '''
    homePath = Path(homePath)
    optcomFold   = homePath / "data_MRI" / "sourcedata" / "t2smap"
    renamedFold  = optcomFold / "renamed"
    fmriprepFold = optcomFold / "fmriprep"
    renamedFold.mkdir(exist_ok=True, parents=True)

    # Remove "optimally combined" description from
    # BOLD and sbref filenames, so they can be used 
    # as single-echo data in preprocessing.
    for old_path in optcomFold.iterdir():

        # Skip directories
        if not old_path.is_file():
            continue
        
        old_name = old_path.name     
        if "desc-optcom" in old_name:

            # Build new filenames
            if "sbref" in old_name:
                idx = old_name.index("sbref") + len("sbref")
                new_name = old_name[:idx] + ".nii.gz"
            else:
                idx = old_name.index("_desc")
                new_name = old_name[:idx] + "_bold.nii.gz"
            
            # Copy and rename files
            new_path = renamedFold / old_name
            new_path_renamed = renamedFold / new_name
            print(f"Renaming: {old_name} → {new_name}")
            shutil.copy2(old_path, new_path)  
            new_path.rename(new_path_renamed)

    # Remove subject, session, and task information from
    # BOLD and sbref filenames, so they can replace fMRIprep 
    # output during preprocessing. fMRIprep's optimally combined
    # images involve large artifacts and perhaps lead to dvars
    # node crash in Nipype.

    for old_path in optcomFold.iterdir():

        # Skip directories
        if not old_path.is_file():
            continue

        old_name = old_path.name 
        # Rename & save renamed files
        if "optcom" in old_name or "T2star" in old_name:

            # Get only BOLD images, not their sbref files
            if "sbref" in old_name:
                continue

            # Find acqID
            acqID = old_name.split("_acq-")[1].split("_")[0]

            # Find subID & sesID
            idx = old_name.index("_task")
            subses = old_name[:idx]
            subID = subses.split("_")[0]
            sesID = subses.split("_")[1]

            # Define the new name
            if "optcom" in old_name:
                new_name = "desc-optcom_bold.nii.gz"
            elif "T2starmap" in old_name:
                new_name = "T2starmap.nii.gz"

            # Copy and rename files
            new_fold = fmriprepFold / subID / sesID / acqID
            new_fold.mkdir(exist_ok=True, parents=True)
            new_path = new_fold / old_name
            new_path_renamed = new_fold / new_name
            
            print(f"Renaming: {old_name} → {new_name}")
            shutil.copy2(old_path, new_path)
            new_path.rename(new_path_renamed)
  
if __name__ == "__main__":
    homePath = sys.argv[1]
    rename_t2smap(homePath)