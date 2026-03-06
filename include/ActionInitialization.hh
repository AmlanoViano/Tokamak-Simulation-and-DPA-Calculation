#pragma once
#include "G4VUserActionInitialization.hh"
#include "G4String.hh"

class ActionInitialization : public G4VUserActionInitialization {
public:
    ActionInitialization(const G4String& mode = "isotropic");
    void BuildForMaster() const override;
    void Build() const override;
private:
    G4String fMode;
};
