# Tokamak Simulation and DPA Calculation
This simulation is based on Geant4, using C++ and Python to simulate neutron beams within a tokamak reactor using an anisotropic source, and calculating Displacement per atom (DPA) for different wall geometries (corrugated and grooved). The aim is to see how angle of incidence of the beam on the reactor wall varies for different geometries and affects DPA. The torus CAD models are loaded using CADMesh.

## Neutron Source: D-T Fusion Plasma

The neutron source simulates plasma within a magnetically confined fusion reactor. 
Neutron birth positions are determined via rejection sampling inside a toroidal plasma 
volume with major radius $R = 500$ mm and minor radius $f_a = 18$ mm. A point 
$(x, y, z)$ is randomly drawn from the bounding box and retained only if it falls 
within the torus boundary:

$$\left(\sqrt{x^2 + y^2} - R\right)^2 + z^2 < f_a^2$$

Emission directions are determined by sampling from the anisotropic D-T angular 
distribution via rejection sampling. The underlying probability distribution is 
expressed as a Legendre polynomial expansion:

$$W(\theta) = 1 + a_2 P_2(\cos\theta) + a_4 P_4(\cos\theta)$$

where the Legendre polynomials take the form:

$$P_2(\cos\theta) = \frac{1}{2}\left(3\cos^2\theta - 1\right)$$

$$P_4(\cos\theta) = \frac{1}{8}\left(35\cos^4\theta - 30\cos^2\theta + 3\right)$$

The expansion coefficients are $a_2 = 0.4456$ and $a_4 = 0.0066$. For T-D runs, 
the angular distribution is reflected via $\cos\theta \rightarrow -\cos\theta$. 
Both D-T and T-D simulations (200,000 events combined) are subsequently merged 
during post-processing to reconstruct a symmetric plasma source.

## Neutron Transport in Geant4
The `QGSP_BIC_HP` physics list is employed, using the following components:

- **High-precision neutron transport** (`G4NeutronHPElastic`, `G4NeutronHPInelastic`)
  using evaluated nuclear data from ENDF/B-VII for neutron energies up to 20 MeV.
  
- **Standard electromagnetic physics** to account for secondary particle behaviour.

Each neutron is propagated, with Geant4 computing cross-sections at every step across all relevant interaction channel and randomly selecting the interaction using the 
Monte Carlo method.

## Surface Normal and Angle of Incidence

When a neutron crosses into the wall volume, the angle of incidence $\theta$ is 
calculated in `SteppingAction.cc`. The surface normal $\hat{n}$ at the hit point 
is retrieved directly from the tessellated STL geometry using the Geant4 navigator:
```
G4Navigator::GetLocalExitNormal()
```

This queries the actual STL triangle facet normal at the boundary crossing point, 
transformed from local to global coordinates via:

$$\hat{n}_{\text{global}} = \mathbf{T}^{-1} \hat{n}_{\text{local}}$$

where $\mathbf{T}$ is the transformation matrix from the touchable history. The 
normal is oriented outward by checking $\hat{n} \cdot (-\hat{d}) < 0$. The angle 
of incidence is measured from the surface normal ($0°$ = head-on, $90°$ = grazing):

$$\theta = \cos^{-1}\left(\left|\hat{d} \cdot (-\hat{n})\right|\right)$$

where $\hat{d}$ is the neutron unit direction vector. The absolute value is to ensure that $\theta \in [0°, 90°]$ regardless of which side of the surface is crossed.

## Data Recording

For each neutron entering the wall, the following quantities are recorded to CSV 
via the Geant4 analysis manager (`G4AnalysisManager`):

| Column | Description |
|--------|-------------|
| `Energy_MeV` | Kinetic energy at wall entry (MeV) |
| `Angle_deg` | Angle of incidence from surface normal (degrees) |
| `X_mm, Y_mm, Z_mm` | 3D position of wall hit (mm) |
| `EventID` | Geant4 event identifier |

Each of the threads used writes its own file (`neutron_hits_DT_nt_Hits_t0.csv` ... 
`t11.csv`). These are merged in post-processing. Two separate runs are performed - 
one for the D-T source and one for the T-D source - giving 200,000 total events combined.

The neutron flux per 1-degree angle bin is:

$$\phi(\theta) = \frac{N_{\text{hits}}(\theta)}{N_{\text{simulated}}} \cdot \frac{S_{\text{source}}}{A_{\text{wall}}}$$

where $S_{\text{source}} = 10^{20}$ n/s is the ITER-equivalent neutron source strength 
($\approx 500$ MW fusion power), and $A_{\text{wall}}$ is the torus outer surface area 
computed automatically from the STL vertex coordinates:

$$A_{\text{wall}} = (2\pi R)(2\pi a_{\text{out}})$$

## Simulation Pipeline Summary

The simulation has been completely summarised below:

| Stage | Component | Output |
|-------|-----------|--------|
| 1. Source generation | `PrimaryGeneratorAction` | 14.1 MeV neutrons from D-T plasma |
| 2. Particle transport | Geant4 `QGSP_BIC_HP` | Full neutron tracking with physics |
| 3. Wall hit recording | `SteppingAction` | $E_n$, $\theta$, $(x, y, z)$ per neutron |
| 4. Data output | `G4AnalysisManager` ($\times 12$) | CSV files, 12 threads merged |
| 5. DPA analysis | `dpa_analysis.py` | NRT + $\cos^2$ DPA per material |
| 6. Results | `matplotlib` plots | Angle dist., DPA, flux, hit map |
