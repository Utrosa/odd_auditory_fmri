#! /usr/bin/env bash
# Time-stamp: <2025-11-24 m.utrosa@bcbl.eu>

# ---- 1.5 mm
# acq-DresdenNoFat
# acq-DresdenWFat
# acq-ME1TR880
# acq-ME3TR1600
# acq-ME3TR1100
# acq-ME3TR850
# acq-ME3TR700

# ---- 1.75 mm
# acq-DresdenNoFat175
# acq-DresdenWFat175
# acq-ME1TR780
# acq-ME3TR1180
# acq-ME3TR770
# acq-ME3TR680

python visualize_freeview.py \
  --bids_dir /home/mutrosa/Documents/projects/select_fMRI/data_MRI/sourcedata/raw/raw_withNORDIC \
  --sub 02 --ses 01 --modalities bold --acq NOACC