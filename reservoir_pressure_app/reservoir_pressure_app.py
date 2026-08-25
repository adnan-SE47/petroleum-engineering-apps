import numpy as np
from scipy.special import exp1
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Reservoir Pressure Drop Simulator", layout="wide")

st.title("🛢️ Reservoir Pressure Drop Simulator")
st.caption("Transient pressure drawdown using the exponential integral (Ei) solution")

st.sidebar.header("Reservoir & Fluid Properties")
pi_val = st.sidebar.number_input("Initial Pressure, pi (psia)", value=5000.0)
q_val = st.sidebar.number_input("Flow Rate, q (STB/D)", value=500.0)
B_val = st.sidebar.number_input("Formation Volume Factor, B (rb/STB)", value=1.2)
mu_val = st.sidebar.number_input("Viscosity, μ (cp)", value=1.0)
k_val = st.sidebar.number_input("Permeability, k (md)", value=50.0)
h_val = st.sidebar.number_input("Thickness, h (ft)", value=50.0)
phi_val = st.sidebar.number_input("Porosity, φ (fraction)", value=0.2)
ct_val = st.sidebar.number_input("Total Compressibility, ct (psi⁻¹)", value=1e-5, format="%.2e")

st.sidebar.header("Calculation Mode")
mode = st.sidebar.radio("Solve for:", ["Pressure vs. Radius (fixed time)", "Pressure vs. Time (fixed radius)"])

const_out = 70.6 * (q_val * B_val * mu_val) / (k_val * h_val)
const_in = (948 * phi_val * mu_val * ct_val) / k_val

if mode == "Pressure vs. Radius (fixed time)":
    t = st.sidebar.number_input("Time, t (hr)", value=24.0)
    r_str = st.sidebar.text_input("Radius values, r (ft) — comma-separated", value="1, 10, 50, 100, 500, 1000, 2000")
    r_vals = np.array([float(x.strip()) for x in r_str.split(",") if x.strip() != ""])

    x_calc = (const_in * (r_vals ** 2)) / t
    p_vals = pi_val - const_out * exp1(x_calc)

    x_data, x_label = r_vals, "Radius, r (ft)"
    plot_title, line_color = f"Pressure Profile at t = {t} hrs", "red"

else:
    r = st.sidebar.number_input("Radius, r (ft)", value=1000.0)
    t_str = st.sidebar.text_input("Time values, t (hr) — comma-separated", value="1, 5, 10, 24, 48, 100, 200")
    t_vals = np.array([float(x.strip()) for x in t_str.split(",") if x.strip() != ""])

    x_calc = (const_in * (r ** 2)) / t_vals
    p_vals = pi_val - const_out * exp1(x_calc)

    x_data, x_label = t_vals, "Time, t (hrs)"
    plot_title, line_color = f"Pressure Drawdown at r = {r} ft", "blue"

col1, col2 = st.columns([2, 1])

with col1:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=p_vals,
            mode="lines+markers",
            marker=dict(size=10, color=line_color),
            line=dict(color=line_color, width=3),
        )
    )
    fig.update_layout(
        title=f"<b>{plot_title}</b>",
        xaxis=dict(title=f"<b>{x_label} [Log Scale]</b>", type="log", showgrid=True),
        yaxis=dict(title="<b>Pressure, p (psia)</b>", showgrid=True),
        plot_bgcolor="white",
        height=550,
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Results Table")
    st.dataframe(
        {x_label: np.round(x_data, 3), "Pressure (psia)": np.round(p_vals, 2)},
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")
st.caption("Originally built as a PyQt5 desktop app — rewritten as an interactive web app.")
