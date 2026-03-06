#include "RunAction.hh"
#include "G4AnalysisManager.hh"
#include "G4Run.hh"

RunAction::RunAction(const G4String& mode) : fMode(mode) {
    auto analysisManager = G4AnalysisManager::Instance();
    analysisManager->SetVerboseLevel(1);
    analysisManager->SetDefaultFileType("csv");
    analysisManager->SetNtupleMerging(true); 
}

void RunAction::BeginOfRunAction(const G4Run*) {
    auto analysisManager = G4AnalysisManager::Instance();
    G4String fileName = "neutron_hits_" + fMode + ".csv";
    analysisManager->OpenFile(fileName); // creates neutron_hits_DT.csv

    analysisManager->CreateNtuple("Hits", "Neutron Wall Hits");
    analysisManager->CreateNtupleDColumn("Energy_MeV");
    analysisManager->CreateNtupleDColumn("Angle_deg");
    analysisManager->CreateNtupleDColumn("X_mm");
    analysisManager->CreateNtupleDColumn("Y_mm");
    analysisManager->CreateNtupleDColumn("Z_mm");
    analysisManager->CreateNtupleIColumn("EventID");
    analysisManager->FinishNtuple();
}

void RunAction::EndOfRunAction(const G4Run*) {
    auto analysisManager = G4AnalysisManager::Instance();
    analysisManager->Write();
    analysisManager->CloseFile();
}
