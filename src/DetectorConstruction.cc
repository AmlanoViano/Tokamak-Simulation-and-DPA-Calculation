#include "DetectorConstruction.hh"

#include "G4Material.hh"
#include "G4NistManager.hh"
#include "G4Box.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4SystemOfUnits.hh"
#include "G4VisAttributes.hh"
#include "G4Colour.hh"
#include "G4Element.hh"
#include "G4TessellatedSolid.hh"
#include "CADMesh.hh"

DetectorConstruction::DetectorConstruction(G4String cadFile, G4String wallMaterial)
    : fCADFile(cadFile), fWallMaterial(wallMaterial), fTorusLogical(nullptr) {}

G4VPhysicalVolume* DetectorConstruction::Construct() {
    auto nist = G4NistManager::Instance();

    // world
    auto worldMat = nist->FindOrBuildMaterial("G4_Galactic");
    auto worldBox = new G4Box("World", 1000*mm, 1000*mm, 1000*mm);;
    auto worldLog = new G4LogicalVolume(worldBox, worldMat, "World");
    worldLog->SetVisAttributes(G4VisAttributes::GetInvisible());
    auto worldPhys = new G4PVPlacement(nullptr, G4ThreeVector(), worldLog,
                                       "World", nullptr, false, 0, true);

    // wall material
    G4Material* wallMat = nullptr;
    if (fWallMaterial == "tungsten")
        wallMat = nist->FindOrBuildMaterial("G4_W");
    else if (fWallMaterial == "steel")
        wallMat = nist->FindOrBuildMaterial("G4_STAINLESS-STEEL");
    else if (fWallMaterial == "beryllium")
        wallMat = nist->FindOrBuildMaterial("G4_Be");
    else if (fWallMaterial == "SiC") {
        auto Si = nist->FindOrBuildElement("Si");
        auto C  = nist->FindOrBuildElement("C");
        wallMat = new G4Material("SiliconCarbide", 3.21*g/cm3, 2);
        wallMat->AddElement(Si, 1);
        wallMat->AddElement(C,  1);
    } else if (fWallMaterial == "RAFM") {
        auto Fe = nist->FindOrBuildElement("Fe");
        auto Cr = nist->FindOrBuildElement("Cr");
        auto W  = nist->FindOrBuildElement("W");
        auto V  = nist->FindOrBuildElement("V");
        auto Ta = nist->FindOrBuildElement("Ta");
        wallMat = new G4Material("RAFM_Steel", 7.7*g/cm3, 5);
        wallMat->AddElement(Fe, 0.883);
        wallMat->AddElement(Cr, 0.090);
        wallMat->AddElement(W,  0.011);
        wallMat->AddElement(V,  0.002);
        wallMat->AddElement(Ta, 0.001);
    } else
        wallMat = nist->FindOrBuildMaterial("G4_W");

    G4cout << ">> Wall material : " << wallMat->GetName() << G4endl;
    G4cout << ">> Loading STL   : " << fCADFile << G4endl;

    // load STL
    auto mesh = CADMesh::TessellatedMesh::FromSTL(fCADFile);
    mesh->SetScale(mm);

    auto solid = mesh->GetSolid();
    fTorusLogical = new G4LogicalVolume(solid, wallMat, "TorusWallLog");

    auto wallVis = new G4VisAttributes(G4Colour(0.2, 0.4, 0.9, 0.5));
    wallVis->SetForceSolid(true);
    fTorusLogical->SetVisAttributes(wallVis);

    new G4PVPlacement(nullptr, G4ThreeVector(), fTorusLogical,
                      "TorusWallPhys", worldLog, false, 0, true);

    G4cout << ">> Geometry loaded successfully." << G4endl;
    return worldPhys;
}
