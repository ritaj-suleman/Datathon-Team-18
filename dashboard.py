"""NorthGrid Loss Command Center.  Run after run_all.py:   streamlit run dashboard.py

Every page follows the sub-division filter in the sidebar. Charts and tables are clickable:
  - Control Room: click a sub-division bar to open its Loss Detective case file
  - Loss Detective / Sub-divisions: pick a row to open that case
  - Crime Network: click a meter to open it in Meter X-Ray; pick a ring row to isolate the ring
  - Meter X-Ray: pick any suspect row to inspect it
"""
import json
import textwrap
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

_V = tuple(int(x) for x in st.__version__.split(".")[:2])
WIDE = {"width": "stretch"} if _V >= (1, 46) else {"use_container_width": True}
OUT = Path(__file__).resolve().parent / "outputs"
NAVY, TEAL, ORANGE, PEACH, INK, MUTED, RED, BG = "#161A3A", "#10B38A", "#FB7A3C", "#FFE3D3", "#1E2240", "#8A90A6", "#E5484D", "#F3F4F8"
PALETTE = [TEAL, ORANGE, NAVY, RED, "#7C5CFF", "#00A3FF", "#F5B700", MUTED]
SUBDIV = {"ZN02": "TXLA", "ZN03": "KHRN", "ZN05": "GJKN", "ZN07": "PTWL", "ZN08": "HTAR", "ZN11": "MRDN", "ZN13": "CHKW", "ZN14": "JHLM"}
PAGES = ["Control Room", "Loss Detective", "Crime Network", "Meter X-Ray", "Sub-divisions", "Recovery Simulator",
         "Data Trust", "Board Pitch"]

st.set_page_config(page_title="NorthGrid Loss Command Center", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
html, body, [class*="css"], .stMarkdown, .stText, button, input {{ font-family: 'Poppins', sans-serif; }}
.stApp {{ background: {BG}; }}
.block-container {{ padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1440px; }}
h1, h2, h3, h4 {{ color: {INK}; font-weight: 700; letter-spacing: -.01em; }}
h4, div[data-testid="stMarkdownContainer"] h4 {{ font-size: 1.05rem !important; margin: 0 0 .25rem 0; padding: 0 0 .2rem 0; }}
section[data-testid="stSidebar"] {{ background: {NAVY}; }}
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] {{ color: #E8EAF6; }}
section[data-testid="stSidebar"] [role="radiogroup"] label {{ padding: 9px 12px; border-radius: 10px; margin: 1px 0; width: 100%;
    transition: background .15s; }}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background: rgba(255,255,255,.08); }}
section[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{ background: rgba(16,179,138,.22);
    box-shadow: inset 3px 0 0 {TEAL}; }}
section[data-testid="stSidebar"] [data-baseweb="tag"] {{ background: {TEAL} !important; }}
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div > div.panel-mark),
div[data-testid="stVerticalBlockBorderWrapper"] {{ background: #fff; border-radius: 18px; border: 1px solid #E8EAF2 !important;
    box-shadow: 0 6px 22px rgba(22,26,58,.05); }}
.kpi {{ background: #fff; border-radius: 18px; padding: 16px 18px; border: 1px solid #E8EAF2; box-shadow: 0 6px 22px rgba(22,26,58,.05);
    min-height: 118px; overflow: hidden; transition: transform .15s, box-shadow .15s; }}
.kpi:hover {{ transform: translateY(-2px); box-shadow: 0 10px 28px rgba(22,26,58,.09); }}
.kpi-label {{ color: {MUTED}; font-size: .74rem; font-weight: 600; text-transform: uppercase; letter-spacing: .06em;
    line-height: 1.3; }}
.kpi-value {{ color: {INK}; font-size: clamp(1.25rem, 2.2vw, 1.85rem); font-weight: 700; line-height: 1.2; margin-top: 6px;
    overflow-wrap: anywhere; }}
