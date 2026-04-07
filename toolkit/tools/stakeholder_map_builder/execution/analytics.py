"""
Stakeholder Map Builder — Network Analytics
============================================
Computes Social Network Analysis metrics per the Varone, Ingold & Jourdain (2016)
framework: "Studying Policy Advocacy Through Social Network Analysis."

Key metrics:
  - Degree centrality    → coalition reach (direct connections)
  - Betweenness centrality → brokerage / bridge role between coalitions
  - Community structure  → structural clusters (may differ from stance labels)
  - Multi-venue presence → actors active across both LDA and LegiScan venues

No API calls. Pure networkx computation — runs in under 1 second on typical maps.
"""

import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities


def compute_network_analytics(
    actors: list[dict],
    relationships: list[dict],
) -> dict:
    """
    Compute SNA metrics for the stakeholder map.

    Enriches each actor dict in-place with:
      - degree_centrality (float 0-1)
      - betweenness_centrality (float 0-1)
      - community_id (int)

    Returns a top-level analytics dict with broker list, community count,
    network density, centrality rankings, and a strategic summary string.
    """
    if not actors:
        return _empty_analytics()

    # ── Build networkx graph ──────────────────────────────────────────────────
    G = nx.Graph()
    actor_ids = {a["id"] for a in actors}
    for actor in actors:
        G.add_node(actor["id"])
    for rel in relationships:
        fid = rel.get("from_id", "")
        tid = rel.get("to_id", "")
        if fid in actor_ids and tid in actor_ids and fid != tid:
            G.add_edge(fid, tid)

    has_edges = G.number_of_edges() > 0

    # ── Centrality metrics ────────────────────────────────────────────────────
    degree = nx.degree_centrality(G)

    if has_edges and G.number_of_nodes() > 2:
        betweenness = nx.betweenness_centrality(G, normalized=True)
    else:
        betweenness = {n: 0.0 for n in G.nodes()}

    # ── Community detection ───────────────────────────────────────────────────
    node_community: dict[str, int] = {}
    num_communities = 1
    if has_edges:
        try:
            communities = list(greedy_modularity_communities(G))
            num_communities = len(communities)
            for i, community in enumerate(communities):
                for node in community:
                    node_community[node] = i
        except Exception:
            # Fall back gracefully if community detection fails
            for node in G.nodes():
                node_community[node] = 0
    else:
        for node in G.nodes():
            node_community[node] = 0

    # ── Enrich actor dicts in-place ───────────────────────────────────────────
    for actor in actors:
        aid = actor["id"]
        actor["degree_centrality"] = round(degree.get(aid, 0.0), 3)
        actor["betweenness_centrality"] = round(betweenness.get(aid, 0.0), 3)
        actor["community_id"] = node_community.get(aid, 0)

    # ── Broker identification ─────────────────────────────────────────────────
    # Brokers: actors with betweenness > 0 who connect proponent AND opponent sides
    proponent_ids = {a["id"] for a in actors if a.get("stance") == "proponent"}
    opponent_ids = {a["id"] for a in actors if a.get("stance") == "opponent"}
    has_both_sides = bool(proponent_ids) and bool(opponent_ids)

    brokers = []
    if has_both_sides and has_edges:
        for actor in actors:
            aid = actor["id"]
            bw = betweenness.get(aid, 0.0)
            if bw <= 0:
                continue
            neighbors = set(G.neighbors(aid))
            bridges_proponents = bool(neighbors & proponent_ids)
            bridges_opponents = bool(neighbors & opponent_ids)
            if bridges_proponents and bridges_opponents:
                brokers.append({
                    "id": aid,
                    "name": actor.get("name", ""),
                    "stakeholder_type": actor.get("stakeholder_type", ""),
                    "stance": actor.get("stance", ""),
                    "betweenness_centrality": bw,
                    "degree_centrality": degree.get(aid, 0.0),
                    "organization": actor.get("organization", ""),
                })
        brokers.sort(key=lambda b: -b["betweenness_centrality"])

    # ── Network density ───────────────────────────────────────────────────────
    density = round(nx.density(G), 3)

    # ── Isolated actors ───────────────────────────────────────────────────────
    isolated = [a for a in actors if degree.get(a["id"], 0) == 0]

    # ── Multi-venue actors ────────────────────────────────────────────────────
    # An actor is multi-venue if they appear in both LDA and LegiScan data.
    # Proxied by: has lda_amount (LDA) AND has bill_numbers (LegiScan).
    multi_venue = [
        a for a in actors
        if (a.get("lda_amount") and a.get("lda_amount", 0) > 0)
        and a.get("bill_numbers")
    ]

    # ── Centrality rankings ───────────────────────────────────────────────────
    top_by_betweenness = sorted(
        actors, key=lambda a: a.get("betweenness_centrality", 0), reverse=True
    )[:5]
    top_by_degree = sorted(
        actors, key=lambda a: a.get("degree_centrality", 0), reverse=True
    )[:5]

    # ── Strategic summary (deterministic, no LLM) ────────────────────────────
    strategic_summary = _build_strategic_summary(
        actors=actors,
        brokers=brokers,
        density=density,
        num_communities=num_communities,
        multi_venue=multi_venue,
        isolated=isolated,
        has_both_sides=has_both_sides,
        has_edges=has_edges,
    )

    return {
        "actors_with_centrality": actors,
        "brokers": brokers[:5],
        "communities": num_communities,
        "network_density": density,
        "top_by_betweenness": top_by_betweenness,
        "top_by_degree": top_by_degree,
        "isolated_actors": isolated,
        "multi_venue_actors": multi_venue,
        "has_both_sides": has_both_sides,
        "has_edges": has_edges,
        "strategic_summary": strategic_summary,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_strategic_summary(
    actors, brokers, density, num_communities, multi_venue,
    isolated, has_both_sides, has_edges
) -> str:
    parts = []

    # Broker sentence
    if not has_edges:
        parts.append(
            f"The network has {len(actors)} actors but no structural relationships were detected — "
            "betweenness centrality cannot be computed. Add lobbying or co-sponsorship relationships "
            "to enable broker analysis."
        )
    elif not has_both_sides:
        parts.append(
            "No bridge actors can be identified because the network lacks both proponent "
            "and opponent actors — stance classification may need review."
        )
    elif brokers:
        top = brokers[0]
        parts.append(
            f"The network contains {len(brokers)} bridge actor(s) connecting proponent "
            f"and opponent coalitions. {top['name']} has the highest betweenness centrality "
            f"({top['betweenness_centrality']:.2f}), indicating a pivotal brokerage role — "
            "a high-priority engagement target."
        )
    else:
        parts.append(
            "No actors currently bridge the proponent and opponent coalitions directly, "
            "suggesting the two sides operate in separate networks with limited direct exchange."
        )

    # Density sentence
    if has_edges:
        if density < 0.05:
            density_desc = "very sparse — actors are largely operating independently"
        elif density < 0.15:
            density_desc = "sparse — limited formal coordination between actors"
        elif density < 0.30:
            density_desc = "moderate — some coalition structure is forming"
        else:
            density_desc = "dense — indicating tight coalition coordination"
        parts.append(
            f"Network density is {density:.2f} ({density_desc}). "
            f"{num_communities} structural {'community was' if num_communities == 1 else 'communities were'} "
            "detected algorithmically, which may reveal coalitions not captured by stance labels alone."
        )

    # Multi-venue sentence
    if multi_venue:
        names = ", ".join(a["name"] for a in multi_venue[:3])
        parts.append(
            f"{len(multi_venue)} actor(s) are active in both administrative (LDA) and "
            f"legislative (LegiScan) venues ({names}{'…' if len(multi_venue) > 3 else ''}), "
            "consistent with higher-influence multi-venue advocacy per Varone et al. (2016)."
        )

    # Isolated actors sentence
    if isolated:
        parts.append(
            f"{len(isolated)} actor(s) have no recorded relationships and appear structurally "
            "peripheral — they may represent independent actors or data gaps in LDA/LegiScan coverage."
        )

    return " ".join(parts) if parts else "Insufficient relationship data for network analysis."


def _empty_analytics() -> dict:
    return {
        "actors_with_centrality": [],
        "brokers": [],
        "communities": 0,
        "network_density": 0.0,
        "top_by_betweenness": [],
        "top_by_degree": [],
        "isolated_actors": [],
        "multi_venue_actors": [],
        "has_both_sides": False,
        "has_edges": False,
        "strategic_summary": "No actors to analyze.",
    }
