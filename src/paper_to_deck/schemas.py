from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class Figure(BaseModel):
    id: str
    kind: Literal["figure", "table"]
    caption: str
    image_path: str
    page: int


class ParsedPaper(BaseModel):
    title: str
    full_text: str
    pages: list[str]
    figures: list[Figure]


class Slide(BaseModel):
    title: str
    bullets: list[str]
    notes: str = ""
    image_id: str | None = None
    section: Literal["main", "appendix"] = "main"


class DeckOutline(BaseModel):
    title: str
    slides: list[Slide]

    def main_slides(self) -> list[Slide]:
        return [s for s in self.slides if s.section == "main"]

    def appendix_slides(self) -> list[Slide]:
        return [s for s in self.slides if s.section == "appendix"]
