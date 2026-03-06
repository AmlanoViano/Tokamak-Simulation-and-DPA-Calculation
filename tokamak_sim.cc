#include "DetectorConstruction.hh"
#include "PhysicsList.hh"
#include "ActionInitialization.hh"
#include "PrimaryGeneratorAction.hh"

#include "G4RunManagerFactory.hh"
#include "G4UImanager.hh"
#include "G4VisExecutive.hh"
#include "G4UIExecutive.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"
#include <iostream>

int main(int argc, char** argv) {
    if (argc < 3) {
        G4cerr << "Usage: " << argv[0]
               << " <stl_file> <DT|TD> [macro]" << G4endl;
        return 1;
    }

    G4String stlFile = argv[1];
    G4String mode    = argv[2];
    G4String macro   = (argc >= 4) ? argv[3] : "";

    G4cout << ">> STL file  : " << stlFile << G4endl;
    G4cout << ">> Mode      : " << mode    << G4endl;

    auto* runManager = G4RunManagerFactory::CreateRunManager(
        G4RunManagerType::Default);
    runManager->SetNumberOfThreads(12);

    runManager->SetUserInitialization(
        new DetectorConstruction(stlFile, "tungsten"));
    runManager->SetUserInitialization(new PhysicsList());
    runManager->SetUserInitialization(new ActionInitialization(mode));

    G4VisManager* visManager = new G4VisExecutive;
    visManager->Initialize();

    G4UImanager* UI = G4UImanager::GetUIpointer();

    if (macro.empty()) {
        G4UIExecutive* uiExec = new G4UIExecutive(argc, argv);
        UI->ApplyCommand("/control/execute macros/vis.mac");
        uiExec->SessionStart();
        delete uiExec;
    } else {
        UI->ApplyCommand("/control/execute " + macro);
    }

    delete visManager;
    delete runManager;
    return 0;
}
