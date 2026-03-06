import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import argparse
import os

MATERIALS = {
    'tungsten':  {'symbol': 'W',    'Ed_eV': 90,  'density': 19.3, 'A': 184},
    'steel':     {'symbol': 'Fe',   'Ed_eV': 40,  'density': 7.9,  'A': 56},
    'beryllium': {'symbol': 'Be',   'Ed_eV': 31,  'density': 1.85, 'A': 9},
    'SiC':       {'symbol': 'SiC',  'Ed_eV': 35,  'density': 3.21, 'A': 28},
    'RAFM':      {'symbol': 'RAFM', 'Ed_eV': 40,  'density': 7.7,  'A': 56},
}


SOURCE_STRENGTH_N_PER_S = 1e20   # neutrons/second (~500 MW fusion power)

def nrt_dpa(E_neutron_MeV, A_target, Ed_eV):
    m_n = 1.0
    T_max_eV = 4*m_n*A_target/(m_n+A_target)**2 * E_neutron_MeV * 1e6
    T_pka_eV = T_max_eV / 2.0
    if T_pka_eV < Ed_eV:      return 0.0
    elif T_pka_eV < 2*Ed_eV:  return 1.0
    else:                      return 0.8 * T_pka_eV / (2*Ed_eV)

def nrt_dpa_angle(E_neutron_MeV, A_target, Ed_eV, angle_deg):
    """
    Angle-dependent NRT-DPA model using cos^2(angle) scaling.
    Only the normal component of neutron momentum contributes to
    PKA energy transfer. angle_deg is measured from the surface
    normal (0 = head-on, 90 = grazing).
    No /2 division — cos^2(angle) replaces isotropic averaging.
    """
    m_n = 1.0
    T_max_eV = 4*m_n*A_target/(m_n+A_target)**2 * E_neutron_MeV * 1e6
    cos2 = np.cos(np.radians(angle_deg)) ** 2
    T_pka_eV = T_max_eV * cos2
    if T_pka_eV < Ed_eV:      return 0.0
    elif T_pka_eV < 2*Ed_eV:  return 1.0
    else:                      return 0.8 * T_pka_eV / (2*Ed_eV)

