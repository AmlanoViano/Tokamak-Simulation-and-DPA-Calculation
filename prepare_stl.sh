#!/bin/bash
STL_FILE="$1"
if [ -z "$STL_FILE" ]; then
    echo "Usage: ./prepare_stl.sh <path_to_stl>"
    exit 1
fi
if [ ! -f "$STL_FILE" ]; then
    echo "Error: File not found: $STL_FILE"
    exit 1
fi

echo "=== Converting to ASCII ==="
python3 /home/amlan-halder/tokamak_sim/convert_stl_ascii.py "$STL_FILE"

FILENAME=$(basename "$STL_FILE")
echo "=== Copying to build/geometry ==="
cp "$STL_FILE" /home/amlan-halder/tokamak_sim/build/geometry/"$FILENAME"
echo "  Copied to: build/geometry/$FILENAME"

echo "=== Checking dimensions ==="
MAX_XY=$(grep "vertex" /home/amlan-halder/tokamak_sim/build/geometry/"$FILENAME" | awk '{print $2}' | sort -rn | head -1)
MAX_Z=$(grep "vertex" /home/amlan-halder/tokamak_sim/build/geometry/"$FILENAME" | awk '{print $4}' | sort -rn | head -1)

python3 - <<PYEOF
max_xy = $MAX_XY
max_z  = $MAX_Z
a_out  = max_z
R      = max_xy - a_out
print(f"  R     = {R:.1f} mm")
print(f"  a_out = {a_out:.1f} mm")
print(f"  Suggested fa = {a_out * 0.6:.1f} mm")
PYEOF

echo "=== Current PrimaryGeneratorAction.hh ==="
grep "fR\|fa" /home/amlan-halder/tokamak_sim/include/PrimaryGeneratorAction.hh

echo ""
echo "=== If dimensions changed, rebuild: ==="
echo "  cd /home/amlan-halder/tokamak_sim/build && make -j\$(nproc)"
echo "=== Then run: ==="
echo "  ./run_all.sh geometry/$FILENAME"
