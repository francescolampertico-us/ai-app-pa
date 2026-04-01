"""
Stakeholder Map — Network Graph Builder
=========================================
Builds an interactive Plotly network graph from classified actors and relationships.
Node color = stance, node size = influence tier, node symbol = stakeholder type.
Edge style = relationship type.
"""

import sys

try:
    import networkx as nx
    HAS_NX = True
except ImportError:
    HAS_NX = False

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


# ── Visual encoding ──────────────────────────────────────────────────────────

STANCE_COLOR = {
    "proponent": "#2ecc71",   # green
    "opponent":  "#e74c3c",   # red
    "neutral":   "#95a5a6",   # gray
    "unknown":   "#3498db",   # blue
}

TIER_SIZE = {
    "high":   28,
    "medium": 18,
    "low":    11,
}

# Plotly marker symbols for stakeholder types
TYPE_SYMBOL = {
    "legislator":  "circle",
    "corporation": "square",
    "nonprofit":   "diamond",
    "lobbyist":    "triangle-up",
    "coalition":   "star",
    "other":       "circle-open",
}

EDGE_DASH = {
    "lobbies_for": "dot",
    "co_sponsors": "solid",
}

EDGE_COLOR = {
    "lobbies_for": "#aaaaaa",
    "co_sponsors": "#2980b9",
}


# ── Graph builder ────────────────────────────────────────────────────────────

def build_network_graph(
    actors: list[dict],
    relationships: list[dict],
    title: str = "",
) -> "go.Figure":
    """
    Build an interactive Plotly network graph from actors and relationships.

    Args:
        actors:        Classified actor dicts (must have 'id' field).
        relationships: Relationship dicts with from_id, to_id, type, label.
        title:         Graph title (displayed at top).

    Returns:
        A plotly Figure object. Use st.plotly_chart() in Streamlit or
        fig.write_html() to export.
    """
    if not HAS_NX or not HAS_PLOTLY:
        missing = []
        if not HAS_NX:
            missing.append("networkx")
        if not HAS_PLOTLY:
            missing.append("plotly")
        raise ImportError(f"Missing required packages: {', '.join(missing)}. Run: pip install {' '.join(missing)}")

    if not actors:
        return _empty_figure(title or "No actors to display")

    # Build networkx graph for layout
    G = nx.Graph()
    actor_by_id = {a["id"]: a for a in actors}

    for actor in actors:
        G.add_node(actor["id"])

    for rel in relationships:
        fid = rel.get("from_id", "")
        tid = rel.get("to_id", "")
        if fid in actor_by_id and tid in actor_by_id:
            G.add_edge(fid, tid, rel_type=rel.get("type", ""), label=rel.get("label", ""))

    # Spring layout — reproducible seed
    pos = nx.spring_layout(G, k=2.2, seed=42)

    # ── Edge traces (one per relationship type for legend grouping) ──────────
    edge_traces = _build_edge_traces(G, pos, actor_by_id)

    # ── Node trace ───────────────────────────────────────────────────────────
    node_x, node_y, node_text, node_hover = [], [], [], []
    node_colors, node_sizes, node_symbols = [], [], []

    for actor in actors:
        aid = actor["id"]
        if aid not in pos:
            continue
        x, y = pos[aid]
        node_x.append(x)
        node_y.append(y)

        stance = actor.get("stance", "unknown")
        tier = actor.get("influence_tier", "low")
        atype = actor.get("stakeholder_type", "other")

        node_colors.append(STANCE_COLOR.get(stance, "#3498db"))
        node_sizes.append(TIER_SIZE.get(tier, 11))
        node_symbols.append(TYPE_SYMBOL.get(atype, "circle"))

        # Short label on node
        name = actor.get("name", "")
        label = name if len(name) <= 22 else name[:19] + "…"
        node_text.append(label)

        # Rich hover text
        evidence = actor.get("evidence", "")
        if evidence and len(evidence) > 100:
            evidence = evidence[:97] + "…"
        org = actor.get("organization", "")
        lda = actor.get("lda_amount")
        lda_str = f"${lda:,.0f}" if lda else "—"

        hover_lines = [
            f"<b>{name}</b>",
            f"Type: {atype.title()}",
        ]
        if org and org != name:
            hover_lines.append(f"Org: {org}")
        hover_lines += [
            f"Stance: {stance.title()}",
            f"Influence: {tier.title()}",
            f"LDA Spend: {lda_str}",
        ]
        if evidence:
            hover_lines.append(f"Evidence: {evidence}")
        node_hover.append("<br>".join(hover_lines))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        hoverinfo="text",
        text=node_text,
        hovertext=node_hover,
        textposition="top center",
        textfont=dict(size=9, color="#333333"),
        marker=dict(
            color=node_colors,
            size=node_sizes,
            symbol=node_symbols,
            line=dict(color="#ffffff", width=1.5),
            opacity=0.9,
        ),
        showlegend=False,
    )

    # ── Legend traces (stance colors) ────────────────────────────────────────
    legend_traces = _build_legend_traces()

    # ── Assemble figure ──────────────────────────────────────────────────────
    all_traces = edge_traces + legend_traces + [node_trace]

    fig = go.Figure(
        data=all_traces,
        layout=go.Layout(
            title=dict(
                text=title or "Stakeholder Map",
                font=dict(size=15, color="#1a1a2e"),
                x=0.5,
            ),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
                font=dict(size=11),
            ),
            hovermode="closest",
            margin=dict(b=80, l=20, r=20, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor="#fafafa",
            paper_bgcolor="#ffffff",
            height=600,
        ),
    )

    # Annotation for type symbols legend
    fig.add_annotation(
        text=(
            "<b>Node shapes:</b> ● Legislator  ■ Corporation  ◆ Nonprofit  "
            "▲ Lobbyist  ★ Coalition<br>"
            "<b>Node size:</b> Influence tier (large=high)  "
            "<b>Edges:</b> ··· lobbies-for  — co-sponsors"
        ),
        xref="paper", yref="paper",
        x=0.5, y=-0.22,
        showarrow=False,
        font=dict(size=9, color="#555555"),
        align="center",
    )

    return fig