def torus_surface_area_cm2(stl_path):
    """
    Compute torus outer surface area from STL vertex coordinates.
    Reads max XY and max Z from the STL to extract R and a_out.
    Surface area of torus = (2*pi*R) * (2*pi*a_out)
    Returns area in cm^2.
    """
    max_xy = -np.inf
    max_z  = -np.inf
    try:
        with open(stl_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('vertex'):
                    parts = line.split()
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    rho = np.sqrt(x*x + y*y)
                    if rho  > max_xy: max_xy = rho
                    if z    > max_z:  max_z  = z
        a_out_mm = max_z
        R_mm     = max_xy - a_out_mm
        area_mm2 = (2 * np.pi * R_mm) * (2 * np.pi * a_out_mm)
        area_cm2 = area_mm2 / 100.0   # mm^2 -> cm^2
        print(f"  STL geometry: R = {R_mm:.1f} mm, a_out = {a_out_mm:.1f} mm")
        print(f"  Torus outer surface area = {area_cm2:.2f} cm²")
        return area_cm2, R_mm, a_out_mm
    except Exception as e:
        print(f"  WARNING: Could not read STL for surface area: {e}")
        print(f"  Using fallback area = 1.0 cm² (relative flux only)")
        return 1.0, None, None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--material', default='tungsten', choices=MATERIALS.keys())
    parser.add_argument('--fluence', type=float, default=1e22)
    parser.add_argument('--dir', default='.')
    parser.add_argument('--stl', default=None,
                        help='Path to STL file for surface area calculation')
    args = parser.parse_args()

    mat = MATERIALS[args.material]
    Ed, A = mat['Ed_eV'], mat['A']

    
    dfs = []
    for mode in ['DT', 'TD']:
        path = os.path.join(args.dir, f"neutron_hits_{mode}_nt_Hits.csv")
        if os.path.exists(path):
            df = pd.read_csv(path, comment="#",
                             names=["Energy_MeV","Angle_deg","X_mm","Y_mm","Z_mm","EventID"])
            df.columns = df.columns.str.strip()
            df['mode'] = mode
            dfs.append(df)
            print(f"  Successfully loaded: {path}")
        else:
            print(f"  WARNING: {path} not found, skipping.")

    if not dfs:
        print("Error: No data files (.csv) found in the build directory!")
        return

    combined   = pd.concat(dfs, ignore_index=True)
    energies   = combined['Energy_MeV'].values
    angles     = combined['Angle_deg'].values
    n_sim_total = len(combined)

    # angle-independent DPA
    disps = np.array([nrt_dpa(e, A, Ed) for e in energies])

    # angle-dependent DPA (cos^2 model)
    disps_angle = np.array([nrt_dpa_angle(e, A, Ed, a)
                            for e, a in zip(energies, angles)])

    # physical DPA
    Na        = 6.022e23
    rho_kg_m3 = mat['density'] * 1000
    A_kg_mol  = mat['A'] * 1e-3
    n_surface = (rho_kg_m3 * Na / A_kg_mol) * 0.05
    dpa_phys  = (disps.sum() / len(combined)) * (args.fluence / n_surface)
    mean_angle = angles.mean()

    # surface area from STL
    stl_path = args.stl
    if stl_path is None:
        for candidate in ['geometry/grooves_10_ascii.stl',
                          'geometry/grooved_torus_ascii.stl']:
            full = os.path.join(args.dir, candidate)
            if os.path.exists(full):
                stl_path = full
                break
    area_cm2, R_mm, a_out_mm = torus_surface_area_cm2(stl_path) \
        if stl_path and os.path.exists(stl_path) \
        else (1.0, None, None)

    print(f"\n{'='*50}")
    print(f"  Material: {args.material} ({mat['symbol']}), Ed={Ed} eV")
    print(f"{'='*50}")
    print(f"  Total hits (DT+TD combined): {n_sim_total}")
    print(f"  Mean energy:                 {energies.mean():.3f} MeV")
    print(f"  Mean angle of incidence:     {mean_angle:.2f}°")
    print(f"  Fraction >70° glancing:      {(angles>70).mean()*100:.1f}%")
    print(f"  Physical DPA:                {dpa_phys:.6f}")

    
    angle_bins  = np.linspace(0, 90, 91)
    bin_centers = 0.5 * (angle_bins[:-1] + angle_bins[1:])

    # angle-independent DPA per angle bin
    dpa_per_angle = []
    for i in range(len(angle_bins)-1):
        mask = (angles >= angle_bins[i]) & (angles < angle_bins[i+1])
        dpa_per_angle.append(disps[mask].mean() if mask.sum() > 0 else np.nan)
    dpa_per_angle = np.array(dpa_per_angle)

    # angle-dependent DPA per angle bin
    dpa_angle_per_bin = []
    for i in range(len(angle_bins)-1):
        mask = (angles >= angle_bins[i]) & (angles < angle_bins[i+1])
        dpa_angle_per_bin.append(disps_angle[mask].mean() if mask.sum() > 0 else np.nan)
    dpa_angle_per_bin = np.array(dpa_angle_per_bin)

    # neutron flux per angle bin
    hits_per_bin = np.array([
        ((angles >= angle_bins[i]) & (angles < angle_bins[i+1])).sum()
        for i in range(len(angle_bins)-1)
    ], dtype=float)
    flux_per_bin = (hits_per_bin / n_sim_total) * SOURCE_STRENGTH_N_PER_S / area_cm2

   
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle(f'Neutron Wall Analysis — {args.material.capitalize()} '
                 f'(Ed={Ed} eV)\nCumulative D-T + T-D Anisotropic Source '
                 f'| Total hits: {n_sim_total:,}', fontsize=13)

    # energy spectrum
    ax = axes[0, 0]
    ax.hist(energies, bins=60, color='steelblue', edgecolor='none',
            alpha=0.8, density=True)
    ax.axvline(14.1, color='red', linestyle='--', linewidth=1.5,
               label='14.1 MeV source')
    ax.axvline(energies.mean(), color='navy', linestyle='-', linewidth=1.5,
               label=f'Mean = {energies.mean():.2f} MeV')
    ax.set_xlabel('Neutron Energy (MeV)')
    ax.set_ylabel('Normalized Frequency')
    ax.set_title('Energy Spectrum at Wall')
    ax.legend(fontsize=9)

    # angle distribution
    ax = axes[0, 1]
    ax.hist(angles, bins=45, range=(0, 90), color='coral',
            edgecolor='none', alpha=0.8, density=True)
    ax.axvline(mean_angle, color='navy', linestyle='--', linewidth=2,
               label=f'Mean = {mean_angle:.1f}°')
    ax.set_xlabel('Angle of Incidence (degrees)')
    ax.set_ylabel('Normalized Frequency')
    ax.set_title('Angle of Incidence Distribution')
    ax.legend(fontsize=10)

    # DPA against angle
    ax = axes[0, 2]
    valid = ~np.isnan(dpa_per_angle)
    ax.plot(bin_centers[valid], dpa_per_angle[valid],
            color='seagreen', linewidth=1.5, alpha=0.4, label='Raw (1° bins)')
    smoothed = pd.Series(dpa_per_angle).rolling(5, center=True,
                                                  min_periods=1).mean().values
    ax.plot(bin_centers, smoothed, color='darkgreen', linewidth=2.5,
            label='Smoothed (5° window)')
    ax.axvline(mean_angle, color='navy', linestyle='--', linewidth=1.5,
               label=f'Mean angle = {mean_angle:.1f}°')
    ax.set_xlabel('Angle of Incidence (degrees)')
    ax.set_ylabel('Mean NRT Displacements per Hit')
    ax.set_title('DPA vs Angle of Incidence\n(dependent on neutron hits)')
    ax.legend(fontsize=9)
    ax.set_xlim(0, 90)

    # spatial hit map
    ax = axes[1, 0]
    sc = ax.scatter(combined['X_mm'], combined['Y_mm'],
                    c=angles, cmap='plasma', s=0.4, alpha=0.3)
    plt.colorbar(sc, ax=ax, label='Angle of Incidence (°)')
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.set_title('Hit Map (coloured by angle of incidence)')
    ax.set_aspect('equal')

    # 5 angle-dependent cos^2 model
    ax = axes[1, 1]
    valid2 = ~np.isnan(dpa_angle_per_bin)
    ax.plot(bin_centers[valid2], dpa_angle_per_bin[valid2],
            color='darkorange', linewidth=1.5, alpha=0.4, label='Raw (1° bins)')
    smoothed2 = pd.Series(dpa_angle_per_bin).rolling(5, center=True,
                                                       min_periods=1).mean().values
    ax.plot(bin_centers, smoothed2, color='red', linewidth=2.5,
            label='Smoothed (5° window)')
    ax.axvline(mean_angle, color='navy', linestyle='--', linewidth=1.5,
               label=f'Mean angle = {mean_angle:.1f}°')
    ax.set_xlabel('Angle of Incidence (degrees)')
    ax.set_ylabel('Mean Angle-Weighted DPA per Hit')
    ax.set_title('Angle-Dependent DPA vs Angle\n(cos² model, no hit-count bias)')
    ax.legend(fontsize=9)
    ax.set_xlim(0, 90)

    # neutron flux against angle
    ax = axes[1, 2]
    ax.bar(bin_centers, flux_per_bin, width=1.0,
           color='mediumpurple', alpha=0.7, label='Flux per 1° bin')
    flux_smoothed = pd.Series(flux_per_bin).rolling(5, center=True,
                                                      min_periods=1).mean().values
    ax.plot(bin_centers, flux_smoothed, color='indigo', linewidth=2.5,
            label='Smoothed (5° window)')
    ax.axvline(mean_angle, color='navy', linestyle='--', linewidth=1.5,
               label=f'Mean angle = {mean_angle:.1f}°')
    ax.set_xlabel('Angle of Incidence (degrees)')
    flux_label = 'Neutron Flux (n/cm²/s)' if area_cm2 != 1.0 \
                 else 'Relative Neutron Flux (n/cm²/s, area=1)'
    ax.set_ylabel(flux_label)
    geo_info = f'R={R_mm:.0f}mm, a={a_out_mm:.0f}mm' \
               if R_mm is not None else 'geometry unknown'
    ax.set_title(f'Neutron Flux vs Angle of Incidence\n'
                 f'(Source={SOURCE_STRENGTH_N_PER_S:.0e} n/s, {geo_info})')
    ax.legend(fontsize=9)
    ax.set_xlim(0, 90)

    plt.tight_layout()
    outfile = f'dpa_analysis_{args.material}.png'
    plt.savefig(outfile, dpi=150, bbox_inches='tight')
    print(f"  Plot saved to: {outfile}\n")

if __name__ == '__main__':
    main()