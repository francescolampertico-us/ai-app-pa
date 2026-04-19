"""
Stakeholder Map Builder — Network Analytics
============================================
Computes Social Network Analysis metrics per the Varone, Ingold & Jourdain (2016)
framework: "Studying Policy Advocacy Through Social Network Analysis."

Key metrics:
  - Degree centrality         → coalition reach (direct connections)
  - Betweenness centrality    → brokerage / bridge role between coalitions
  - Community structure       → structural clusters (may differ from stance labels)
  - Multi-venue presence      → actors active across both LDA and LegiScan venues
  - Coalition cohesion        → internal edge density per stance group
  - Composite influence score → weighted blend of tier, centrality, and LDA spend

No LLM calls. Pure networkx computation — runs in under 1 second on typical maps.
"""

import math
import networkx as nx
from networkx.algorithms.community import greedy_modularity_communities


def _source_priority(actor: dict) -> tuple[int, int]:
    source_names = set(actor.get("source_names") or [])
    if "LegiScan" in source_names:
        return (0, 0)
    if "LDA" in source_names:
        return (1, 0)
    if actor.get("source") == "seeded" or "seeded" in source_names:
        return (2, 0)
    if "brave" in source_names:
        return (3, 0)
    return (4, 0)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def compute_network_analytics(
    actors: list[dict],
    relationships: list[dict],
) -> dict:
    """
    Compute SNA metrics for the stakeholder map.

    Enriches each actor dict in-place with:
      - degree_centrality        (float 0-1)
      - betweenness_centrality   (float 0-1)
      - community_id             (int)
      - composite_score          (int 0-100)

    Returns a top-level analytics dict.
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

    # ── Composite influence score ─────────────────────────────────────────────
    _compute_composite_scores(actors)

    # ── Broker identification ─────────────────────────────────────────────────
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
            nbrs = set(G.neighbors(aid))
            if (nbrs & proponent_ids) and (nbrs & opponent_ids):
                brokers.append({
                    "id": aid,
                    "name": actor.get("name", ""),
                    "stakeholder_type": actor.get("stakeholder_type", ""),
                    "stance": actor.get("stance", ""),
                    "betweenness_centrality": round(bw, 3),
                    "degree_centrality": round(degree.get(aid, 0.0), 3),
                    "organization": actor.get("organization", ""),
                    "composite_score": actor.get("composite_score", 0),
                    "evidence": actor.get("evidence", ""),
                })
        brokers.sort(key=lambda b: -b["betweenness_centrality"])

    # ── Network density ───────────────────────────────────────────────────────
    density = round(nx.density(G), 3)

    # ── Isolated actors ───────────────────────────────────────────────────────
    isolated = [a for a in actors if degree.get(a["id"], 0) == 0]

    # ── Multi-venue actors ────────────────────────────────────────────────────
    lda_ids = {a["id"] for a in actors if (a.get("lda_amount") or 0) > 0}
    leg_ids = {a["id"] for a in actors if a.get("bill_numbers")}
    nbr_map: dict[str, set] = {a["id"]: set() for a in actors}
    for rel in relationships:
        fid, tid = rel.get("from_id", ""), rel.get("to_id", "")
        if fid in nbr_map:
            nbr_map[fid].add(tid)
        if tid in nbr_map:
            nbr_map[tid].add(fid)
    multi_venue = [
        a for a in actors
        if (nbr_map[a["id"]] & lda_ids) and (nbr_map[a["id"]] & leg_ids)
    ]

    # ── Coalition cohesion ────────────────────────────────────────────────────
    cohesion = _compute_coalition_cohesion(actors, relationships)

    # ── Centrality rankings ───────────────────────────────────────────────────
    top_by_betweenness = sorted(
        actors, key=lambda a: (-(a.get("betweenness_centrality", 0) or 0),) + _source_priority(a)
    )[:5]
    top_by_degree = sorted(
        actors, key=lambda a: (-(a.get("degree_centrality", 0) or 0),) + _source_priority(a)
    )[:5]

    # ── Engagement priorities ─────────────────────────────────────────────────
    # Ranked by structured-source priority first, then composite_score.
    def _priority_key(a):
        return _source_priority(a) + (-(a.get("composite_score", 0) or 0),)

    top_opponents = sorted(
        [a for a in actors if a.get("stance") == "opponent"],
        key=_priority_key,
    )[:5]
    top_proponents = sorted(
        [a for a in actors if a.get("stance") == "proponent"],
        key=_priority_key,
    )[:5]
    # Swing actors: neutral/unknown with meaningful network position
    # Prioritise: high betweenness (structurally positioned) first, then composite score
    top_persuadables = sorted(
        [
            a for a in actors
            if a.get("stance") in ("neutral", "unknown")
            and (a.get("composite_score", 0) >= 20 or a.get("betweenness_centrality", 0) > 0)
        ],
        key=lambda a: _source_priority(a) + (-(a.get("betweenness_centrality") or 0), -(a.get("composite_score", 0) or 0)),
    )[:5]

    # ── Strategic summary (deterministic, always available) ───────────────────
    strategic_summary = _build_strategic_summary(
        actors=actors,
        brokers=brokers,
        density=density,
        num_communities=num_communities,
        multi_venue=multi_venue,
        has_both_sides=has_both_sides,
        has_edges=has_edges,
        cohesion=cohesion,
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
        "top_opponents": top_opponents,
        "top_proponents": top_proponents,
        "top_persuadables": top_persuadables,
        "coalition_cohesion": cohesion,
    }


# ---------------------------------------------------------------------------
# Composite score
# ---------------------------------------------------------------------------

def _compute_composite_scores(actors: list[dict]) -> None:
    """
    Add composite_score (int 0–100) to each actor in-place.

    Weights:
      35% — influence tier (high=1.0, medium=0.6, low=0.2)
      30% — betweenness centrality (0–1, already normalised)
      20% — degree centrality (0–1, already normalised)
      15% — log-normalised LDA spend
    """
    tier_map = {"high": 1.0, "medium": 0.6, "low": 0.2}
    lda_vals = [math.log1p(a.get("lda_amount") or 0) for a in actors]
    max_lda_log = max(lda_vals) if lda_vals else 1.0

    for actor, lda_log in zip(actors, lda_vals):
        inf = tier_map.get(actor.get("influence_tier", "low"), 0.2)
        bw = actor.get("betweenness_centrality") or 0.0
        deg = actor.get("degree_centrality") or 0.0
        lda_norm = lda_log / max(max_lda_log, 1e-9)

        raw = (inf * 0.35) + (bw * 0.30) + (deg * 0.20) + (lda_norm * 0.15)
        actor["composite_score"] = round(raw * 100)


# ---------------------------------------------------------------------------
# Coalition cohesion
# ---------------------------------------------------------------------------

def _compute_coalition_cohesion(
    actors: list[dict],
    relationships: list[dict],
) -> dict:
    """
    For proponents and opponents, compute internal edge density (0–1).
    Higher = more tightly coordinated coalition.
    """
    stance_ids: dict[str, set] = {}
    for a in actors:
        s = a.get("stance", "unknown")
        stance_ids.setdefault(s, set()).add(a["id"])

    result: dict = {}
    for stance in ("proponent", "opponent"):
        ids = stance_ids.get(stance, set())
        n = len(ids)
        if n < 2:
            result[f"{stance}_cohesion"] = 0.0
            result[f"{stance}_cohesion_label"] = "insufficient data"
            continue
        internal = sum(
            1 for r in relationships
            if r.get("from_id") in ids and r.get("to_id") in ids
        )
        max_possible = n * (n - 1) / 2
        cohesion = round(internal / max_possible, 3) if max_possible > 0 else 0.0
        result[f"{stance}_cohesion"] = cohesion
        if cohesion < 0.05:
            label = "fragmented"
        elif cohesion < 0.15:
            label = "loosely coordinated"
        elif cohesion < 0.35:
            label = "moderately cohesive"
        else:
            label = "tightly organised"
        result[f"{stance}_cohesion_label"] = label

    return result


# ---------------------------------------------------------------------------
# Strategic summary (deterministic — no LLM)
# ---------------------------------------------------------------------------

def _build_strategic_summary(
    actors, brokers, density, num_communities, multi_venue,
    has_both_sides, has_edges, cohesion
) -> str:
    parts = []

    if not has_edges:
        parts.append(
            f"The network has {len(actors)} actors but no structural relationships — "
            "Bridge Role cannot be computed."
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
            f"and opponent coalitions. {top['name']} has the highest Bridge Role "
            f"({top['betweenness_centrality']:.2f}), indicating a pivotal brokerage position."
        )
    else:
        parts.append(
            "No actors currently bridge the proponent and opponent coalitions directly — "
            "the two sides operate in largely separate networks."
        )

    if has_edges:
        if density < 0.05:
            density_desc = "very sparse"
        elif density < 0.15:
            density_desc = "sparse"
        elif density < 0.30:
            density_desc = "moderate"
        else:
            density_desc = "dense"
        parts.append(
            f"Network density is {density:.3f} ({density_desc}), with {num_communities} "
            f"structural {'community' if num_communities == 1 else 'communities'} detected."
        )

    # Coalition cohesion comparison
    pc = cohesion.get("proponent_cohesion", 0)
    oc = cohesion.get("opponent_cohesion", 0)
    pl = cohesion.get("proponent_cohesion_label", "")
    ol = cohesion.get("opponent_cohesion_label", "")
    if pl and ol:
        parts.append(
            f"Proponent coalition is {pl} (cohesion {pc:.2f}); "
            f"opponent coalition is {ol} (cohesion {oc:.2f})."
        )

    if multi_venue:
        names = ", ".join(a["name"] for a in multi_venue[:3])
        parts.append(
            f"{len(multi_venue)} actor(s) are active in both LDA and legislative venues "
            f"({names}{'…' if len(multi_venue) > 3 else ''})."
        )

    return " ".join(parts) if parts else "Insufficient relationship data for network analysis."


# ---------------------------------------------------------------------------
# Empty fallback
# ---------------------------------------------------------------------------

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
        "top_opponents": [],
        "top_proponents": [],
        "top_persuadables": [],
        "coalition_cohesion": {
            "proponent_cohesion": 0.0,
            "proponent_cohesion_label": "insufficient data",
            "opponent_cohesion": 0.0,
            "opponent_cohesion_label": "insufficient data",
        },
    }
