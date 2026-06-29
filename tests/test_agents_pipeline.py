import json
import os

import pytest
from paper_to_deck.agents import tools, pipeline
from paper_to_deck.schemas import DeckOutline, Slide


def test_render_deck_tool_writes_html(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPER_TO_DECK_SANDBOX", str(tmp_path))
    outline = DeckOutline(title="T", slides=[Slide(title="Intro", bullets=["a"])])
    path = tools.render_deck_tool(outline.model_dump_json())
    assert path.endswith("deck.html")
    assert (tmp_path / "deck.html").exists()
    assert "Intro" in (tmp_path / "deck.html").read_text()


def test_render_deck_tool_rejects_bad_json(tmp_path, monkeypatch):
    monkeypatch.setenv("PAPER_TO_DECK_SANDBOX", str(tmp_path))
    result = tools.render_deck_tool("{not json")
    assert result.lower().startswith("error")


def test_pipeline_has_four_agents_in_order():
    root = pipeline.build_root_agent()
    names = [a.name for a in root.sub_agents]
    assert names == ["concierge", "distiller", "visual_matcher", "frontend_coder"]


def test_pipeline_state_keys_are_chained():
    root = pipeline.build_root_agent()
    by_name = {a.name: a for a in root.sub_agents}
    assert by_name["concierge"].output_key == "constraints"
    assert by_name["distiller"].output_key == "deck_outline"
    assert by_name["visual_matcher"].output_key == "mapped_outline"
