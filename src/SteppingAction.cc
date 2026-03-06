#include "SteppingAction.hh"
#include "RunAction.hh"
#include "DetectorConstruction.hh"
#include "G4Step.hh"
#include "G4RunManager.hh"
#include "G4AnalysisManager.hh"
#include "G4TransportationManager.hh"
#include "G4Navigator.hh"
#include "G4SystemOfUnits.hh"

SteppingAction::SteppingAction(RunAction* runAction) : fRunAction(runAction) {}

void SteppingAction::UserSteppingAction(const G4Step* step) {
    auto track = step->GetTrack();

    // only care about neutrons
    if (track->GetDefinition()->GetParticleName() != "neutron") return;

    auto postPoint = step->GetPostStepPoint();

    // only care about the moment they hit the surface (Boundary)
    if (postPoint->GetStepStatus() != fGeomBoundary) return;

    auto preVol  = step->GetPreStepPoint()->GetPhysicalVolume();
    auto postVol = postPoint->GetPhysicalVolume();
    if (!preVol || !postVol) return;

    // get detector pointer to check logical volume
    auto detConst = static_cast<const DetectorConstruction*>(
        G4RunManager::GetRunManager()->GetUserDetectorConstruction());

    if (postVol->GetLogicalVolume() != detConst->GetTorusLogical()) return;

    G4double energy = step->GetPreStepPoint()->GetKineticEnergy() / MeV;
    G4ThreeVector pos = postPoint->GetPosition();
    G4ThreeVector dir = track->GetMomentumDirection();

    // calculate surface normal accurately
    G4Navigator* nav = G4TransportationManager::GetTransportationManager()->GetNavigatorForTracking();
    G4bool valid = false;
    G4ThreeVector localNorm = nav->GetLocalExitNormal(&valid);

    if(!valid) {
        auto solid = postVol->GetLogicalVolume()->GetSolid();
        G4ThreeVector localPos = postPoint->GetTouchableHandle()->GetHistory()->GetTopTransform().TransformPoint(pos);
        localNorm = solid->SurfaceNormal(localPos);
    }

    G4ThreeVector globalNorm = postPoint->GetTouchableHandle()->GetHistory()->GetTopTransform().InverseTransformAxis(localNorm).unit();

    // dot product for angle of incidence
    if (globalNorm.dot(-dir) < 0) globalNorm = -globalNorm;
    G4double cosA = std::min(1.0, std::max(-1.0, dir.dot(-globalNorm)));
    G4double angle = std::acos(cosA) * (180.0 / CLHEP::pi);

    auto analysisManager = G4AnalysisManager::Instance();
    analysisManager->FillNtupleDColumn(0, energy);
    analysisManager->FillNtupleDColumn(1, angle);
    analysisManager->FillNtupleDColumn(2, pos.x());
    analysisManager->FillNtupleDColumn(3, pos.y());
    analysisManager->FillNtupleDColumn(4, pos.z());
    analysisManager->FillNtupleIColumn(5, G4RunManager::GetRunManager()->GetCurrentEvent()->GetEventID());
    analysisManager->AddNtupleRow();
}
