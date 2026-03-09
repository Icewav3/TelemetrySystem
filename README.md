### Todo:

- [ ] Component refactor
    - [x] C++ implementation (get working)
    - [x] Blueprint implementation (working)
    - [ ] C++ implementation (polish pass)
    - [ ] Testing and ensuring no edge cases
- [ ] Resolve issue with subscribing to cates damage system

#### Cleaning
- [ ] Remove unused now redudant blueprint library functions that will be taken over by the new component.

#### JSON schema issues:

###### Replace in dataset
- [ ] "death" --> "respawn"
- [ ] "framecount" --> "event_order"

###### Additions
- [ ] "current_framerate" : int
- [ ] "current_room" : string

#### Marimo Visualization issues:
###### Replacements
- [ ] change framecount to event_order
- [ ] exclude PIE data

#### Features:
- [ ] Room logging
    - [ ] Test locally
    - [ ] Update JSON schema
- [ ] PIE (play in editor) awareness
    - [ ] Test locally
    - [ ] Update JSON schema
- [ ] Kyle hoping for framerate logging
- [ ] Collect info on weapons used/interacted with
- [ ] Collect first interactions (e.g. first attack, first jump)

#### Networking:
- Aiden has the domain IronRise - could potentially host endpoint to reroute data via that.
### Notes
 - for playtests could potentially connect demo pcs to my laptop via VPN network to allow data collection.
    - Aiden has a domnain I can use
