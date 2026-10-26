# Packet Path Lab — CPS 5745 Midterm

An interactive Streamlit teaching application demonstrating shortest-path routing, cost adjustments, packet animation, Dijkstra stepping, failure-driven rerouting, and scenario comparisons in a **synthetic** six-router network.

## Deploy online with Streamlit Community Cloud

The complete deployable application is already uploaded to the public GitHub repository:
https://github.com/Youssefali908/packet-path-lab

1. Open https://share.streamlit.io and sign in using your GitHub account.
2. Choose **Create app** (or **New app**) and select the existing repository `Youssefali908/packet-path-lab`.
3. Choose branch `main` and main file path `app.py`.
4. Under advanced settings, select Python **3.12**. No secrets are required.
5. Click **Deploy**, then test the network map, packet controls, E–F cost adjustment, link failure, and disconnected scenario.
6. Add the resulting public Streamlit URL to the final IEEE report or course submission. The app is not published on Streamlit Cloud until this step is completed.

Official guide: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy

### Files

- `app.py` — app entrypoint; six interactive views + model explanation.
- `routing_model.py` — CSV loading, graph model, route solver and independent verification.
- `visualizations.py` — Plotly plots and playback visuals.
- `data/network_edges.csv` — baseline educational network data; **required**.
- `requirements.txt` — cloud dependencies.
- `.streamlit/config.toml` — optional dark theme.
- `tests/` and `docs/` — reproducibility and test evidence; not needed for runtime.

## Run locally

On Windows PowerShell from this project directory:

```powershell
uv venv --python 3.12 .venv
uv pip install --link-mode=copy --python .venv\Scripts\python.exe -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

To run tests locally (pytest isn't a cloud runtime dependency):

```powershell
uv pip install --link-mode=copy --python .venv\Scripts\python.exe pytest
.\.venv\Scripts\python.exe -m pytest -q
```

## Scientific scope / known results

This is a deterministic, OSPF-inspired teaching **simulation**, not live Internet measurements or complete OSPF. Link cost is unitless; latency and bandwidth are illustrative. Baseline A→F route A–C–E–F costs **12**. Raising E–F cost to 20 or failing E–F changes the chosen path to A–C–E–D–F with cost **20**. Failing A–B and A–C disconnects A, correctly reporting no route. Same source and destination yields cost 0 and 0 hops. Scenario saves are held in memory per running session rather than written to a persistent database.

AI disclosure: ChatGPT assisted with implementation, visualization design, tests, debugging, and documentation. The routing model has numerical verification using NetworkX and manual browser checks on Windows. Verify the deployed version independently before class.
