import math
import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Directional Trajectory Calculator", layout="wide")

st.title("🧭 Directional Drilling Trajectory Design")
st.caption("Survey-to-survey well path calculation")

st.sidebar.header("Station 1")
md1 = st.sidebar.number_input("MD1 (ft)", value=0.0)
inc1 = st.sidebar.number_input("Inclination 1 (°)", value=0.0)
az1 = st.sidebar.number_input("Azimuth 1 (°)", value=0.0)
tvd1 = st.sidebar.number_input("TVD1 (ft)", value=0.0)
n1 = st.sidebar.number_input("North1 (ft)", value=0.0)
e1 = st.sidebar.number_input("East1 (ft)", value=0.0)

st.sidebar.header("Station 2")
md2 = st.sidebar.number_input("MD2 (ft)", value=1000.0)
inc2 = st.sidebar.number_input("Inclination 2 (°)", value=30.0)
az2 = st.sidebar.number_input("Azimuth 2 (°)", value=45.0)

st.sidebar.header("Target")
target_az = st.sidebar.number_input("Target Azimuth (°)", value=45.0)
method_str = st.sidebar.selectbox(
    "Calculation Method",
    ["Minimum Curvature", "Average Angle", "Balanced Tangential", "Tangential", "Radius of Curvature"],
)


def calculate_trajectory(md1, inc1, az1, tvd1, n1, e1, md2, inc2, az2, target_az, method_str):
    i1, i2 = math.radians(inc1), math.radians(inc2)
    a1, a2 = math.radians(az1), math.radians(az2)
    delta_MD = md2 - md1

    dTVD = dN = dE = 0.0

    if method_str == "Minimum Curvature":
        D1 = np.clip(math.cos(i2) * math.cos(i1) + math.sin(i2) * math.sin(i1) * math.cos(a2 - a1), -1.0, 1.0)
        D2 = math.acos(D1)
        FC = 1 if D2 == 0 else (2 / D2) * math.tan(D2 / 2)
        dTVD = (delta_MD / 2) * (math.cos(i1) + math.cos(i2)) * FC
        dN = (delta_MD / 2) * (math.sin(i1) * math.cos(a1) + math.sin(i2) * math.cos(a2)) * FC
        dE = (delta_MD / 2) * (math.sin(i1) * math.sin(a1) + math.sin(i2) * math.sin(a2)) * FC

    elif method_str == "Average Angle":
        i_avg, a_avg = (i1 + i2) / 2, (a1 + a2) / 2
        dTVD = delta_MD * math.cos(i_avg)
        dN = delta_MD * math.sin(i_avg) * math.cos(a_avg)
        dE = delta_MD * math.sin(i_avg) * math.sin(a_avg)

    elif method_str == "Balanced Tangential":
        dTVD = (delta_MD / 2) * (math.cos(i1) + math.cos(i2))
        dN = (delta_MD / 2) * (math.sin(i1) * math.cos(a1) + math.sin(i2) * math.cos(a2))
        dE = (delta_MD / 2) * (math.sin(i1) * math.sin(a1) + math.sin(i2) * math.sin(a2))

    elif method_str == "Tangential":
        dTVD = delta_MD * math.cos(i2)
        dN = delta_MD * math.sin(i2) * math.cos(a2)
        dE = delta_MD * math.sin(i2) * math.sin(a2)

    elif method_str == "Radius of Curvature":
        dI, dA = i2 - i1, a2 - a1
        if abs(dI) < 1e-6:
            dTVD = delta_MD * math.cos(i1)
            dHD = delta_MD * math.sin(i1)
        else:
            dTVD = delta_MD * (math.sin(i2) - math.sin(i1)) / dI
            dHD = delta_MD * (math.cos(i1) - math.cos(i2)) / dI
        if abs(dA) < 1e-6:
            dN = dHD * math.cos(a1)
            dE = dHD * math.sin(a1)
        else:
            dN = dHD * (math.sin(a2) - math.sin(a1)) / dA
            dE = dHD * (math.cos(a1) - math.cos(a2)) / dA

    tvd2, n2, e2 = tvd1 + dTVD, n1 + dN, e1 + dE

    closure_dist = math.sqrt(n2 ** 2 + e2 ** 2)
    closure_dir = math.degrees(math.atan2(e2, n2))
    if closure_dir < 0:
        closure_dir += 360
    VS = closure_dist * math.cos(math.radians(closure_dir - target_az))

    if delta_MD == 0:
        dls_cos = dls_sin = dls_pyth = 0.0
    else:
        cos_beta = np.clip(math.cos(i1) * math.cos(i2) + math.sin(i1) * math.sin(i2) * math.cos(a2 - a1), -1.0, 1.0)
        dls_cos = math.degrees(math.acos(cos_beta)) * (100 / delta_MD)

        sin_sq_half_beta = max((math.sin((i2 - i1) / 2) ** 2) + (math.sin(i1) * math.sin(i2) * math.sin((a2 - a1) / 2) ** 2), 0)
        dls_sin = (2 * math.degrees(math.asin(math.sqrt(sin_sq_half_beta)))) * (100 / delta_MD)

        delta_I_deg, delta_A_deg = inc2 - inc1, az2 - az1
        if delta_A_deg > 180:
            delta_A_deg -= 360
        elif delta_A_deg < -180:
            delta_A_deg += 360
        dls_pyth = math.sqrt(delta_I_deg ** 2 + (math.sin((i1 + i2) / 2) * delta_A_deg) ** 2) * (100 / delta_MD)

    return dict(
        dTVD=dTVD, dN=dN, dE=dE, tvd2=tvd2, n2=n2, e2=e2,
        closure_dist=closure_dist, closure_dir=closure_dir, VS=VS,
        dls_cos=dls_cos, dls_sin=dls_sin, dls_pyth=dls_pyth,
    )


