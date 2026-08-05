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
Budget Agent
      │
      ▼
END

Additional planning agents can be added by:

1. Creating a node function.
2. Appending it to WORKFLOW.

The graph assembly logic does not need to change.
"""

from __future__ import annotations

from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from ai.agents.budget_agent import budget_agent
from ai.agents.travel_planner import travel_planner_agent
from ai.agents.weather_agent import weather_agent
from ai.agents.recommendation_agent import recommendation_agent
from ai.agents.packing_agent import packing_agent
from ai.graphs.state import PlanningGraphState


# ==============================================================================
# Graph Nodes
# ==============================================================================


def _travel_planner_node(
    state: PlanningGraphState,
) -> PlanningGraphState:
    """
    Execute the Travel Planner agent.
    """

    return travel_planner_agent.plan(state)


def _budget_agent_node(
    state: PlanningGraphState,
) -> PlanningGraphState:
    """
    Execute the Budget Agent.
    """

    return budget_agent.estimate_budget(state)

def _weather_agent_node(
    state: PlanningGraphState,
) -> PlanningGraphState:
    """
    Execute the Weather Agent.
    """

    return weather_agent.estimate_weather(state)

def _recommendation_agent_node(
    state: PlanningGraphState,
) -> PlanningGraphState:
    """
    Execute the Recommendation Agent.
    """

    return recommendation_agent.generate_recommendations(state)

def _packing_agent_node(
    state: PlanningGraphState,
) -> PlanningGraphState:
    """
    Execute the Packing Agent.
    """

    return packing_agent.generate_packing_list(state)


# ==============================================================================
# Workflow Definition
# ==============================================================================

#
# Future agents should simply be appended here.
#
# Example:
#
# WORKFLOW = [
#     ("travel_planner", _travel_planner_node),
#     ("budget_agent", _budget_agent_node),
#     ("hotel_agent", _hotel_agent_node),
# ]
#

WORKFLOW = [
    (
        "travel_planner",
        _travel_planner_node,
    ),
    (
        "budget_agent",
        _budget_agent_node,
    ),
    (
        "weather_agent",
        _weather_agent_node,
    ),
    (
        "recommendation_agent",
        _recommendation_agent_node,
    ),
    (
        "packing_agent",
        _packing_agent_node,
    ),
]


# ==============================================================================
# Graph Builder
# ==============================================================================


def build_planning_graph():
    """
    Build and compile the AI planning workflow.
    """

    graph = StateGraph(
        PlanningGraphState,
    )

    #
    # Register nodes.
    #
    for node_name, node_function in WORKFLOW:

        graph.add_node(
            node_name,
            node_function,
        )

    #
    # Connect START.
    #
    graph.add_edge(
        START,
        WORKFLOW[0][0],
    )

    #
    # Connect sequential workflow.
    #
    for current, nxt in zip(
        WORKFLOW,
        WORKFLOW[1:],
    ):

        graph.add_edge(
            current[0],
            nxt[0],
        )

    #
    # Connect END.
    #
    graph.add_edge(
        WORKFLOW[-1][0],
        END,
    )

    return graph.compile()


# ==============================================================================
# Public API
# ==============================================================================


def run_planning_graph(
    initial_state: PlanningGraphState,
) -> PlanningGraphState:
    """
    Execute the planning workflow.
    """

    compiled_graph = build_planning_graph()

    return compiled_graph.invoke(
        initial_state,
    )


planning_graph = build_planning_graph()