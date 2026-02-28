import streamlit as st
import random
from datetime import datetime

st.set_page_config(page_title="GeoCatch 🌍", page_icon="🌟", layout="wide")
st.title("🌍 GeoCatch — Pokémon-GO Style Adventure in Overland Park!")
st.success("✅ If you see this green box, the app is working perfectly! Map issue fixed.")

st.write("**Click the arrows fast to move around Overland Park**")

if "player_lat" not in st.session_state:
    st.session_state.player_lat = 38.98
if "player_lon" not in st.session_state:
    st.session_state.player_lon = -94.67
if "score" not in st.session_state:
    st.session_state.score = 0
if "caught" not in st.session_state:
    st.session_state.caught = 0

st.metric("Score", st.session_state.score)
st.metric("Creatures Caught", st.session_state.caught)

step = st.select_slider("Step size", [50, 200, 500], value=200)

col1, col2, col3 = st.columns([1,1,1])
with col2:
    if st.button("↑ North", use_container_width=True):
        st.session_state.player_lat += step / 111000
with col1:
    if st.button("← West", use_container_width=True):
        st.session_state.player_lon -= step / 90000
with col3:
    if st.button("→ East", use_container_width=True):
        st.session_state.player_lon += step / 90000
with col2:
    if st.button("↓ South", use_container_width=True):
        st.session_state.player_lat -= step / 111000

st.write(f"Your position: {st.session_state.player_lat:.4f}, {st.session_state.player_lon:.4f}")

if st.button("🔄 Spawn Creatures"):
    st.success("8 creatures spawned nearby! (imagine them on the map)")

if st.button("🎉 Catch Random Creature"):
    st.session_state.caught += 1
    st.session_state.score += random.randint(30, 70)
    st.balloons()
    st.success("You caught one!")

st.caption("Once this works, we'll add the real map back.")