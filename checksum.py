#! /usr/bin/env python
# Time-stamp: <2025-12-11 m.utrosa@bcbl.eu>

import hashlib, os
import nibabel as nib

def sha256_checksum(filename, block_size=65536):
    '''
    Generate SHA-256 checksum for a file for secure data validation.

    Checksum is a string that is used to verify file downloads/uploads and
    detect accidental/malicious changes (integrity check).

    Returns None on failure.
    '''
    sha = hashlib.sha256()
    try:
        with open(filename, 'rb') as f:
            for block in iter(lambda: f.read(block_size), b''):
                sha.update(block)
        return sha.hexdigest()
    except Exception:
        return None

def validate_nifti(filepath):
    '''
    Try loading and reading a NIfTI file using nibabel.
    '''
    try:
        img = nib.load(filepath)
        _ = img.get_fdata()
        return True, None
    except Exception as e:
        return False, str(e)

def check_dataset(root_dir, compute_hash=True):

    corrupted_files = []
    for root, _, files in os.walk(root_dir):
        for fname in files:
            path = os.path.join(root, fname)

            # Only validate NIfTI images for corruption detection
            if fname.endswith(('.nii', '.nii.gz')):
                valid, error = validate_nifti(path)
                if not valid:
                    corrupted_files.append((path, error))

            # Optional checksum for *all* files
            if compute_hash:
                checksum = sha256_checksum(path)
                if checksum is None:
                    corrupted_files.append((path, "Checksum read error"))

    return corrupted_files


# Example usage
if __name__ == "__main__":
    homePath  = "/home/mutrosa/Documents/projects/select_fMRI/data_MRI"
    corrupted = check_dataset(homePath)
    if not corrupted:
        print("No corrupted files detected.")
    else:
        print("\nCorrupted or unreadable files found:")
        for f, err in corrupted:
            print(f" - {f}\n   Error: {err}")