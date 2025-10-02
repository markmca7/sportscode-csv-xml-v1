
import io
import csv
import re
import base64
from pathlib import Path
import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET

st.set_page_config(page_title="Sportscode CSV → XML", page_icon="🎥", layout="wide")

# ---------- Helpers ----------
def robust_csv_bytes(file_bytes: bytes, encoding: str = "utf-8"):
    # Read bytes into list of rows via csv.reader with error replacement
    text = file_bytes.decode(encoding=encoding, errors="replace")
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return [], []
    rows = list(reader)
    # Extend header to longest row length
    max_len = max(len(header), max((len(r) for r in rows), default=len(header)))
    if len(header) < max_len:
        header = header + [f"Extra{i}" for i in range(1, max_len - len(header) + 1)]
    # Normalize row lengths
    rows = [r + [""] * (len(header) - len(r)) for r in rows]
    return header, rows

def parse_hms_to_seconds(s: str):
    if s is None:
        return None
    s = str(s).strip()
    if not s:
        return None
    parts = s.split(":")
    try:
        if len(parts) == 1:
            return float(parts[0])
        if len(parts) == 2:
            m = float(parts[0]); sec = float(parts[1]); return m * 60 + sec
        if len(parts) == 3:
            h = float(parts[0]); m = float(parts[1]); sec = float(parts[2]); return h * 3600 + m * 60 + sec
    except ValueError:
        return None
    return None

def hex_to_16bit_rgb(hexcode: str, default=(0x8080, 0x8080, 0x8080)):
    if not isinstance(hexcode, str):
        return default
    m = re.match(r"^#?([0-9A-Fa-f]{6})$", hexcode.strip())
    if not m:
        return default
    h = m.group(1)
    r = int(h[0:2], 16) * 257
    g = int(h[2:4], 16) * 257
    b = int(h[4:6], 16) * 257
    return (r, g, b)

def build_xml_from_df(df, col_map, fps, pre, post, offset_secs, id_seed):
    # Prepare XML
    root = ET.Element("file")
    all_instances = ET.SubElement(root, "ALL_INSTANCES")

    def add_text(parent, tag, text):
        el = ET.SubElement(parent, tag)
        el.text = f"{text}"
        return el

    code_to_hex = {}
    next_id = id_seed
    for _, row in df.iterrows():
        code = str(row.get(col_map["code"], "") or "").strip()
        if not code:
            continue

        # Compose anchor
        try:
            m = float(row.get(col_map["mins"], 0) or 0)
            s = float(row.get(col_map["secs"], 0) or 0)
            f = float(row.get(col_map["frames"], 0) or 0)
        except ValueError:
            m = s = f = 0.0
        anchor = m * 60.0 + s + (f / float(fps))
        anchor_shifted = anchor + offset_secs
        start = max(0.0, anchor_shifted - pre)
        end = anchor_shifted + post

        inst = ET.SubElement(all_instances, "instance")
        add_text(inst, "ID", next_id)
        next_id += 1
        add_text(inst, "start", f"{start:.3f}".rstrip("0").rstrip("."))
        add_text(inst, "end", f"{end:.3f}".rstrip("0").rstrip("."))
        add_text(inst, "code", code)

        # Labels
        def add_label(group, text):
            t = str(text or "").strip()
            if not t:
                return
            lab = ET.SubElement(inst, "label")
            add_text(lab, "group", group)
            add_text(lab, "text", t)

        add_label("Team in Possession", row.get(col_map["team"]))
        add_label("Shot Outcome", row.get(col_map["outcome"]))
        add_label("Player", row.get(col_map["player"]))
        add_label("PSR", row.get(col_map["psr"]))
        add_label("Colormark", row.get(col_map["colormark"]))

        # Palette capture
        if code not in code_to_hex:
            hx = str(row.get(col_map["colormark"], "") or "").strip()
            code_to_hex[code] = hx

    # ROWS palette
    rows_el = ET.SubElement(root, "ROWS")
    for code, hx in code_to_hex.items():
        r, g, b = hex_to_16bit_rgb(hx, default=(0x8080, 0x8080, 0x8080))
        row_el = ET.SubElement(rows_el, "row")
        add_text(row_el, "code", code)
        add_text(row_el, "R", r)
        add_text(row_el, "G", g)
        add_text(row_el, "B", b)

    # Serialize
    buf = io.BytesIO()
    ET.ElementTree(root).write(buf, encoding="utf-8", xml_declaration=True)
    return buf.getvalue()

