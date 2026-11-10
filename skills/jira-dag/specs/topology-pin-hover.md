# Topologies: hover and pin (characterisation of current behaviour)

Anchors: P6, D8, D9. These describe what the page does today; they exist to protect it during the refactor.
Browser scenarios run against a synthetic page that has at least two PODs, an interface band and an external issue.

- **S-pin-1** *(P6)* Given the page at rest, when I hover an epic, then every box and line outside its chain is dimmed or hidden, and moving the mouse away restores all.
- **S-pin-2** *(P6, D8)* Given nothing pinned, when I shift-click an epic, then only it and its direct neighbours are shown, empty bands collapse, and lines between hidden boxes are gone.
- **S-pin-3** *(D8)* Given one pinned epic, when I pin a second, then both and their direct neighbours are shown.
- **S-pin-4** *(D8)* Given a pin with Direct depth, when I choose Full chain, then the whole upstream and downstream chain is shown; choosing Direct returns to neighbours.
- **S-pin-5** *(P6)* Given pins, when I unpin the last one (✕, Unpin all or Esc), then every box is shown at its original position and none is dimmed.
- **S-pin-6** *(P6)* Given a hover is active under the mouse, when I pin or unpin, then no stale dimming remains.
- **S-pin-7** *(D9)* Given pins and depth, then the URL hash holds them (`pin=A,B&depth=full`), and loading that URL restores the same view.
- **S-pin-8** *(P6)* Given no pins, then box positions equal the server-rendered layout exactly.
- **S-pin-9** *(P6)* Given an epic card, when it can be pinned, then the card offers Pin or Unpin and the action matches the pin state.
