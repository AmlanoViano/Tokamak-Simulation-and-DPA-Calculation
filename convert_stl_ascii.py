import struct, sys, os

def convert_to_ascii(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    if data[:5] == b'solid':
        print(f"Already ASCII — no conversion needed.")
        return
    num_tris = struct.unpack_from('<I', data, 80)[0]
    print(f"Binary STL: {num_tris} triangles — converting...")
    lines = ["solid converted"]
    offset = 84
    for i in range(num_tris):
        nx, ny, nz = struct.unpack_from('<fff', data, offset); offset += 12
        v1x,v1y,v1z = struct.unpack_from('<fff', data, offset); offset += 12
        v2x,v2y,v2z = struct.unpack_from('<fff', data, offset); offset += 12
        v3x,v3y,v3z = struct.unpack_from('<fff', data, offset); offset += 12
        offset += 2
        lines += [f"  facet normal {nx:.6e} {ny:.6e} {nz:.6e}",
                  f"    outer loop",
                  f"      vertex {v1x:.6e} {v1y:.6e} {v1z:.6e}",
                  f"      vertex {v2x:.6e} {v2y:.6e} {v2z:.6e}",
                  f"      vertex {v3x:.6e} {v3y:.6e} {v3z:.6e}",
                  f"    endloop",
                  f"  endfacet"]
    lines.append("endsolid converted")
    with open(filepath, 'w') as f:
        f.write("\n".join(lines) + "\n")
    print(f"Done. '{filepath}' converted to ASCII ({os.path.getsize(filepath)/1e6:.1f} MB).")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 convert_stl_ascii.py <file.stl>")
        sys.exit(1)
    convert_to_ascii(sys.argv[1])