# ---------- UI ----------
st.title("🎥 Sportscode CSV → XML")
st.caption("Distributor-ready tool to convert PerformaSports-style CSV into Hudl Sportscode XML with global offset and 15s pre/post clips.")

with st.expander("⚙️ Settings", expanded=True):
    colA, colB, colC, colD = st.columns([1,1,1,1])
    encoding = colA.selectbox("CSV Encoding", ["utf-8", "latin-1"], index=0)
    fps = colB.number_input("Frames per second", value=25.0, min_value=1.0, max_value=240.0, step=1.0)
    pre = colC.number_input("Seconds PRE", value=15.0, min_value=0.0, step=1.0)
    post = colD.number_input("Seconds POST", value=15.0, min_value=0.0, step=1.0)

    # Global offset input (HH:MM:SS or MM:SS or seconds)
    offset_str = st.text_input("Global offset (e.g., 4:36, 00:04:36, or 276)", value="0")
    try:
        offset_secs = float(offset_str)
    except ValueError:
        parsed = parse_hms_to_seconds(offset_str)
        offset_secs = parsed if parsed is not None else 0.0

    id_seed = st.number_input("Starting ID", value=1, min_value=1, step=1)

uploaded = st.file_uploader("Upload PerformaSports CSV", type=["csv"])

if uploaded is not None:
    header, rows = robust_csv_bytes(uploaded.getvalue(), encoding=encoding)
    if not header:
        st.error("Could not read CSV. Please check encoding.")
        st.stop()

    df = pd.DataFrame(rows, columns=header)
    st.success(f"Loaded CSV with {len(df)} rows and {len(header)} columns.")
    st.dataframe(df.head(20), use_container_width=True)

    # Column mapping
    st.subheader("Column Mapping")
    left, right = st.columns(2)
    with left:
        mins_col = st.selectbox("Minutes column", header, index=header.index("Mins") if "Mins" in header else 0)
        secs_col = st.selectbox("Seconds column", header, index=header.index("Secs") if "Secs" in header else 0)
        frames_col = st.selectbox("Frames column", header, index=header.index("Frames") if "Frames" in header else 0)
        code_col = st.selectbox("Code (Event Name)", header, index=header.index("Event Name") if "Event Name" in header else 0)
        team_col = st.selectbox("Team", header, index=header.index("Team Name") if "Team Name" in header else 0)
    with right:
        outcome_col = st.selectbox("Outcome", header, index=header.index("Outcome") if "Outcome" in header else 0)
        player_col = st.selectbox("Player", header, index=header.index("Player") if "Player" in header else 0)
        psr_col = st.selectbox("PSR", header, index=header.index("PSR") if "PSR" in header else 0)
        colormark_col = st.selectbox("Colormark (hex #RRGGBB)", header, index=header.index("Colormark") if "Colormark" in header else 0)

    col_map = {
        "mins": mins_col,
        "secs": secs_col,
        "frames": frames_col,
        "code": code_col,
        "team": team_col,
        "outcome": outcome_col,
        "player": player_col,
        "psr": psr_col,
        "colormark": colormark_col,
    }

    # Preview computed times
    st.subheader("Preview (first 12)")
    preview = []
    for i, r in df.head(12).iterrows():
        try:
            m = float(r.get(mins_col, 0) or 0)
            s = float(r.get(secs_col, 0) or 0)
            f = float(r.get(frames_col, 0) or 0)
        except ValueError:
            m = s = f = 0.0
        anchor = m * 60.0 + s + (f / float(fps))
        anchor_shifted = anchor + offset_secs
        start = max(0.0, anchor_shifted - pre)
        end = anchor_shifted + post
        preview.append({
            "code": str(r.get(code_col, "")),
            "team": str(r.get(team_col, "")),
            "player": str(r.get(player_col, "")),
            "outcome": str(r.get(outcome_col, "")),
            "anchor(s)": round(anchor, 3),
            "start(s)": round(start, 3),
            "end(s)": round(end, 3)
        })
    st.dataframe(pd.DataFrame(preview), use_container_width=True)

    # Build XML and provide download
    xml_bytes = build_xml_from_df(df, col_map, fps=fps, pre=pre, post=post, offset_secs=offset_secs, id_seed=int(id_seed))

    st.download_button(
        label="⬇️ Download Sportscode XML",
        data=xml_bytes,
        file_name="sportscode_output.xml",
        mime="application/xml"
    )

else:
    st.info("Upload a CSV to begin.")
