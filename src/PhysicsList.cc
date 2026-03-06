#include "PhysicsList.hh"

#include "G4EmStandardPhysics.hh"
#include "G4DecayPhysics.hh"
#include "G4RadioactiveDecayPhysics.hh"
#include "G4HadronPhysicsQGSP_BIC_HP.hh"
#include "G4HadronElasticPhysicsHP.hh"
#include "G4StoppingPhysics.hh"
#include "G4IonPhysics.hh"
#include "G4NeutronTrackingCut.hh"
#include "G4SystemOfUnits.hh"

PhysicsList::PhysicsList() : G4VModularPhysicsList() {
    SetVerboseLevel(0);

    // electromagnetic
    RegisterPhysics(new G4EmStandardPhysics());

    // decays
    RegisterPhysics(new G4DecayPhysics());
    RegisterPhysics(new G4RadioactiveDecayPhysics());

    // hadronic: QGSP_BIC_HP 
    RegisterPhysics(new G4HadronPhysicsQGSP_BIC_HP());

    // HP elastic scattering
    RegisterPhysics(new G4HadronElasticPhysicsHP());

    // ion recoil physics 
    RegisterPhysics(new G4IonPhysics());

    // stopping physics for slow ions
    RegisterPhysics(new G4StoppingPhysics());

    // cut thermal neutrons to prevent infinite tracking loops
    RegisterPhysics(new G4NeutronTrackingCut());
}

void PhysicsList::SetCuts() {
    SetCutsWithDefault();

    // fine production cuts for wall
    SetCutValue(0.1*mm, "proton");
    SetCutValue(0.1*mm, "e-");
    SetCutValue(0.1*mm, "e+");
    SetCutValue(0.1*mm, "gamma");

    // track neutrons as long as possible — zero cut
    SetCutValue(0.*mm, "neutron");
}
