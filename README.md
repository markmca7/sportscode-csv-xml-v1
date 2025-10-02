
# Sportscode CSV → XML (Distributor UI)

A simple Streamlit app to convert PerformaSports-style CSV into **Hudl Sportscode** XML.
- Robust CSV reader (handles rows with more fields than headers)
- Compose time from **Mins + Secs + Frames** (FPS configurable)
- **Global manual offset** (e.g., `4:36`) shifts **all events later**
- **15s pre/post** (configurable) around each event
- Builds `<ROWS>` palette from `Colormark` hex; defaults to grey when missing
- Lets you map columns via dropdowns

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown in the terminal.

## Client handoff options
- **Zip these 3 files (app.py, requirements.txt, README.md)** and share.
- Host for clients (e.g., Streamlit Community Cloud or your own server).
- If you need a desktop EXE without Python, consider a Tkinter build; I can provide one on request.
