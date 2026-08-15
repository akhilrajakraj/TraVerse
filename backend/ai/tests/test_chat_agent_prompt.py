from django.test import SimpleTestCase

from ai.prompts.chat_agent_v1 import chat_agent_prompt_v1


class ChatAgentPromptTests(SimpleTestCase):
    def test_trip_context_is_rendered_before_user_message(self):
        prompt = chat_agent_prompt_v1.render_user_prompt(
            conversation_context="User: hello",
            trip_context=(
                "Trip Data (authoritative application data):\n"
                "Title: Japan Tour\n"
                "Dates: 2026-09-10 to 2026-09-15\n"
                "Budget:\n"
                "Computed budget total: 450.00"
            ),
            user_message="Can you estimate the cost of this trip?",
            retrieved_destinations=[],
        )

        trip_index = prompt.index("Authoritative Trip Data:")
        history_index = prompt.index("Conversation History:")
        message_index = prompt.index("Latest User Message:")

        self.assertLess(trip_index, history_index)
        self.assertLess(history_index, message_index)
        self.assertIn("Japan Tour", prompt)
        self.assertIn("Computed budget total: 450.00", prompt)
        self.assertIn("Can you estimate the cost of this trip?", prompt)

    def test_empty_trip_context_is_explicit(self):
        prompt = chat_agent_prompt_v1.render_user_prompt(
            conversation_context="No previous conversation.",
            trip_context="",
            user_message="What is my destination?",
            retrieved_destinations=[],
        )

        self.assertIn("No trip data is available.", prompt)
