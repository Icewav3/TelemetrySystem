### Todo:

- [x] Component refactor
    - [x] C++ implementation (get working)
    - [x] Blueprint implementation (working)
    - [x] C++ implementation (polish pass)
    - [x] Testing and ensuring no edge cases
- [x] Resolve issue with subscribing to cates damage system

### Bugs:

- [ ] Currently some weirdness with runs not properly ending.
    - [ ] I suspect this has to do with the way respawn events are called.
    - [ ] Damage events failing?

#### Cleaning

- [x] Remove unused now redudant blueprint library functions that will be taken over by the new component.

#### JSON schema issues:

###### Replace in dataset

- [ ] "death" --> "respawn"
- [ ] "framecount" --> "event_order"

###### Additions

- [x] "current_framerate" : int
- [ ] "current_room" : string

#### Marimo Visualization issues:

###### Replacements

- [ ] change framecount to event_order

###### Additions

- [ ] Improve metadata system
    - [ ] change from setting massive bounds if undefined in metadata to instead use boundless
- [ ] Exclude PIE data

###### Major Features

- [x] Split notebooks (or see if we can make them cleanly seperate without fresh runs)
    - [x] Debugging notebook (internal use)

      - [STATUS] Currently in a very rough state, duplicate info from main notebook
    - [x] ~~Annotation notebook (for manual data cleaning)~~ → merged to debug notebook 

- 
- [ ] Main visualization notebook (only pretty graphs, nothing technical)

#### C++ Telemetry Features:

- [ ] Room logging
    - [ ] Test locally
    - [x] Update JSON schema
- [x] PIE (play in editor) awareness
    - [x] Test locally
    - [x] Update JSON schema
- [ ] Kyle hoping for framerate logging
- [ ] Collect info on weapons used/interacted with
- [ ] Collect first interactions (e.g. first attack, first jump)
- [ ] In engine visualization

#### Networking:

- Aiden has the domain IronRise - could potentially host endpoint to reroute data via that.

### Notes

- for playtests could potentially connect demo pcs to my laptop via VPN network to allow data collection.
    - Aiden has a domnain I can use