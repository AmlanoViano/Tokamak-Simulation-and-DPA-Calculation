#!/bin/bash
# ================================================================
# run_all.sh — run simulation for a given STL model
#
# Usage:
#   ./run_all.sh <path_to_stl>
# ================================================================

STL_FILE="${1:-geometry/grooves_10_ascii.stl}"

cd /home/amlan-halder/tokamak_sim/build

echo "=== STL model: $STL_FILE ==="

echo "=== Cleaning old data ==="
rm -f neutron_hits_*.csv dpa_analysis_*.png

echo "=== Running DT simulation ==="
./tokamak_sim "$STL_FILE" DT macros/run.mac

echo "=== Running TD simulation ==="
./tokamak_sim "$STL_FILE" TD macros/run.mac

echo "=== Merging thread CSV files ==="
head -1 neutron_hits_DT_nt_Hits_t0.csv > neutron_hits_DT_nt_Hits.csv
tail -n +2 -q neutron_hits_DT_nt_Hits_t*.csv >> neutron_hits_DT_nt_Hits.csv

head -1 neutron_hits_TD_nt_Hits_t0.csv > neutron_hits_TD_nt_Hits.csv
tail -n +2 -q neutron_hits_TD_nt_Hits_t*.csv >> neutron_hits_TD_nt_Hits.csv

echo "=== Running DPA analysis ==="
for mat in tungsten steel beryllium SiC RAFM; do
    python3 /home/amlan-halder/tokamak_sim/dpa_analysis.py \
        --material $mat --dir . --stl "$STL_FILE"
done

echo "=== Done! ==="
ls -lh dpa_analysis_*.png
wc -l neutron_hits_DT_nt_Hits.csv neutron_hits_TD_nt_Hits.csv
