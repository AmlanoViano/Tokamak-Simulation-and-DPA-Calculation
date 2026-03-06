#pragma once
#include "G4UserRunAction.hh"
#include "G4String.hh"

class G4Run;

class RunAction : public G4UserRunAction {
public:
    RunAction(const G4String& mode = "DT");
    ~RunAction() override = default;

    void BeginOfRunAction(const G4Run*) override;
    void EndOfRunAction(const G4Run*) override;

private:
    G4String fMode;
};
