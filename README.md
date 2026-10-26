# Packet Path Lab — CPS 5745 Midterm

An interactive Streamlit teaching application demonstrating shortest-path routing, cost adjustments, packet animation, Dijkstra stepping, failure-driven rerouting, and scenario comparisons in a **synthetic** six-router network.

## Deploy online with Streamlit Community Cloud

1. Download `Packet_Path_Lab_Streamlit_Deploy.zip` and **extract it**. You should see `app.py` and `requirements.txt` directly inside the extracted folder.
2. Create a repository at https://github.com/new (for example, `packet-path-lab`). A public repository is easiest to share with your professor. Do not upload your `.venv` folder or any secrets.
3. In your new repository, choose **Add file → Upload files**. Drag in the **contents** of the extracted folder, including `data`, `tests`, `docs`, and `.streamlit`, so that **`app.py` and `requirements.txt` are at the repository root**. Commit the files. GitHub's browser upload supports dragging a folder's contents; if hidden `.streamlit` is skipped, add it separately or deploy without the optional theme config.
4. Go to https://share.streamlit.io , sign in using GitHub, and choose **Create app → Yup, I have an app**.
5. Select the new GitHub repository and branch `main`. Set **Main file path** to `app.py`.
6. In **Advanced settings**, select Python **3.12** (matching local development). No secrets are required.
7. Click **Deploy**. When the app loads, verify View 1 and test **E–F cost = 20**, **E–F link failure**, and the **A disconnected** preset.
8. Copy the resulting `https://<your-app>.streamlit.app/` link into your IEEE report and class submission.

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