def save_graph_html(fig: "go.Figure", output_path: str) -> None:
    """Export the graph as a standalone HTML file (CDN-linked Plotly)."""
    fig.write_html(output_path, include_plotlyjs="cdn")


# ── Private helpers ──────────────────────────────────────────────────────────

def _build_edge_traces(G, pos, actor_by_id: dict) -> list:
    """Build one scatter trace per edge, colored by relationship type."""
    traces = []
    edge_type_shown: set = set()

    for u, v, data in G.edges(data=True):
        if u not in pos or v not in pos:
            continue

        x0, y0 = pos[u]
        x1, y1 = pos[v]
        rel_type = data.get("rel_type", "")
        label = data.get("label", rel_type.replace("_", " "))

        color = EDGE_COLOR.get(rel_type, "#cccccc")
        dash = EDGE_DASH.get(rel_type, "solid")
        show_legend = rel_type not in edge_type_shown
        if show_legend:
            edge_type_shown.add(rel_type)

        legend_name = {
            "lobbies_for": "Lobbies-for",
            "co_sponsors": "Co-sponsors",
        }.get(rel_type, rel_type.replace("_", " ").title())

        hover_from = actor_by_id.get(u, {}).get("name", u)
        hover_to = actor_by_id.get(v, {}).get("name", v)

        trace = go.Scatter(
            x=[x0, x1, None],
            y=[y0, y1, None],
            mode="lines",
            line=dict(width=1.5, color=color, dash=dash),
            hoverinfo="text",
            hovertext=f"{hover_from} → {hover_to}<br>{label}",
            legendgroup=rel_type,
            showlegend=show_legend,
            name=legend_name,
        )
        traces.append(trace)

    return traces


def _build_legend_traces() -> list:
    """Build invisible marker traces used only to display the stance color legend."""
    legend_items = [
        ("Proponent", STANCE_COLOR["proponent"]),
        ("Opponent",  STANCE_COLOR["opponent"]),
        ("Neutral",   STANCE_COLOR["neutral"]),
        ("Unknown",   STANCE_COLOR["unknown"]),
    ]
    traces = []
    for name, color in legend_items:
        traces.append(go.Scatter(
            x=[None], y=[None],
            mode="markers",
            marker=dict(size=10, color=color),
            name=name,
            showlegend=True,
            legendgroup=f"stance_{name}",
        ))
    return traces


def _empty_figure(message: str) -> "go.Figure":
    """Return a blank figure with a centered message."""
    return go.Figure(
        layout=go.Layout(
            title=dict(text=message, x=0.5),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            height=400,
        )
    )
