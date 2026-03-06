"""
Usage:
    python3 generate_vgroove_torus.py --grooves {number of grooves}
"""

import math, argparse, os

# FIXED PARAMETERS 
R          = 500.0  # major radius mm
A_OUT_PEAK = 120.0  # outer minor radius mm
A_OUT_VAL  = 102.0  # outer minor radius mm
A_IN_PEAK  = 116.0  # inner minor radius mm
A_IN_VAL   =  98.0  # inner minor radius mm

def triangular_wave(phi_t, n_grooves):
    t = (phi_t * n_grooves / (2.0 * math.pi)) % 1.0
    return 1.0 - 2.0 * abs(t - 0.5)

def a_outer(phi_t, n_grooves):
    w = triangular_wave(phi_t, n_grooves)
    return A_OUT_VAL + w * (A_OUT_PEAK - A_OUT_VAL)

def a_inner(phi_t, n_grooves):
    w = triangular_wave(phi_t, n_grooves)
    return A_IN_VAL + w * (A_IN_PEAK - A_IN_VAL)

def torus_point(phi_t, phi_p, a_minor):
    x = (R + a_minor * math.cos(phi_p)) * math.cos(phi_t)
    y = (R + a_minor * math.cos(phi_p)) * math.sin(phi_t)
    z = a_minor * math.sin(phi_p)
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

def get_resolution(n_grooves):
    n_spine   = max(512, n_grooves * 16)
    n_profile = 80
    return n_spine, n_profile

def generate_stl(n_grooves, output_path):
    n_spine, n_profile = get_resolution(n_grooves)
    wall_at_peak   = A_OUT_PEAK - A_IN_PEAK
    wall_at_valley = A_OUT_VAL  - A_IN_VAL

    print(f"Parameters:")
    print(f"  R              = {R} mm")
    print(f"  A_OUT peak     = {A_OUT_PEAK} mm  (XY_max = {R+A_OUT_PEAK:.0f} mm)")
    print(f"  A_OUT valley   = {A_OUT_VAL} mm")
    print(f"  A_IN  peak     = {A_IN_PEAK} mm")
    print(f"  A_IN  valley   = {A_IN_VAL} mm")
    print(f"  Groove depth   = {A_OUT_PEAK - A_OUT_VAL:.1f} mm")
    print(f"  Wall at peak   = {wall_at_peak:.1f} mm")
    print(f"  Wall at valley = {wall_at_valley:.1f} mm")
    print(f"  N_GROOVES      = {n_grooves}")
    print(f"  N_SPINE        = {n_spine}  (toroidal resolution)")
    print(f"  N_PROFILE      = {n_profile}  (poloidal resolution)")
    print(f"  Total triangles ~ {4 * n_spine * n_profile:,}")
    print(f"Generating...")

    phi_t_vals = [2.0 * math.pi * i / n_spine   for i in range(n_spine)]
    phi_p_vals = [2.0 * math.pi * j / n_profile for j in range(n_profile)]

    with open(output_path, 'w') as f:
        f.write("solid vgroove_torus\n")

        for i in range(n_spine):
            if i % (n_spine // 10) == 0:
                print(f"  {100*i//n_spine}%...")

            i1 = (i + 1) % n_spine

            ao_i  = a_outer(phi_t_vals[i],  n_grooves)
            ao_i1 = a_outer(phi_t_vals[i1], n_grooves)
            ai_i  = a_inner(phi_t_vals[i],  n_grooves)
            ai_i1 = a_inner(phi_t_vals[i1], n_grooves)

            for j in range(n_profile):
                j1 = (j + 1) % n_profile

                oo = torus_point(phi_t_vals[i],  phi_p_vals[j],  ao_i)
                o1 = torus_point(phi_t_vals[i1], phi_p_vals[j],  ao_i1)
                o2 = torus_point(phi_t_vals[i],  phi_p_vals[j1], ao_i)
                o3 = torus_point(phi_t_vals[i1], phi_p_vals[j1], ao_i1)
                write_triangles(f, [(oo, o1, o3), (oo, o3, o2)])

                io  = torus_point(phi_t_vals[i],  phi_p_vals[j],  ai_i)
                i1p = torus_point(phi_t_vals[i1], phi_p_vals[j],  ai_i1)
                i2  = torus_point(phi_t_vals[i],  phi_p_vals[j1], ai_i)
                i3  = torus_point(phi_t_vals[i1], phi_p_vals[j1], ai_i1)
                write_triangles(f, [(io, i3, i1p), (io, i2, i3)])

        f.write("endsolid vgroove_torus\n")

    size_mb = os.path.getsize(output_path) / 1e6
    print(f"  100%")
    print(f"Done! Saved to: {output_path} ({size_mb:.1f} MB)")
    print(f"\nVerification:")
    print(f"  Expected max XY = {R + A_OUT_PEAK:.1f} mm")
    print(f"  Expected max Z  = {A_OUT_PEAK:.1f} mm")
    print(f"  Wall thickness  = {wall_at_peak:.1f} mm (constant at peak and valley)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--grooves', type=int, default=100)
    parser.add_argument('--output', type=str, default=None)
    args = parser.parse_args()
    out = args.output or f"vgroove_{args.grooves}.stl"
    generate_stl(args.grooves, out)