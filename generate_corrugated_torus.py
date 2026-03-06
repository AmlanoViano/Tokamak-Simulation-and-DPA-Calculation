"""
Usage:
    python3 generate_corrugated_torus.py --grooves {number of grooves}
"""

import math, argparse, os

# FIXED PARAMETERS 
R     = 500.0   # major radius mm
A_OUT = 120.0   # outer minor radius mm
A_IN  = 116.0   # inner minor radius mm  
AMP   =  10.0   # corrugation amplitude mm

def get_resolution(n_grooves):
    n_profile = max(64, 80)         # poloidal resolution 
    n_spine   = max(256, n_grooves * 8)  # toroidal resolution 
    return n_spine, n_profile

def torus_point(phi_t, phi_p, a_minor, n_grooves):
    r = a_minor + AMP * math.sin(n_grooves * phi_t)
    x = (R + r * math.cos(phi_p)) * math.cos(phi_t)
    y = (R + r * math.cos(phi_p)) * math.sin(phi_t)
    z = r * math.sin(phi_p)
    return (x, y, z)

def triangle_normal(p0, p1, p2):
    ax, ay, az = p1[0]-p0[0], p1[1]-p0[1], p1[2]-p0[2]
    bx, by, bz = p2[0]-p0[0], p2[1]-p0[1], p2[2]-p0[2]
    nx = ay*bz - az*by
    ny = az*bx - ax*bz
    nz = ax*by - ay*bx
    mag = math.sqrt(nx*nx + ny*ny + nz*nz)
    if mag < 1e-12:
        return (0.0, 0.0, 1.0)
    return (nx/mag, ny/mag, nz/mag)

def write_triangles(f, triangles):
    for p0, p1, p2 in triangles:
        n = triangle_normal(p0, p1, p2)
        f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
        f.write(f"    outer loop\n")
        f.write(f"      vertex {p0[0]:.6e} {p0[1]:.6e} {p0[2]:.6e}\n")
        f.write(f"      vertex {p1[0]:.6e} {p1[1]:.6e} {p1[2]:.6e}\n")
        f.write(f"      vertex {p2[0]:.6e} {p2[1]:.6e} {p2[2]:.6e}\n")
        f.write(f"    endloop\n")
        f.write(f"  endfacet\n")

def generate_stl(n_grooves, output_path):
    n_spine, n_profile = get_resolution(n_grooves)

    print(f"Parameters:")
    print(f"  R         = {R} mm")
    print(f"  A_OUT     = {A_OUT} mm")
    print(f"  A_IN      = {A_IN} mm")
    print(f"  Thickness = {A_OUT - A_IN} mm")
    print(f"  Amplitude = {AMP} mm")
    print(f"  N_GROOVES = {n_grooves}")
    print(f"  N_SPINE   = {n_spine}  (toroidal, along major circle)")
    print(f"  N_PROFILE = {n_profile}  (poloidal, around tube cross-section)")
    print(f"  Total triangles ~ {4 * n_spine * n_profile:,}")
    print(f"Generating...")

    phi_t_vals = [2.0 * math.pi * i / n_spine   for i in range(n_spine)]
    phi_p_vals = [2.0 * math.pi * j / n_profile for j in range(n_profile)]

    with open(output_path, 'w') as f:
        f.write("solid corrugated_torus\n")

        for i in range(n_spine):
            if i % (n_spine // 10) == 0:
                print(f"  {100*i//n_spine}%...")

            i1 = (i + 1) % n_spine

            for j in range(n_profile):
                j1 = (j + 1) % n_profile

                oo = torus_point(phi_t_vals[i],  phi_p_vals[j],  A_OUT, n_grooves)
                o1 = torus_point(phi_t_vals[i1], phi_p_vals[j],  A_OUT, n_grooves)
                o2 = torus_point(phi_t_vals[i],  phi_p_vals[j1], A_OUT, n_grooves)
                o3 = torus_point(phi_t_vals[i1], phi_p_vals[j1], A_OUT, n_grooves)
                write_triangles(f, [(oo, o1, o3), (oo, o3, o2)])

                io = torus_point(phi_t_vals[i],  phi_p_vals[j],  A_IN, n_grooves)
                i1p= torus_point(phi_t_vals[i1], phi_p_vals[j],  A_IN, n_grooves)
                i2 = torus_point(phi_t_vals[i],  phi_p_vals[j1], A_IN, n_grooves)
                i3 = torus_point(phi_t_vals[i1], phi_p_vals[j1], A_IN, n_grooves)
                write_triangles(f, [(io, i3, i1p), (io, i2, i3)])

        f.write("endsolid corrugated_torus\n")

    size_mb = os.path.getsize(output_path) / 1e6
    print(f"  100%")
    print(f"Done! Saved to: {output_path} ({size_mb:.1f} MB)")
    print(f"\nVerification:")
    print(f"  Max XY = {R + A_OUT + AMP:.1f} mm")
    print(f"  Max Z  = {A_OUT + AMP:.1f} mm")
    print(f"  Wall thickness = {A_OUT - A_IN:.1f} mm")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--grooves', type=int, default=10)
    parser.add_argument('--output', type=str, default=None)
    args = parser.parse_args()
    out = args.output or f"corrugated_{args.grooves}.stl"
    generate_stl(args.grooves, out)