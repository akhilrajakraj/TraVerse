from ai.prompts.planner_v1 import travel_planner_prompt_v1


def test_travel_planner_prompt_declares_the_actual_itinerary_shape():
    prompt = travel_planner_prompt_v1.render_user_prompt(
        trip_title="Summer in Tokyo",
        destination_names=["Tokyo"],
        start_date="2026-08-13",
        end_date="2026-08-15",
        traveler_count=2,
        trip_notes="Food and culture",
    )

    assert '"days": [' in travel_planner_prompt_v1.system_prompt
    assert '"day_number": 1' in travel_planner_prompt_v1.system_prompt
    assert '"items": [' in travel_planner_prompt_v1.system_prompt
    assert '"title": "Activity title"' in travel_planner_prompt_v1.system_prompt
    assert '"tripTitle"' in travel_planner_prompt_v1.system_prompt
    assert "Return ONLY one JSON object" in prompt
    assert "Do not return the schema definition itself" in prompt


def test_travel_planner_prompt_keeps_trip_content_delimited():
    prompt = travel_planner_prompt_v1.render_user_prompt(
        trip_title="Summer in Tokyo",
        destination_names=["Tokyo"],
        start_date="2026-08-13",
        end_date="2026-08-15",
        traveler_count=2,
        trip_notes="Food and culture",
    )

    assert "Summer in Tokyo" in prompt
    assert "Food and culture" in prompt
    assert "Tokyo" in prompt
