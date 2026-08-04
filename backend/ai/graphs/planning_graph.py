"""
LangGraph workflow for AI-powered travel planning.

This module assembles the travel planning graph used by the AI layer.

Current graph:

    START
      │
      ▼
Travel Planner
      │
      ▼
      END

The graph currently contains a single node. Additional planning agents
(weather, budget, recommendations, packing, etc.) can be inserted later
without changing callers.
"""

from __future__ import annotations

from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from ai.agents.travel_planner import travel_planner_agent
from ai.graphs.state import PlanningGraphState


def _travel_planner_node(
    state: PlanningGraphState,
) -> PlanningGraphState:
    """
    Execute the Travel Planner agent.

    The agent returns a new immutable graph state. LangGraph merges the
    returned state into the execution context.
    """

    return travel_planner_agent.plan(state)


def build_planning_graph():
    """
    Build and compile the AI planning workflow.

    Returns
    -------
    CompiledStateGraph
        Executable LangGraph workflow.
    """

    graph = StateGraph(
        PlanningGraphState,
    )

    graph.add_node(
        "travel_planner",
        _travel_planner_node,
    )

    graph.add_edge(
        START,
        "travel_planner",
    )

    graph.add_edge(
        "travel_planner",
        END,
    )

    return graph.compile()


def run_planning_graph(
    initial_state: PlanningGraphState,
) -> PlanningGraphState:
    """
    Execute the planning workflow.

    Parameters
    ----------
    initial_state:
        Initial immutable planning state.

    Returns
    -------
    PlanningGraphState
        Final graph state after execution.
    """

    compiled_graph = build_planning_graph()

    return compiled_graph.invoke(
        initial_state,
    )


planning_graph = build_planning_graph()