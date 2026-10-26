# Recorded verification - working model stage

This record corresponds to initial implementation of the six-view Python project. It does **not** claim that a user has tested the Streamlit front-end on their computer.

| Scenario | Source → destination | Expected outcome | Computed outcome | Check |
|---|---|---|---|---|
| Baseline | A → F | A-C-E-F, cost 2 + 3 + 7 = 12 | A-C-E-F, cost 12, 3 hops, 13 illustrative ms | Pass |
| Increase E-F routing cost to 20 | A → F | Reroute A-C-E-D-F, cost 2 + 3 + 4 + 11 = 20 | A-C-E-D-F, cost 20, 4 hops, 22 illustrative ms | Pass |
| Disable link E-F | A → F | New path A-C-E-D-F, cost 20 | A-C-E-D-F, cost 20 | Pass |
| Disable links A-B and A-C | A → F | No route available | Unreachable, `cost=None` | Pass |
| Same source and destination | C → C | C, cost 0, 0 hops | C, cost 0, 0 hops | Pass |
| Invalid missing cost | N/A | Reject invalid input rather than fill missing value | `ValueError` | Pass |
| Negative link cost | N/A | Reject invalid cost | `ValueError` | Pass |

**Independent computational verification:** the custom Dijkstra step logger's route cost was compared against `nx.dijkstra_path_length` for **every one of 6 × 6 ordered endpoint pairs across four scenarios** (144 independent route-cost/reachability checks). Additionally, each selected path's link costs are directly summed and must match the reported cost.

**Automated suite:** `python -m pytest -q` -> **13 passed**, including Plotly chart/animation serialization tests. These checks were run in the development environment; Streamlit package could not be fetched there because its package server was inaccessible, so a live graphical browser test remains necessary.

## Before final submission

1. Install the required packages locally with the commands in `START_HERE.txt`.
2. Open all six tabs and exercise their controls in a live browser.
3. Capture a labeled screenshot of every view and at least one changed-route scenario; record what settings were shown.
4. Ask classmates for actual usability feedback and document any corrections made.
5. Generate the concise IEEE-format midterm PDF with required sections and source, run and deployment links.
6. Rehearse the 15-minute live presentation and its audience question.