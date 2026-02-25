"""Tests for clone_brain.py - system prompt loading and response generation."""

import sys
import os
import importlib
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))


def _reload_brain_module():
    """Force reimport of clone_brain to pick up env changes."""
    mod_name = "clone_brain"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    if f"scripts.{mod_name}" in sys.modules:
        del sys.modules[f"scripts.{mod_name}"]
    return importlib.import_module(mod_name)


class TestSystemPromptLoading:
    """Test that the brain loads system prompt from config file."""

    def test_system_prompt_file_exists(self):
        """The config/clone_system_prompt.txt file should exist."""
        prompt_file = Path(__file__).resolve().parent.parent / "config" / "clone_system_prompt.txt"
        assert prompt_file.exists(), f"System prompt file not found: {prompt_file}"

    def test_system_prompt_has_content(self):
        """The system prompt should have substantial content."""
        prompt_file = Path(__file__).resolve().parent.parent / "config" / "clone_system_prompt.txt"
        content = prompt_file.read_text(encoding="utf-8")
        assert len(content) > 100, "System prompt is too short"
        assert "Jason Tulloch" in content
        assert "Slopify" in content

    def test_system_prompt_has_guidelines(self):
        """The system prompt should include response guidelines."""
        prompt_file = Path(__file__).resolve().parent.parent / "config" / "clone_system_prompt.txt"
        content = prompt_file.read_text(encoding="utf-8")
        assert "Response Guidelines" in content


class TestCloneBrainInit:
    """Test CloneBrain initialization."""

    def test_requires_openai_api_key(self):
        """Should raise ValueError if OPENAI_API_KEY not set."""
        old_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            os.environ["OPENAI_API_KEY"] = ""
            mod = _reload_brain_module()
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                mod.CloneBrain()
        finally:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key

    def test_initializes_with_api_key(self):
        """Should initialize successfully with API key set."""
        os.environ["OPENAI_API_KEY"] = "test-key-123"
        try:
            mod = _reload_brain_module()
            brain = mod.CloneBrain(speak=False)
            assert brain.conversation_history == []
            assert brain.speak is False
        finally:
            del os.environ["OPENAI_API_KEY"]


class TestCloneBrainRespond:
    """Test response generation with mocked OpenAI."""

    def test_think_adds_to_history(self):
        """think() should add user message and response to history."""
        os.environ["OPENAI_API_KEY"] = "test-key-123"
        try:
            mod = _reload_brain_module()

            brain = mod.CloneBrain(speak=False)

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Test response from clone"
            brain.client.chat.completions.create = MagicMock(return_value=mock_response)

            result = brain.think("Hello, tell me about Slopify")

            assert result == "Test response from clone"
            assert len(brain.conversation_history) == 2
            assert brain.conversation_history[0]["role"] == "user"
            assert brain.conversation_history[1]["role"] == "assistant"
        finally:
            del os.environ["OPENAI_API_KEY"]

    def test_reset_clears_history(self):
        """reset_conversation() should clear history."""
        os.environ["OPENAI_API_KEY"] = "test-key-123"
        try:
            mod = _reload_brain_module()
            brain = mod.CloneBrain(speak=False)
            brain.conversation_history = [{"role": "user", "content": "test"}]
            brain.reset_conversation()
            assert brain.conversation_history == []
        finally:
            del os.environ["OPENAI_API_KEY"]

    def test_history_truncation(self):
        """Should truncate history when it exceeds max_history."""
        os.environ["OPENAI_API_KEY"] = "test-key-123"
        try:
            mod = _reload_brain_module()
            brain = mod.CloneBrain(speak=False)

            # Fill history beyond max
            for i in range(25):
                brain.conversation_history.append({"role": "user", "content": f"msg {i}"})

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "response"
            brain.client.chat.completions.create = MagicMock(return_value=mock_response)

            brain.think("new message")

            # History should be trimmed (max_history is 20, + 1 user + 1 assistant = 22 -> trimmed to 20 before call + 2 new)
            assert len(brain.conversation_history) <= mod.MAX_HISTORY + 2
        finally:
            del os.environ["OPENAI_API_KEY"]
