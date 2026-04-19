"""
Stakeholder Map — Network Graph
===============================
Builds an interactive Plotly network graph from classified actors and relationships.
Node color = stance, node size = influence tier, node symbol = stakeholder type.
Edge style = relationship type.
"""

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


# ── Graph rendering ──────────────────────────────────────────────────────────

def build_network_graph(
    actors: list[dict],
    relationships: list[dict],
    title: str = "",
    centrality: dict = None,
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

    # Stance-grouped layout: proponents left, opponents right, neutral center-left,
    # unknown center-right. Each group uses spring layout driven by ALL its edges
    # (including cross-coalition) so brokers appear pulled toward both sides.
    stance_order = {"proponent": -1.6, "opponent": 1.6, "neutral": -0.4, "unknown": 0.4}
    group_graphs = {s: nx.Graph() for s in stance_order}
    for actor in actors:
        stance = actor.get("stance", "unknown")
        if stance not in group_graphs:
            stance = "unknown"
        group_graphs[stance].add_node(actor["id"])
    # Include all edges in the subgraph of each actor's group (not just same-stance)
    for rel in relationships:
        fid, tid = rel.get("from_id", ""), rel.get("to_id", "")
        fs = actor_by_id.get(fid, {}).get("stance", "unknown")
        ts = actor_by_id.get(tid, {}).get("stance", "unknown")
        # Add edge to both actors' groups so cross-coalition connections affect layout
        for stance in (fs, ts):
            if stance in group_graphs and fid in group_graphs[stance].nodes:
                group_graphs[stance].add_edge(fid, tid)

    pos = {}
    for stance, subG in group_graphs.items():
        if not subG.nodes:
            continue
        x_center = stance_order[stance]
        if len(subG.nodes) == 1:
            sub_pos = {list(subG.nodes)[0]: (0.0, 0.0)}
        else:
            sub_pos = nx.spring_layout(subG, k=1.4, seed=42)
        for nid, (x, y) in sub_pos.items():
            pos[nid] = (x_center + x * 0.6, y)

    # ── Edge traces (one per relationship type for legend grouping) ──────────
    edge_traces = _build_edge_traces(G, pos, actor_by_id)

    # ── Node trace ───────────────────────────────────────────────────────────
    centrality = centrality or {}
    node_x, node_y, node_text, node_hover = [], [], [], []
    node_colors, node_sizes, node_symbols = [], [], []
    node_border_colors, node_border_widths = [], []

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

        # Border: thick gold border for broker actors (high betweenness), white otherwise
        bw_score = centrality.get(aid, actor.get("betweenness_centrality", 0))
        if bw_score > 0.1:
            node_border_colors.append("#f39c12")   # gold = broker
            node_border_widths.append(min(6.0, max(2.5, bw_score * 25)))
        else:
            node_border_colors.append("#ffffff")
            node_border_widths.append(1.5)

        # Short label on node — longer limit so names are readable
        name = actor.get("name", "")
        label = name if len(name) <= 30 else name[:27] + "…"
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
            f"Estimated Influence Tier: {tier.title()}",
            f"LDA Spend: {lda_str}",
        ]
        if actor.get("composite_score") is not None:
            hover_lines.append(f"Strategic Relevance: {actor.get('composite_score')}")
        if actor.get("source_summary"):
            hover_lines.append(f"Source Type: {actor.get('source_summary')}")
        if bw_score > 0:
            hover_lines.append(f"Bridge Role: {bw_score:.2f}")
        degree_score = actor.get("degree_centrality")
        if degree_score is not None:
            hover_lines.append(f"Connection Reach: {float(degree_score):.2f}")
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
            line=dict(color=node_border_colors, width=node_border_widths),
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
            "<b>Layout:</b> Proponents (left) · Neutral (center-left) · Unknown (center-right) · Opponents (right)<br>"
            "<b>Node shapes:</b> ● Legislator  ■ Corporation  ◆ Nonprofit  ▲ Lobbyist  ★ Coalition<br>"
            "<b>Node size:</b> Estimated influence tier (large=high)  "
            "<b>Gold border:</b> Bridge actor (connects both sides)  "
            "<b>Unknown stance:</b> LLM could not determine from available evidence<br>"
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
