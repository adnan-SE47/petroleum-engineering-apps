"""
Drilling Cost Optimization — Cost-per-Foot Equation with the Galle-Woods Bit Wear Model
==========================================================================================
Interactive Streamlit version. Finds the optimum drilling parameters (Weight on Bit
and Rotary Speed) that minimize the cost per foot of drilling, using two classic
drilling-engineering models:

1. Galle-Woods Bit Wear Model — predicts Rate of Penetration (ROP), tooth wear life,
   and bearing wear life for roller-cone bits as functions of WOB and RPM.
2. Cost-per-Foot Equation — combines bit cost, rig operating cost, trip time, and
   connection time with the footage drilled to compute the true economic cost of
   drilling ($/ft):

        Cost = (Cb + Cr * (tb + tc + Tt)) / Delta_D

Run locally:  streamlit run drilling_cost_optimizer.py
"""

import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Drilling Cost Optimizer", layout="wide")

st.title("🛢️ Drilling Cost Optimization")
st.caption("Galle-Woods Bit Wear Model + Cost-per-Foot Equation")

# ---------------------------------------------------------------------------
# Sidebar — Operating & Economic Parameters
# ---------------------------------------------------------------------------
st.sidebar.header("Economic Parameters")
Cb = st.sidebar.number_input("Bit cost, Cb ($)", value=400.0, step=10.0)
Cr = st.sidebar.number_input("Rig cost, Cr ($/hr)", value=500.0, step=10.0)
Tt = st.sidebar.number_input("Trip time, Tt (hr)", value=6.5, step=0.1)
Tc_RATE = st.sidebar.number_input("Connection time rate (hr/ft)", value=0.04 / 30, format="%.5f")

st.sidebar.header("Galle-Woods Model Constants")
TAU_H = st.sidebar.number_input("Tooth wear time constant (τH)", value=15.7)
TAU_B = st.sidebar.number_input("Bearing wear time constant (τB)", value=22.0)
WT = st.sidebar.number_input("Threshold weight on bit (Wt)", value=0.5)
A5 = st.sidebar.number_input("A5", value=1.2)
A6 = st.sidebar.number_input("A6", value=0.6)
A7 = st.sidebar.number_input("A7", value=0.9)
H1 = st.sidebar.number_input("H1", value=1.84)
H2 = st.sidebar.number_input("H2", value=6.0)

st.sidebar.header("Formation / Environmental Factor")
F1 = st.sidebar.number_input("F1", value=20.0)
F2 = st.sidebar.number_input("F2", value=1.83)
F3 = st.sidebar.number_input("F3", value=1.0)
F4 = st.sidebar.number_input("F4", value=0.76)
F8 = st.sidebar.number_input("F8", value=0.959)
J_ENV = F1 * F2 * F3 * F4 * F8

st.sidebar.header("Sweep Ranges")
w_min, w_max = st.sidebar.slider("WOB range (1000 lbf/in)", 1, 15, (2, 7))
n_min, n_max = st.sidebar.slider("RPM range", 10, 300, (20, 200))

W_VEC = np.arange(w_min, w_max + 1, 1)
N_VEC = np.arange(n_min, n_max + 1, 20 if n_max - n_min > 60 else 10)
if len(N_VEC) < 2:
    N_VEC = np.linspace(n_min, n_max, 10)


def compute_cost_per_foot(W: float, N: float) -> float:
    f5 = ((W - WT) / (4.0 - WT)) ** A5 if W > WT else 0.0
    f6 = (N / 60.0) ** A6
    J1 = J_ENV * f5 * f6

    J2 = 0.250 * (2 - (W / 4.0)) * (60.0 / N) ** H1
    tb_teeth = 4 * J2 * TAU_H

    J3 = (60.0 / N) * (4.0 / W)
    tb_bearing = TAU_B * J3

    tb = min(tb_teeth, tb_bearing)
    hf_final = 1.0 if tb_teeth <= tb_bearing else tb_bearing / tb_teeth

    term1 = (1 - np.exp(-A7 * hf_final)) / A7
    term2 = (H2 * (1 - np.exp(-A7 * hf_final) - A7 * hf_final * np.exp(-A7 * hf_final))) / (A7 ** 2)
    delta_D = J1 * J2 * TAU_H * (term1 + term2)

    if delta_D <= 0:
        return np.nan

    tc = delta_D * Tc_RATE
    return (Cb + Cr * (tb + tc + Tt)) / delta_D


@st.cache_data
def build_result_table(W_VEC, N_VEC, Cb, Cr, Tt, Tc_RATE, TAU_H, TAU_B, WT, A5, A6, A7, H1, H2, J_ENV):
    table = np.zeros((len(N_VEC), len(W_VEC)))
    for i, N in enumerate(N_VEC):
        for j, W in enumerate(W_VEC):
            table[i, j] = compute_cost_per_foot(W, N)
    return table


Result_Table = build_result_table(
    tuple(W_VEC), tuple(N_VEC), Cb, Cr, Tt, Tc_RATE, TAU_H, TAU_B, WT, A5, A6, A7, H1, H2, J_ENV
)

i_min, j_min = np.unravel_index(np.nanargmin(Result_Table), Result_Table.shape)
opt_rpm, opt_wob, opt_cost = N_VEC[i_min], W_VEC[j_min], Result_Table[i_min, j_min]

col1, col2, col3 = st.columns(3)
col1.metric("Optimum WOB", f"{opt_wob:.0f} (×1000 lbf/in)")
col2.metric("Optimum RPM", f"{opt_rpm:.0f}")
col3.metric("Minimum Cost", f"${opt_cost:.2f} /ft")

tab1, tab2 = st.tabs(["Heatmap", "3D Surface"])

with tab1:
    fig_heat = go.Figure(
        data=go.Heatmap(
            z=Result_Table,
            x=W_VEC,
            y=N_VEC,
            colorscale=[[0, "green"], [0.2, "yellow"], [1, "red"]],
            text=np.round(Result_Table, 2),
            texttemplate="%{text}",
            colorbar=dict(title="$/ft"),
        )
    )
    fig_heat.update_layout(
        title="Cost Per Foot ($/ft)",
        xaxis_title="Weight on Bit (WOB) — 1000 lbf/in",
        yaxis_title="Rotary Speed (RPM)",
        height=550,
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with tab2:
    fig_3d = go.Figure(
        data=[
            go.Surface(
                z=Result_Table,
                x=W_VEC,
                y=N_VEC,
                colorscale=[[0, "green"], [0.2, "yellow"], [1, "red"]],
            )
        ]
    )
    fig_3d.update_layout(
        title="Cost Optimization Surface",
        scene=dict(xaxis_title="WOB", yaxis_title="RPM", zaxis_title="Cost ($/ft)"),
        height=650,
    )
    st.plotly_chart(fig_3d, use_container_width=True)

st.markdown("---")
st.caption("Originally developed as a Drilling Engineering course project — rewritten as an interactive web app.")