results = calculate_trajectory(md1, inc1, az1, tvd1, n1, e1, md2, inc2, az2, target_az, method_str)

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Survey Results")
    r1, r2, r3 = st.columns(3)
    r1.metric("ΔTVD (ft)", f"{results['dTVD']:.2f}")
    r2.metric("ΔNorth (ft)", f"{results['dN']:.2f}")
    r3.metric("ΔEast (ft)", f"{results['dE']:.2f}")

    r4, r5, r6 = st.columns(3)
    r4.metric("TVD2 (ft)", f"{results['tvd2']:.2f}")
    r5.metric("North2 (ft)", f"{results['n2']:.2f}")
    r6.metric("East2 (ft)", f"{results['e2']:.2f}")

    r7, r8, r9 = st.columns(3)
    r7.metric("Closure Dist (ft)", f"{results['closure_dist']:.2f}")
    r8.metric("Closure Dir (°)", f"{results['closure_dir']:.2f}")
    r9.metric("Vertical Section (ft)", f"{results['VS']:.2f}")

    st.subheader("Dogleg Severity (°/100ft)")
    d1, d2, d3 = st.columns(3)
    d1.metric("Cosine Method", f"{results['dls_cos']:.4f}")
    d2.metric("Sine Method", f"{results['dls_sin']:.4f}")
    d3.metric("Pythagorean Method", f"{results['dls_pyth']:.4f}")

with col2:
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[e1, results["e2"]],
            y=[n1, results["n2"]],
            mode="lines+markers+text",
            text=["<b>1</b>", "<b>2</b>"],
            textposition=["bottom right", "top left"],
            line=dict(color="#0072BD", width=3),
            marker=dict(size=11, color="white", line=dict(color="#0072BD", width=2.5)),
            showlegend=False,
        )
    )
    fig.add_trace(
        go.Scatter(x=[0], y=[0], mode="markers", marker=dict(symbol="square", size=10, color="red"), showlegend=False)
    )
    max_val = max(abs(e1), abs(results["e2"]), abs(n1), abs(results["n2"])) * 1.2 or 10
    fig.update_layout(
        title="<b>Plan View</b>",
        xaxis=dict(title="<b>EAST</b>", range=[-max_val, max_val], constrain="domain"),
        yaxis=dict(title="<b>NORTH</b>", range=[-max_val, max_val], scaleanchor="x", scaleratio=1),
        height=550,
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Originally built as a PyQt5 desktop app — rewritten as an interactive web app.")
