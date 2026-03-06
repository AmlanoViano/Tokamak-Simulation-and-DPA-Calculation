#pragma once

#include "G4VUserDetectorConstruction.hh"
#include "G4String.hh"

class G4VPhysicalVolume;
class G4LogicalVolume;

class DetectorConstruction : public G4VUserDetectorConstruction {
public:
    DetectorConstruction(G4String cadFile, G4String wallMaterial);
    ~DetectorConstruction() override = default;

    G4VPhysicalVolume* Construct() override;

    G4LogicalVolume* GetTorusLogical() const { return fTorusLogical; }

private:
    G4String fCADFile;
    G4String fWallMaterial;
    G4LogicalVolume* fTorusLogical = nullptr;
};
