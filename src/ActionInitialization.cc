#include "ActionInitialization.hh"
#include "PrimaryGeneratorAction.hh"
#include "RunAction.hh"
#include "EventAction.hh"
#include "SteppingAction.hh"

ActionInitialization::ActionInitialization(const G4String& mode)
    : fMode(mode) {}

void ActionInitialization::BuildForMaster() const {
    SetUserAction(new RunAction(fMode));
}

void ActionInitialization::Build() const {
    auto* primary = new PrimaryGeneratorAction();
    primary->SetSourceMode(fMode);
    SetUserAction(primary);
    auto* runAction = new RunAction(fMode);
    SetUserAction(runAction);
    SetUserAction(new EventAction());
    SetUserAction(new SteppingAction(runAction));
}
