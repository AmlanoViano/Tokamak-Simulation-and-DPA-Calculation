#include "PrimaryGeneratorAction.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4SystemOfUnits.hh"
#include "G4PhysicalConstants.hh"
#include "Randomize.hh"
#include <cmath>

PrimaryGeneratorAction::PrimaryGeneratorAction()
    : fMode("isotropic") {
    fParticleGun = new G4ParticleGun(1);
    auto* table = G4ParticleTable::GetParticleTable();
    fParticleGun->SetParticleDefinition(table->FindParticle("neutron"));
    fParticleGun->SetParticleEnergy(14.1 * MeV);
}

PrimaryGeneratorAction::~PrimaryGeneratorAction() {
    delete fParticleGun;
}

G4ThreeVector PrimaryGeneratorAction::SamplePlasmaPosition() {
    // Rejection sampling inside torus plasma volume
    while (true) {
        G4double x = (2*G4UniformRand()-1) * (fR + fa) * mm;
        G4double y = (2*G4UniformRand()-1) * (fR + fa) * mm;
        G4double z = (2*G4UniformRand()-1) * fa * mm;
        G4double r = std::sqrt(x*x + y*y);
        G4double dr = r - fR*mm;
        if (dr*dr + z*z < (fa*mm)*(fa*mm))
            return G4ThreeVector(x, y, z);
    }
}

G4double PrimaryGeneratorAction::DTAngularDistribution(G4double cosTheta, bool isTD) {
    // Standard D-T anisotropy from Peres (1979) / IAEA data
    // W(theta) = 1 + a2*P2(cos theta) + a4*P4(cos theta)
    // D-T coefficients at 14.1 MeV center-of-mass
    // a2 = 0.4456, a4 = 0.0066 (from Drosg 1987)
    G4double ct = isTD ? -cosTheta : cosTheta; // T-D is mirror of D-T
    G4double P2 = 0.5*(3*ct*ct - 1);
    G4double P4 = 0.125*(35*ct*ct*ct*ct - 30*ct*ct + 3);
    G4double W  = 1.0 + 0.4456*P2 + 0.0066*P4;
    return std::max(0.0, W);
}

G4ThreeVector PrimaryGeneratorAction::SampleDirection() {
    if (fMode == "isotropic") {
        // Uniform sphere sampling
        G4double cosTheta = 2*G4UniformRand() - 1;
        G4double sinTheta = std::sqrt(1 - cosTheta*cosTheta);
        G4double phi      = 2*CLHEP::pi*G4UniformRand();
        return G4ThreeVector(sinTheta*std::cos(phi),
                             sinTheta*std::sin(phi),
                             cosTheta);
    }

    // Rejection sampling for anisotropic distribution
    bool isTD = (fMode == "TD");
    G4double Wmax = 1.0 + 0.4456*0.5*(3-1) + 0.0066*0.125*(35-30+3); // W at cos=1
    Wmax = DTAngularDistribution(1.0, false); // max at cos=1 for DT, cos=-1 for TD

    while (true) {
        G4double cosTheta = 2*G4UniformRand() - 1;
        G4double W        = DTAngularDistribution(cosTheta, isTD);
        if (G4UniformRand() * Wmax < W) {
            G4double sinTheta = std::sqrt(std::max(0.0, 1-cosTheta*cosTheta));
            G4double phi      = 2*CLHEP::pi*G4UniformRand();
            return G4ThreeVector(sinTheta*std::cos(phi),
                                 sinTheta*std::sin(phi),
                                 cosTheta);
        }
    }
}

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event) {
    G4ThreeVector pos = SamplePlasmaPosition();
    G4ThreeVector dir = SampleDirection();

    fParticleGun->SetParticlePosition(pos);
    fParticleGun->SetParticleMomentumDirection(dir);
    fParticleGun->GeneratePrimaryVertex(event);
}
