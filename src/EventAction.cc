#include "EventAction.hh"
#include "G4Event.hh"
#include "G4RunManager.hh"

void EventAction::BeginOfEventAction(const G4Event*) {}

void EventAction::EndOfEventAction(const G4Event* event) {
    // Print progress every 1000 events
    G4int evtID = event->GetEventID();
    if (evtID % 1000 == 0) {
        G4cout << "  >> Event " << evtID << G4endl;
    }
}
