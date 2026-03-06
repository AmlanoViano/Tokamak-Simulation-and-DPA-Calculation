#pragma once
#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4ParticleGun.hh"
#include "G4String.hh"

class G4Event;

class PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction {
public:
    PrimaryGeneratorAction();
    ~PrimaryGeneratorAction() override;
    void GeneratePrimaries(G4Event* event) override;
    void SetSourceMode(const G4String& mode) { fMode = mode; }
    G4String GetSourceMode() const { return fMode; }

private:
    G4ParticleGun* fParticleGun;
    G4String fMode; // "isotropic", "DT", "TD"

    // torus plasma region
    static constexpr double fR = 100.0;  // major radius mm
    static constexpr double fa = 18.0;   // plasma minor radius mm

    G4ThreeVector SamplePlasmaPosition();
    G4ThreeVector SampleDirection();
    G4double DTAngularDistribution(G4double cosTheta, bool isTD);
};