.kpi-sub {{ font-size: .8rem; margin-top: 4px; line-height: 1.35; }}
.kpi-bar {{ height: 4px; border-radius: 4px; margin-bottom: 10px; width: 36px; }}
.hero {{ background: linear-gradient(135deg, {NAVY} 0%, #2A3170 100%); color: #fff; border-radius: 18px; padding: 18px 22px;
    position: relative; overflow: hidden; }}
.hero:after {{ content: ''; position: absolute; right: -40px; top: -40px; width: 160px; height: 160px; border-radius: 50%;
    background: radial-gradient(circle, rgba(16,179,138,.45), rgba(16,179,138,0) 70%); }}
.hero .big {{ font-size: clamp(1.6rem, 3vw, 2.3rem); font-weight: 700; color: {TEAL}; }}
.hero .lbl {{ font-size: .74rem; text-transform: uppercase; letter-spacing: .08em; opacity: .7; }}
.pill {{ display: inline-block; padding: 3px 11px; border-radius: 999px; font-size: .74rem; font-weight: 600; margin: 2px 6px 2px 0;
    white-space: nowrap; }}
.tl {{ border-left: 2px solid #DDE0EA; padding: 2px 0 12px 16px; margin-left: 6px; position: relative; }}
.tl:before {{ content: ''; width: 10px; height: 10px; background: #fff; border: 3px solid {ORANGE}; border-radius: 50%;
    position: absolute; left: -8px; top: 5px; }}
.tl b {{ color: {INK}; font-size: .86rem; }} .tl span {{ color: {MUTED}; font-size: .8rem; }}
.ev {{ background: #F7F8FC; border-radius: 12px; padding: 10px 14px; margin: 6px 0; border-left: 4px solid {ORANGE};
    font-size: .88rem; line-height: 1.45; overflow-wrap: anywhere; }}
.ev.lead {{ border-left-color: {TEAL}; background: #EEFAF6; }}
.brand {{ font-size: 1.3rem; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 8px; }}
.bolt {{ width: 26px; height: 26px; border-radius: 8px; background: {TEAL}; display: inline-flex; align-items: center;
    justify-content: center; }}
.hint {{ color: {MUTED}; font-size: .78rem; margin-top: -4px; }}
.pagehead {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 14px; margin-bottom: 4px; }}
.pagehead h2 {{ margin: 0; }}
@media (max-width: 900px) {{ .kpi {{ min-height: 0; }} .block-container {{ padding-left: 1rem; padding-right: 1rem; }} }}
</style>""", unsafe_allow_html=True)

BOLT = ("<svg width='14' height='16' viewBox='0 0 14 16'><path d='M8 0L0 9h5l-1 7 8-9H7l1-7z' fill='#fff'/></svg>")


@st.cache_resource
def load():
    def csv(name, **kw):
        p = OUT / name
        return pd.read_csv(p, **kw) if p.exists() else pd.DataFrame()
    res = json.loads((OUT / "results_losses.json").read_text()) if (OUT / "results_losses.json").exists() else {}
    d = dict(res=res, zm=csv("zone_month.csv", parse_dates=["mo"]), bridge=csv("a3_it_bridge.csv"),
             b1=csv("b1_subdivision_loss.csv"), scores=csv("meter_scores_all.csv"), nodes=csv("network_nodes.csv"),
             edges=csv("network_edges.csv"), rings=csv("network_rings.csv"), readers=csv("c5_readers.csv"), dq=csv("dq_log.csv"))
    p = OUT / "xray_monthly.parquet"
    d["xray"] = pd.read_parquet(p) if p.exists() else pd.DataFrame()
    return d


D = load()
R = D["res"]
C6, C3, C2 = R.get("C6") or {}, R.get("C3") or {}, R.get("C2") or {}
VERS = R.get("billing_versions") or {}


# ---------------------------------------------------------------- helpers
def zname(z, short=False):
    return SUBDIV.get(z, z) if short else f"{SUBDIV.get(z, z)} ({z})"


def num(x, f="{:,.1f}", na="n/a"):
    try:
        return f.format(x) if x is not None and not (isinstance(x, float) and np.isnan(x)) else na
    except Exception:
        return na


def wrap(s, n=22):
    return "<br>".join(textwrap.wrap(str(s), n)) or str(s)


def short_part(name):
    n = name.lower()
    for key, lab in [("billing", "Billing software"), ("tamper", "Meter tampering"), ("network area", "New network area"),
                     ("other", "Other / unexplained")]:
        if key in n:
            return lab
    return wrap(name, 20)


def kpi(col, label, value, sub="", color=TEAL):
    col.markdown(f"<div class='kpi'><div class='kpi-bar' style='background:{color}'></div><div class='kpi-label'>{label}</div>"
                 f"<div class='kpi-value'>{value}</div><div class='kpi-sub' style='color:{color}'>{sub}</div></div>",
                 unsafe_allow_html=True)


def head(title, sub=""):
    st.markdown(f"<div class='pagehead'><h2>{title}</h2></div>", unsafe_allow_html=True)
    if sub:
        st.caption(sub)


def style(fig, h=340, legend=True, legend_below=True):
    fig.update_layout(height=h, margin=dict(l=8, r=8, t=12, b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family="Poppins, sans-serif", color=INK, size=12), showlegend=legend,
                      hoverlabel=dict(bgcolor="#fff", bordercolor="#E0E3EC", font=dict(family="Poppins", color=INK)),
                      legend=dict(orientation="h", yanchor="top", y=-0.14, x=0, bgcolor="rgba(0,0,0,0)") if legend_below
                      else dict(orientation="h", yanchor="bottom", y=1.0, x=0, bgcolor="rgba(0,0,0,0)"))
    fig.update_xaxes(showgrid=False, linecolor="#E6E8F0", automargin=True)
    fig.update_yaxes(gridcolor="#EEF0F6", zeroline=False, automargin=True)
    return fig


def padx(fig, vals, pad=0.3):
    """Leave room for outside bar labels so they never collide with the axis or each other."""
    v = pd.Series(vals, dtype=float).dropna()
    lo, hi = min(v.min(), 0), max(v.max(), 0)
    span = (hi - lo) or 1
    return fig.update_xaxes(range=[lo - (pad * span if lo < 0 else 0), hi + pad * span])


def show(fig, key=None, on_select=None):
    kw = dict(**WIDE, config={"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]})
    if key:
        kw.update(key=key, on_select=on_select or "rerun", selection_mode="points")
    return st.plotly_chart(fig, **kw)


def picked(key, field="customdata"):
    """First clicked point of a chart or the selected row of a table, from session state."""
    sel = st.session_state.get(key)
    try:
        sel = sel["selection"] if "selection" in sel else sel
        if "points" in sel and sel["points"]:
            v = sel["points"][0].get(field)
            return v[0] if isinstance(v, list) else v
        if "rows" in sel and sel["rows"]:
            return sel["rows"][0]
    except (TypeError, KeyError, AttributeError):
        pass
    return None


def go_to(page, **state):
    st.session_state["nav"] = page
    for k, v in state.items():
        st.session_state[k] = v


def panel():
    return st.container(border=True)


# ---------------------------------------------------------------- sidebar: navigation + global filter
ALL_Z = sorted(D["zm"].z.unique()) if len(D["zm"]) else []
st.session_state.setdefault("nav", PAGES[0])
st.session_state.setdefault("zsel", ALL_Z)
with st.sidebar:
    st.markdown(f"<div class='brand'><span class='bolt'>{BOLT}</span>NorthGrid</div>"
                "<div style='opacity:.65;font-size:.82rem;margin:2px 0 14px 34px'>Loss Investigation Unit</div>", unsafe_allow_html=True)
    page = st.radio("Navigate", PAGES, key="nav", label_visibility="collapsed")
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
    st.multiselect("Sub-divisions", ALL_Z, key="zsel", format_func=zname,
                   help="Filters every page. Clear it to see all sub-divisions.")
    st.markdown("<div style='opacity:.55;font-size:.74rem;margin-top:10px;line-height:1.5'>Click bars, meters and table rows "
                "to drill down. Company-wide figures (IT bridge, C6) are not filtered.</div>", unsafe_allow_html=True)
ZSEL = st.session_state["zsel"] or ALL_Z
ZM = D["zm"][D["zm"].z.isin(ZSEL)] if len(D["zm"]) else D["zm"]
FILTERED = set(ZSEL) != set(ALL_Z)
SCOPE = "all sub-divisions" if not FILTERED else ", ".join(zname(z, True) for z in ZSEL)


def fy_loss(df, fy):
    g = df[df.fy == fy]
    return 100 * (1 - g.billed.sum() / g.so.sum()) if len(g) and g.so.sum() else None


# ---------------------------------------------------------------- CONTROL ROOM
if page == "Control Room":
    head("Loss Command Center", f"Board meeting, 11:00. The truth about the losses, in one screen. Showing {SCOPE}.")
    l24, l26 = fy_loss(ZM, "FY2023-24"), fy_loss(ZM, "FY2025-26")
    br = D["bridge"]
    it26 = br[(br.step.str.startswith("0.")) & (br.fy == "FY2025-26")].loss_pct if len(br) else pd.Series(dtype=float)
    cost = ZM.excess_pkr.sum() / 1e6 if "excess_pkr" in ZM else C3.get("excess_loss_pkr_mn")
    gwh = ZM.excess_kwh.sum() / 1e6 if "excess_kwh" in ZM else None
    hit = [z for z in C2.get("affected", []) if z in ZSEL]
    k = st.columns(4)
    kpi(k[0], "Real loss FY2025-26", f"{num(l26)}%",
        f"up {num((l26 or 0) - (l24 or 0), '{:+.1f}')}pp since FY2023-24" if l24 is not None else "", RED)
    kpi(k[1], "IT dashboard said", f"{num(it26.iloc[0] if len(it26) else None)}%", "company-wide, raw files summed", MUTED)
    kpi(k[2], "Cost to 30 Jun 2026", f"PKR {num(cost, '{:,.0f}')} mn", f"{num(gwh)} GWh above the FY2023-24 rate", ORANGE)
    kpi(k[3], "It started", min(VERS[z]["golive"] for z in hit) if hit else "no break",
        ("billing upgrade in " + ", ".join(zname(z, True) for z in hit)) if hit else "no billing upgrade in this selection", TEAL)
    st.write("")

    left, right = st.columns([1.75, 1], gap="medium")
    with left, panel():
        st.markdown("#### Energy sent out vs energy billed")
        if len(ZM):
            cm = ZM.groupby("mo")[["so", "billed"]].sum().reset_index()
            cm["loss"] = 100 * (1 - cm.billed / cm.so)
            fig = go.Figure()
            fig.add_bar(x=cm.mo, y=cm.so / 1e6, name="Sent out (GWh)", marker_color=PEACH,
                        hovertemplate="%{x|%b %Y}<br>Sent out %{y:.2f} GWh<extra></extra>")
            fig.add_scatter(x=cm.mo, y=cm.billed / 1e6, name="Billed (GWh)", mode="lines", line=dict(color=NAVY, width=2, dash="dot"),
                            hovertemplate="Billed %{y:.2f} GWh<extra></extra>")
            fig.add_scatter(x=cm.mo, y=cm.loss, name="Loss %", yaxis="y2", mode="lines", line=dict(color=TEAL, width=3, shape="spline"),
                            hovertemplate="Loss %{y:.1f}%<extra></extra>")
            gl = [(pd.Timestamp(v["golive"]), z) for z, v in VERS.items() if v.get("golive") and z in ZSEL]
            if gl:
                lk = cm.set_index("mo").loss
                fig.add_scatter(x=[d for d, _ in gl], y=[lk.get(d, np.nan) for d, _ in gl], yaxis="y2", mode="markers",
                                name="Billing v5.2 goes live", marker=dict(symbol="diamond", size=13, color=ORANGE, line=dict(color="#fff", width=2)),
                                text=[zname(z) for _, z in gl], hovertemplate="Billing v5.2 live in %{text}<br>%{x|%b %Y}<extra></extra>")
            fig.update_layout(hovermode="x unified", yaxis=dict(title="GWh"),
                              yaxis2=dict(title="Loss %", overlaying="y", side="right", showgrid=False, rangemode="tozero"))
            show(style(fig, 370))
    with right:
        parts = C6.get("parts", {})
        if parts:
            big = max(parts.items(), key=lambda kv: kv[1])
            st.markdown(f"<div class='hero'><div class='lbl'>Root cause found (company-wide)</div>"
                        f"<div style='font-size:1rem;margin:6px 0 2px 0;max-width:85%'>{big[0]}</div>"
                        f"<div class='big'>{big[1]:.1f}pp</div><div style='opacity:.8;font-size:.86rem'>of the {C6['total_pp']:.1f}pp "
                        f"rise ({100 * big[1] / C6['total_pp']:.0f}%)</div></div>", unsafe_allow_html=True)
            st.write("")
            with panel():
                st.markdown("#### What drove the rise (pp)")
                s = pd.Series(parts).sort_values()
                s.index = [short_part(i) for i in s.index]
                fig = go.Figure(go.Bar(y=list(s.index), x=s.values, orientation="h",
                                       marker_color=[TEAL if v == s.max() else ("#C9CCDA" if v < 0 else ORANGE) for v in s.values],
                                       text=[f"{v:+.2f}" for v in s.values], textposition="outside", cliponaxis=False,
                                       hovertemplate="%{y}<br>%{x:+.2f}pp<extra></extra>"))
                show(padx(style(fig, 280, legend=False), s.values).update_xaxes(title="percentage points"))

    a, b = st.columns([1.2, 1], gap="medium")
    with a, panel():
        st.markdown("#### Loss change by sub-division, FY2023-24 to FY2025-26")
        st.markdown("<div class='hint'>Click a bar to open that sub-division's case file.</div>", unsafe_allow_html=True)
        if len(ZM):
            zf = ZM.groupby(["z", "fy"])[["so", "billed"]].sum()
            zf = (100 * (1 - zf.billed / zf.so)).unstack()
            if {"FY2023-24", "FY2025-26"} <= set(zf.columns):
                ch = (zf["FY2025-26"] - zf["FY2023-24"]).sort_values()
                up = [bool(VERS.get(z, {}).get("golive")) for z in ch.index]
                fig = go.Figure(go.Bar(y=[zname(z) for z in ch.index], x=ch.values, orientation="h", customdata=list(ch.index),
                                       marker_color=[ORANGE if u else TEAL for u in up], text=[f"{v:+.1f}pp" for v in ch.values],
                                       textposition="outside", cliponaxis=False, hovertemplate="%{y}<br>%{x:+.2f}pp<br>Click for the case file<extra></extra>"))
                fig.add_scatter(x=[None], y=[None], mode="markers", marker=dict(color=ORANGE, size=10, symbol="square"), name="Got billing v5.2")
                fig.add_scatter(x=[None], y=[None], mode="markers", marker=dict(color=TEAL, size=10, symbol="square"), name="Still on v5.1")
                show(padx(style(fig, 90 + 38 * len(ch)), ch.values, 0.2).update_xaxes(title="pp"), key="cr_zone",
                     on_select=lambda: (z := picked("cr_zone")) and go_to("Loss Detective", case=z))
    with b, panel():
        st.markdown("#### Timeline")
        ev = []
        for c in R.get("DETECTIVE") or []:
            if c["zone"] in ZSEL and c.get("change_point") and c.get("loss_jump_pp", 0) >= 1:
                ev.append((c["change_point"], f"Loss breaks upward in {zname(c['zone'], True)}", f"{c['loss_jump_pp']:+.1f}pp vs FY2023-24"))
        for z, v in VERS.items():
            if v.get("golive") and z in ZSEL:
                ev.append((v["golive"], f"Billing {v['to_ver']} live in {zname(z, True)}", "billed/metered ratio drops"))
        for g in (R.get("NETWORK") or {}).get("top_rings", [])[:3]:
            if g["zone"] in ZSEL and g.get("drop_window"):
                ev.append((g["drop_window"][:7], f"{g['ring']}: {g['meters']} meters drop together", zname(g["zone"], True)))
        if not ev:
            st.caption("No events in this selection.")
        for d_, t_, s_ in sorted(ev)[:8]:
            st.markdown(f"<div class='tl'><b>{d_}</b> &middot; {t_}<br><span>{s_}</span></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------- LOSS DETECTIVE
elif page == "Loss Detective":
    head("Loss Detective", "Automatic root-cause investigation: find the break in each sub-division, put every suspect on trial, "
                           "and convert the evidence into percentage points explained.")
    cases = [c for c in R.get("DETECTIVE") or [] if c["zone"] in ZSEL]
    if not cases:
        st.info("No case files for this selection. Run step 7 (python run_all.py --from 7).")
    else:
        ov = pd.DataFrame([dict(Sub_division=zname(c["zone"]), Break=c.get("change_point") or "none",
                                Jump_pp=c.get("loss_jump_pp"), Loss_FY24=c.get("loss_fy24"), Loss_FY26=c.get("loss_fy26"),
                                Prime_suspect=(c["suspects"][0]["suspect"] if c.get("suspects") else "no material break")) for c in cases])
        codes = [c["zone"] for c in cases]
        with panel():
            st.markdown("#### All case files")
            st.markdown("<div class='hint'>Select a row to open the case.</div>", unsafe_allow_html=True)
            st.dataframe(ov.rename(columns=lambda c: c.replace("_", " ")), **WIDE, hide_index=True,
                         key="det_tbl", on_select=lambda: (i := picked("det_tbl")) is not None and st.session_state.update(case=codes[i]),
                         selection_mode="single-row",
                         column_config={"Jump pp": st.column_config.NumberColumn(format="%+.2f"),
                                        "Loss FY24": st.column_config.NumberColumn("Loss FY2023-24 %", format="%.2f"),
                                        "Loss FY26": st.column_config.NumberColumn("Loss FY2025-26 %", format="%.2f")})
        if st.session_state.get("case") not in codes:
            st.session_state["case"] = max(cases, key=lambda c: c.get("loss_jump_pp") or 0)["zone"]
        zc = st.selectbox("Case file", codes, key="case", format_func=zname)
        c = next(x for x in cases if x["zone"] == zc)
        k = st.columns(4)
        kpi(k[0], "Loss FY2023-24", f"{num(c.get('loss_fy24'), '{:.2f}')}%", "baseline", MUTED)
        kpi(k[1], "Loss FY2025-26", f"{num(c.get('loss_fy26'), '{:.2f}')}%",
            f"{num((c.get('loss_fy26') or 0) - (c.get('loss_fy24') or 0), '{:+.2f}')}pp", RED)
        kpi(k[2], "Break month", c.get("change_point") or "none", f"{num(c.get('loss_jump_pp'), '{:+.1f}')}pp jump", ORANGE)
        gl = VERS.get(zc, {}).get("golive")
        kpi(k[3], "Billing upgrade", gl or "none", "v5.1 to v5.2" if gl else "still on v5.1 (control group)", TEAL)
        st.write("")
        st.markdown(f"<div class='ev lead'><b>Verdict.</b> {c['verdict']}</div>", unsafe_allow_html=True)
        st.write("")
        a, b = st.columns([1.15, 1], gap="medium")
        with a, panel():
            st.markdown("#### Loss vs the same month of FY2023-24")
            g = ZM[ZM.z == zc].sort_values("mo")
            if len(g):
                fig = go.Figure()
                fig.add_bar(x=g.mo, y=g.yoy_vs_fy24_pp, marker_color=[ORANGE if v > 2 else "#C9CCDA" for v in g.yoy_vs_fy24_pp],
                            name="pp vs FY2023-24", hovertemplate="%{x|%b %Y}: %{y:+.2f}pp<extra></extra>")
                if "billed_over_ami" in g:
                    fig.add_scatter(x=g.mo, y=g.billed_over_ami, yaxis="y2", name="Billed / smart-meter kWh",
                                    line=dict(color=TEAL, width=3, shape="spline"), hovertemplate="ratio %{y:.3f}<extra></extra>")
                for d_, col, nm in [(c.get("change_point"), RED, "Break"), (gl, NAVY, "Billing v5.2 live")]:
                    if d_:
                        fig.add_scatter(x=[pd.Timestamp(d_)] * 2, y=[g.yoy_vs_fy24_pp.min(), g.yoy_vs_fy24_pp.max()], mode="lines",
                                        line=dict(color=col, dash="dash", width=2), name=f"{nm} {d_}", hoverinfo="skip")
                fig.update_layout(yaxis_title="pp", yaxis2=dict(overlaying="y", side="right", showgrid=False, title="ratio"))
                show(style(fig, 360))
        with b, panel():
            st.markdown("#### Suspects on trial (pp of the jump explained)")
            if c.get("suspects"):
                s = pd.DataFrame(c["suspects"]).iloc[::-1]
                fig = go.Figure(go.Bar(y=[wrap(x, 24) for x in s.suspect], x=s.explains_pp, orientation="h",
                                       marker_color=[TEAL if v == s.explains_pp.max() and v > 0 else ("#C9CCDA" if v <= 0 else ORANGE) for v in s.explains_pp],
                                       text=[f"{v:+.2f} ({cf})" for v, cf in zip(s.explains_pp, s.confidence)], textposition="outside", cliponaxis=False,
                                       hovertext=[wrap(e, 50) for e in s.evidence], hovertemplate="%{hovertext}<extra></extra>"))
                show(padx(style(fig, 360, legend=False), s.explains_pp, 0.45).update_xaxes(title="pp"))
            else:
                st.caption("No material break, so no suspects were tried.")
        if c.get("suspects"):
            cols = st.columns(2)
            for i, r_ in enumerate(c["suspects"]):
                cols[i % 2].markdown(f"<div class='ev{' lead' if i == 0 else ''}'><b>{r_['suspect']}</b> &middot; {r_['explains_pp']:+.2f}pp, "
                                     f"{r_['confidence']} confidence<br>{r_['evidence']}</div>", unsafe_allow_html=True)
            st.caption(f"Unexplained remainder: {num(c.get('unexplained_pp'), '{:+.2f}')}pp")

# ---------------------------------------------------------------- CRIME NETWORK
elif page == "Crime Network":
    nw = R.get("NETWORK") or {}
    head("Transformer Crime Network", "Suspicious meters linked through their transformer, their meter reader and synchronized "
                                      f"tampering dates. Link basis in this run: {nw.get('link', 'n/a')}.")
    nodes, edges, rings = D["nodes"], D["edges"], D["rings"]
    if not len(nodes):
        st.info("Run step 8 (python run_all.py --from 8).")
    else:
        nodes = nodes[nodes.zone.isin(ZSEL)]
        rings = rings[rings.zone.isin(ZSEL)].reset_index(drop=True) if len(rings) else rings
        k = st.columns(3)
        kpi(k[0], "Suspicious meters mapped", f"{(nodes.kind == 'meter').sum():,}", "top-ranked by the model")
        kpi(k[1], "Rings detected", f"{len(rings)}", "connected groups of 3 or more meters", ORANGE)
        kpi(k[2], "Energy hidden by rings", f"{num(rings.hidden_kwh_month.sum() / 1e3 if len(rings) else 0, '{:,.0f}')} MWh/mo",
            "estimated from each meter's drop", RED)
        st.write("")
        a, b = st.columns([1.6, 1], gap="medium")
        with b, panel():
            st.markdown("#### Rings")
            st.markdown("<div class='hint'>Select a ring to isolate it on the map.</div>", unsafe_allow_html=True)
            if len(rings):
                rt = rings.drop(columns=["members"]).assign(zone=rings.zone.map(lambda z: zname(z, True)))
                st.dataframe(rt[["ring", "meters", "zone", "drop_window", "hidden_kwh_month", "mean_score"]], **WIDE,
                             hide_index=True, height=440, key="ring_tbl", on_select="rerun", selection_mode="single-row",
                             column_config={"hidden_kwh_month": st.column_config.NumberColumn("kWh hidden / mo", format="%d"),
                                            "mean_score": st.column_config.ProgressColumn("score", min_value=0, max_value=1, format="%.2f"),
                                            "drop_window": "dropped"})
            ri = picked("ring_tbl")
            ring = rings.ring.iloc[ri] if ri is not None and len(rings) > ri else None
        with a, panel():
            st.markdown(f"#### {'Ring ' + ring if ring else 'Network map'}")
            st.markdown("<div class='hint'>Click a red meter to open it in Meter X-Ray. Scroll to zoom.</div>", unsafe_allow_html=True)
            nd = nodes if ring is None else nodes[nodes.ring == ring]
            pos = nd.set_index("id")[["x", "y"]]
            ed = edges[edges.a.isin(pos.index) & edges.b.isin(pos.index)]
            fig = go.Figure()
            for kind, col, w in [("dropped together", "rgba(251,122,60,.28)", 1), ("supplied by", "rgba(16,179,138,.45)", 1.2),
                                 ("read by", "rgba(22,26,58,.35)", 1.2)]:
                e = ed[ed.kind == kind]
                if len(e) > 4000:
                    e = e.sample(4000, random_state=0)
                if not len(e):
                    continue
                xs = np.column_stack([pos.x.reindex(e.a).values, pos.x.reindex(e.b).values, np.full(len(e), np.nan)]).ravel()
                ys = np.column_stack([pos.y.reindex(e.a).values, pos.y.reindex(e.b).values, np.full(len(e), np.nan)]).ravel()
                fig.add_scatter(x=xs, y=ys, mode="lines", line=dict(color=col, width=w), hoverinfo="skip", name=kind)
            m = nd[nd.kind == "meter"]
            if len(m):
                sc = m.score.astype(float)
                fig.add_scatter(x=m.x, y=m.y, mode="markers", name="suspicious meter", customdata=m["id"],
                                marker=dict(size=7 + 11 * (sc - sc.min()) / (sc.max() - sc.min() + 1e-9), color=sc,
                                            colorscale=[[0, "#FFD7C2"], [1, RED]], line=dict(color="#fff", width=1)),
                                text=[f"<b>{i}</b><br>score {s:.3f}, drop {d}<br>{wrap(str(e)[:150], 50)}" for i, s, d, e in
                                      zip(m["id"], sc, m["drop"], m["evidence"].fillna(""))], hovertemplate="%{text}<extra></extra>")
            for kind, col, sym in [("transformer", TEAL, "square"), ("reader", NAVY, "diamond")]:
                h = nd[nd.kind == kind]
                if len(h):
                    fig.add_scatter(x=h.x, y=h.y, mode="markers", name=kind, text=h.id, hovertemplate="%{text}<extra></extra>",
                                    marker=dict(size=13, color=col, symbol=sym, line=dict(color="#fff", width=2)))
            fig.update_xaxes(visible=False)
            fig.update_yaxes(visible=False, scaleanchor="x")
            fig.update_layout(dragmode="pan")
            show(style(fig, 520), key="net_map",
                 on_select=lambda: (mm := picked("net_map")) and go_to("Meter X-Ray", meter=mm))

# ---------------------------------------------------------------- METER X-RAY
elif page == "Meter X-Ray":
    head("Meter X-Ray: explainable AI", "Every score comes with its evidence: the signals that pushed it up, in plain words, "
                                         "against the typical meter.")
    sc = D["scores"]
    if not len(sc):
        st.info("Run step 4 (python run_all.py --from 4).")
    else:
        sc = sc[sc.z.isin(ZSEL)]
        top = sc.dropna(subset=["evidence"]).sort_values("rank")
        opts = top.m.head(500).tolist()
        rank_of = dict(zip(sc.m, sc["rank"]))
        if st.session_state.get("meter") not in rank_of:
            st.session_state["meter"] = opts[0] if opts else sc.sort_values("rank").m.iloc[0]
        if st.session_state["meter"] not in opts:
            opts = [st.session_state["meter"]] + opts
        c1, c2 = st.columns([1, 2])
        q = c1.text_input("Search a meter serial", placeholder="e.g. NG-ZN11-1000103").strip()
        if q and q in rank_of and q != st.session_state.get("_last_q"):
            st.session_state["_last_q"] = q
            st.session_state["meter"] = q
            opts = [q] + [o for o in opts if o != q]
        elif q and q not in rank_of:
            c1.caption("Not found in this selection.")
        pick = c2.selectbox("Top suspects", opts, key="meter",
                            format_func=lambda x: f"{x}  (rank {int(rank_of[x]):,})" if x in rank_of else x)
        r_ = sc[sc.m == pick].iloc[0]
        a, b = st.columns([1, 1.7], gap="medium")
        with a, panel():
            fig = go.Figure(go.Indicator(mode="gauge+number", value=float(r_.raw) * 100, number=dict(font=dict(size=38), suffix=""),
                                         gauge=dict(axis=dict(range=[0, 100], tickwidth=0), bar=dict(color=ORANGE, thickness=.28),
                                                    bgcolor="#fff", borderwidth=0,
                                                    steps=[dict(range=[0, 60], color="#EEF0F6"), dict(range=[60, 85], color=PEACH),
                                                           dict(range=[85, 100], color="#FFC9B0")])))
            show(style(fig, 210, legend=False).update_layout(margin=dict(l=24, r=24, t=16, b=0)))
            st.markdown(f"<div style='text-align:center;margin-top:-10px'><b>Tampering score</b> &middot; rank {int(r_['rank']):,} "
                        f"of {len(D['scores']):,}</div>", unsafe_allow_html=True)
            pills = [(zname(r_.z), "#DDF6EE", TEAL), (f"drop {str(r_.drop_mo)[:7]}", PEACH, ORANGE)]
            if isinstance(r_.get("t"), str):
                pills.append((r_.t, "#E8EAF6", NAVY))
            if r_.get("confirmed") == 1:
                pills.append(("confirmed theft", "#FDE2E3", RED))
            st.markdown("<div style='text-align:center'>" + "".join(f"<span class='pill' style='background:{bg};color:{fg}'>{t}</span>"
                                                                   for t, bg, fg in pills) + "</div>", unsafe_allow_html=True)
            st.markdown("#### Why this meter")
            evs = [e for e in str(r_.evidence).split(" | ") if e and e != "nan"]
            for i, e in enumerate(evs):
                st.markdown(f"<div class='ev{' lead' if i == 0 else ''}'>{e}</div>", unsafe_allow_html=True)
            if not evs:
                st.caption("Evidence is written for the top-ranked meters only.")
        with b, panel():
            st.markdown("#### Monthly consumption against its neighbours")
            x = D["xray"]
            xm = x[x.m == pick].sort_values("mo") if len(x) else pd.DataFrame()
            if len(xm):
                dm = str(r_.drop_mo)[:7]
                fig = go.Figure()
                fig.add_bar(x=xm.mo, y=xm.kwh, name="This meter (kWh)",
                            marker_color=[ORANGE if str(m_)[:7] == dm else PEACH for m_ in xm.mo])
                fig.add_scatter(x=xm.mo, y=xm.peer_med, name="Typical neighbour (kWh)", line=dict(color=TEAL, width=3, shape="spline"))
                fig.add_scatter(x=xm.mo, y=xm.pk_share * 100, name="Peak-hour share %", yaxis="y2", line=dict(color=NAVY, dash="dot"))
                fig.update_layout(hovermode="x unified", yaxis_title="kWh / month",
                                  yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Peak %"))
                show(style(fig, 330))
                fig = go.Figure()
                fig.add_scatter(x=xm.mo, y=xm.v_mean, name="Voltage (V)", line=dict(color=NAVY))
                fig.add_bar(x=xm.mo, y=xm.n_miss, name="Days with no reading", yaxis="y2", marker_color="rgba(229,72,77,.45)")
                fig.update_layout(hovermode="x unified", yaxis_title="V", yaxis2=dict(overlaying="y", side="right", showgrid=False, title="days"))
                show(style(fig, 210))
            else:
                st.caption("Monthly detail is stored for the top suspects only.")
        with panel():
            st.markdown("#### Top suspects with their evidence")
            st.markdown("<div class='hint'>Select a row to X-ray that meter.</div>", unsafe_allow_html=True)
            tt = top.head(200)[["rank", "m", "z", "raw", "drop_mo", "evidence"]].reset_index(drop=True)
            st.dataframe(tt, **WIDE, hide_index=True, height=360, key="xr_tbl", selection_mode="single-row",
                         on_select=lambda: (i := picked("xr_tbl")) is not None and st.session_state.update(meter=tt.m.iloc[i]),
                         column_config={"raw": st.column_config.ProgressColumn("score", min_value=0, max_value=1, format="%.3f"),
                                        "m": "meter", "z": "zone", "drop_mo": "drop month",
                                        "evidence": st.column_config.TextColumn("evidence", width="large")})

# ---------------------------------------------------------------- SUB-DIVISIONS
elif page == "Sub-divisions":
    head("Sub-divisions", f"Where it went wrong, and when. Showing {SCOPE}.")
    if len(ZM):
        with panel():
            st.markdown("#### Loss vs the same month of FY2023-24 (pp)")
            piv = ZM.pivot_table(index="z", columns=ZM.mo.dt.strftime("%Y-%m"), values="yoy_vs_fy24_pp")
            piv = piv.loc[:, [c for c in piv.columns if c >= "2024-07"]]
            fig = go.Figure(go.Heatmap(z=piv.values, x=piv.columns, y=[zname(z) for z in piv.index], xgap=2, ygap=2,
                                       colorscale=[[0, "#FFFFFF"], [0.5, PEACH], [1, ORANGE]], zmin=0,
                                       hovertemplate="%{y}<br>%{x}: %{z:+.2f}pp<extra></extra>", colorbar=dict(title="pp", thickness=12)))
            fig.update_xaxes(tickangle=-45, nticks=12)
            show(style(fig, 90 + 34 * len(piv), legend=False))
        a, b = st.columns(2, gap="medium")
        with a, panel():
            st.markdown("#### Billed units / smart-meter kWh")
            fig = go.Figure()
            for i, (z, g) in enumerate(ZM.groupby("z")):
                fig.add_scatter(x=g.mo, y=g.billed_over_ami, name=zname(z, True), mode="lines",
                                line=dict(width=2.5, shape="spline", color=PALETTE[ALL_Z.index(z) % 8]),
                                hovertemplate=zname(z, True) + " %{x|%b %Y}: %{y:.3f}<extra></extra>")
            fig.add_hline(y=1, line_dash="dot", line_color=MUTED)
            show(style(fig, 340).update_yaxes(title="ratio"))
        with b, panel():
            st.markdown("#### Loss % by fiscal year")
            st.markdown("<div class='hint'>Select a row to open that sub-division's case file.</div>", unsafe_allow_html=True)
            t = D["b1"][D["b1"].z.isin(ZSEL)].reset_index(drop=True) if len(D["b1"]) else D["b1"]
            if len(t):
                t = t.assign(month_went_wrong=t.month_went_wrong.fillna("no sustained break"),
                             upgrade=t.z.map(lambda z: VERS.get(z, {}).get("golive") or "none"))
                st.dataframe(t.assign(z=t.z.map(zname)), **WIDE, hide_index=True, key="b1_tbl",
                             selection_mode="single-row",
                             on_select=lambda: (i := picked("b1_tbl")) is not None and go_to("Loss Detective", case=t.z.iloc[i]),
                             column_config={"z": "sub-division", "pp_change_24_to_26": st.column_config.NumberColumn("change pp", format="%+.2f"),
                                            "month_went_wrong": "went wrong", "upgrade": "billing v5.2"})
            b4, b3 = R.get("B4") or {}, R.get("B3") or {}
            st.markdown(f"<div class='ev'><b>B4: new network area</b><br>FY2025-26 loss {num(b4.get('fy26_loss_with'), '{:.2f}')}% with it, "
                        f"{num(b4.get('fy26_loss_without'), '{:.2f}')}% without; the new area's own loss "
                        f"{num(b4.get('new_area_loss'), '{:.2f}')}%.</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='ev'><b>B3: load-shedding</b><br>{b3.get('verdict') or 'See ANSWERS.md'}</div>", unsafe_allow_html=True)

# ---------------------------------------------------------------- RECOVERY SIMULATOR
elif page == "Recovery Simulator":
    head("Revenue Recovery Simulator", f"What Monday's decisions are worth for {SCOPE}. Move the sliders.")
    gap = pd.DataFrame(R.get("C1_billing_gap") or [])
    tariff = list((C3.get("avg_tariff_pkr_per_kwh_ex_gst") or {"x": 40}).values())[-1]
    gap_kwh = gap[gap.z.isin(ZSEL)].unbilled_kwh_since_golive.fillna(0).sum() if len(gap) else 0
    a, b = st.columns([1, 1.5], gap="medium")
    with a, panel():
        st.markdown("#### Decisions")
        rec = st.slider("Metered-but-unbilled units re-billed (%)", 0, 100, 70, 5)
        insp = st.slider("Vigilance raids next month", 100, 2000, 500, 50)
        prec = st.slider("Model precision in the raided meters (%)", 10, 100, 60, 5)
        det = st.slider("Detection units billed per confirmed theft (kWh)", 200, 5000, 1500, 100)
        fix = st.toggle("Fix the billing software for the next 12 months", True)
    up = ZM[ZM.z.isin([z for z, v in VERS.items() if v.get("golive")])]
    last12 = up.sort_values("mo").groupby("z").tail(12)
    future = ((last12.ami_kwh * (1 - last12.billed_over_ami.clip(upper=1))).sum() if len(last12) else 0) * tariff / 1e6
    v1, v2, v3 = gap_kwh * tariff / 1e6 * rec / 100, insp * prec / 100 * det * tariff / 1e6, future if fix else 0
    with b, panel():
        st.markdown("#### PKR million recoverable or avoidable")
        log = st.toggle("Log scale (so small levers stay visible)", True)
        lev = pd.Series({"Re-bill the gap": v1, "Vigilance raids": v2, "Stop the leak (12 months)": v3, "Total": v1 + v2 + v3})
        fig = go.Figure(go.Bar(y=lev.index, x=lev.clip(lower=0.01).values, orientation="h",
                               marker_color=[TEAL, ORANGE, TEAL, NAVY], text=[f"PKR {v:,.1f} mn" for v in lev.values],
                               textposition="outside", cliponaxis=False, hovertemplate="%{y}: PKR %{x:,.1f} mn<extra></extra>"))
        fig.update_yaxes(autorange="reversed")
        if log:
            fig.update_xaxes(type="log", range=[np.log10(max(lev.clip(lower=0.01).min() / 3, 0.01)), np.log10(lev.max() * 6)])
        else:
            fig.update_xaxes(range=[0, lev.max() * 1.3])
        show(style(fig, 330, legend=False).update_xaxes(title="PKR million"))
    k = st.columns(4)
    kpi(k[3], "Vigilance raids recover", f"PKR {v2:,.1f} mn", f"{insp * prec / 100:,.0f} thefts x {det:,} kWh", ORANGE)
    kpi(k[0], "Total", f"PKR {v1 + v2 + v3:,.0f} mn", f"at PKR {tariff:.2f}/kWh ex-GST", TEAL)
    kpi(k[1], "Unbilled energy in scope", f"{gap_kwh / 1e6:,.1f} GWh", "metered by AMI, never billed", ORANGE)
    kpi(k[2], "Expected thefts caught", f"{insp * prec / 100:,.0f}", f"from {insp:,} raids", NAVY)

# ---------------------------------------------------------------- DATA TRUST
elif page == "Data Trust":
    head("Data Trust: why IT's number is wrong", "Each bar is one fix applied to the raw extract, in order. Company-wide.")
    br = D["bridge"]
    if len(br):
        fys = sorted(br.fy.unique())
        fy = st.segmented_control("Fiscal year", fys, default=fys[-1]) or fys[-1]
        s = br[br.fy == fy].sort_values("step")
        vals = s.loss_pct.values
        with panel():
            fig = go.Figure(go.Waterfall(x=[wrap(x[3:], 18) for x in s.step], measure=["absolute"] + ["relative"] * (len(vals) - 2) + ["total"],
                                         y=[vals[0]] + list(np.diff(vals))[:-1] + [0],
                                         text=[f"{vals[0]:.1f}%"] + [f"{d:+.1f}" for d in np.diff(vals)[:-1]] + [f"{vals[-1]:.1f}%"],
                                         textposition="outside", cliponaxis=False,
                                         increasing=dict(marker=dict(color=ORANGE)), decreasing=dict(marker=dict(color=TEAL)),
                                         totals=dict(marker=dict(color=NAVY)), connector=dict(line=dict(color="#DDE0EA"))))
            fig.update_yaxes(title="Loss %", range=[0, max(vals) * 1.25])
            show(style(fig, 420, legend=False).update_layout(margin=dict(t=30)))
    with panel():
        st.markdown("#### Data-quality log (A2)")
        dq = D["dq"]
        if len(dq):
            imp = st.segmented_control("Impact", ["high", "medium", "low"], selection_mode="multi", default=["high", "medium", "low"])
            dq = dq[dq.impact.isin(imp or ["high", "medium", "low"])]
            dq = dq.assign(problem=dq.problem.str.replace(r"\{'(\w+)': '(\w+)'\}", r"\1 to \2", regex=True))
            st.dataframe(dq, **WIDE, hide_index=True,
                         column_config={"rows_affected": st.column_config.NumberColumn("rows", format="%d"),
                                        "problem": st.column_config.TextColumn(width="large"), "fix": st.column_config.TextColumn(width="large")})

# ---------------------------------------------------------------- PITCH
else:
    head("Three minutes for the Board")
    p = OUT / "PITCH.md"
    with panel():
        st.markdown(p.read_text() if p.exists() else "Run step 6 to generate the pitch.")
