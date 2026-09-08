"""Deterministic card composition through the installed Pyto runtime."""

from __future__ import annotations

import hashlib
import json
import inspect
from dataclasses import asdict
from importlib.metadata import version as package_version
from pathlib import Path
from typing import Any

from pyto import Calculation, PCR, Part, PxC


PART_REQUEST = "px.card.composition.request"
PART_RESULT = "px.card.composition.result"


def _copy(value: Any) -> Any:
    return json.loads(json.dumps(value, separators=(",", ":"), ensure_ascii=False))


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 120 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for c in value):
        raise ValueError(f"{label} must be a short identifier")
    return value


def _legacy(recipe: dict[str, Any]) -> dict[str, Any]:
    """Adapt pre-schema-3 recipes without fabricating an unresolved disc id."""
    if recipe.get("schemaVersion") == 3:
        return _copy(recipe)
    value = _copy(recipe)
    value["schemaVersion"] = 3
    presentation = value.get("presentationId") or value.get("discId")
    if not presentation:
        # A stable adapter identity is a presentation identity only; physical identity stays absent.
        raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        presentation = "legacy-" + hashlib.sha256(raw).hexdigest()[:16]
    value["presentationId"] = presentation
    value.setdefault("name", "")
    value.setdefault("note", "")
    value.setdefault("color", "#999999")
    value.setdefault("positions", {})
    value.setdefault("flightValues", {})
    value.setdefault("cards", {})
    # Schema 3 kept editor state at recipe level. Move it under the owning card.
    single = value["cards"].setdefault("single", {"type": "single", "layout": "standard", "details": True, "discRecipeIds": [presentation]})
    for key in ("positions", "group", "selected", "appearance", "hierarchy", "framing", "title"):
        if key in value and key not in single:
            single[key] = value[key]
    value["cards"].setdefault("battle", {"type": "battle", "layout": "standard", "details": True, "discRecipeIds": [presentation]})
    value.setdefault("presentations", {})
    value["presentations"].setdefault(presentation, _copy(value))
    value["presentations"][presentation].pop("presentations", None)
    value["presentations"][presentation].pop("cards", None)
    return value


def normalize_recipe(recipe: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(recipe, dict):
        raise ValueError("recipe object required")
    r = _legacy(recipe)
    presentation = _identifier(r.get("presentationId"), "presentationId")
    cards = r.get("cards")
    if not isinstance(cards, dict):
        raise ValueError("cards object required")
    presentations = r.get("presentations")
    if not isinstance(presentations, dict):
        raise ValueError("presentations object required")
    active = presentations.get(presentation)
    if not isinstance(active, dict):
        raise ValueError("active presentation is missing")
    for key in ("single", "battle"):
        card = cards.get(key)
        if not isinstance(card, dict) or card.get("type", key) != key:
            raise ValueError(f"invalid {key} card")
        allowed = (1 if key == "single" else 2)
        refs = card.get("discRecipeIds")
        if (not isinstance(refs, list) or not 1 <= len(refs) <= allowed or
                any(not isinstance(ref, str) for ref in refs) or refs[0] != presentation or
                len(set(refs)) != len(refs)):
            raise ValueError(f"invalid {key} card references")
        for ref in refs:
            _identifier(ref, "card presentation reference")
            if ref not in presentations:
                raise ValueError("card presentation reference is missing")
        layout = card.get("layout", "standard")
        valid_layouts = {"standard", "gallery"} if key == "single" else {"standard", "stacked"}
        if layout not in valid_layouts or not isinstance(card.get("details", True), bool):
            raise ValueError(f"invalid {key} card layout")
    if len(presentations) > 2:
        raise ValueError("at most two presentations are supported")
    for embedded_id, embedded in presentations.items():
        _identifier(embedded_id, "embedded presentation identity")
        if not isinstance(embedded, dict) or embedded.get("presentationId") != embedded_id:
            raise ValueError("embedded presentation identity mismatch")
    # Card-owned state is copied explicitly; arbitrary transport fields are ignored.
    for key in ("single", "battle"):
        card = cards[key]
        card["discRecipeIds"] = list(card["discRecipeIds"])
        for field in ("positions", "group", "selected", "appearance", "hierarchy", "framing", "title",
                      "participants", "scores", "highlight", "winner", "manualWinner"):
            if field in card and field not in ("positions", "appearance") and not isinstance(card[field], (str, bool, int, float, list, dict, type(None))):
                raise ValueError(f"invalid {key} card {field}")
    return r


def _presentation(value: dict[str, Any], card: dict[str, Any]) -> dict[str, Any]:
    fields = {"presentationId": value.get("presentationId"), "physicalDiscId": value.get("physicalDiscId"),
              "manufacturer": value.get("manufacturer", ""), "mold": value.get("mold", ""),
              "variant": value.get("variant", ""), "name": value.get("name", ""), "note": value.get("note", ""),
              "color": value.get("color"), "surface": value.get("surface", ""), "spin": value.get("spin", False),
              "flightValues": value.get("flightValues", {}), "art": value.get("art")}
    return {k: _copy(v) for k, v in fields.items() if v is not None}


def compose(recipe: dict[str, Any]) -> dict[str, Any]:
    r = normalize_recipe(recipe)
    cards = {}
    for key in ("single", "battle"):
        card = r["cards"][key]
        refs = card["discRecipeIds"]
        participants = [_presentation(r["presentations"][ref], card) for ref in refs]
        cards[key] = _card_output(key, card, participants)
    return {"schemaVersion": 1, "theme": "warm-paper", "cards": cards}


def _compose_parts(args: dict[str, Any]) -> dict[str, Any]:
    cards = {}
    for key in ("single", "battle"):
        config = args[key]
        participants = [_copy(args[ref]) for ref in config["discRecipeIds"]]
        cards[key] = _card_output(key, config, participants)
    return {"schemaVersion": 1, "theme": "warm-paper", "cards": cards}


def _card_output(key: str, config: dict[str, Any], participants: list[dict[str, Any]]) -> dict[str, Any]:
    output = {"type": key, "layout": config.get("layout", "standard"),
              "details": config.get("details", True), "participants": participants}
    for field in ("positions", "group", "selected", "appearance", "hierarchy", "framing", "title",
                  "scores", "highlight", "winner", "manualWinner"):
        if field in config:
            output[field] = _copy(config[field])
    return output


def execute_card(recipe: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized = normalize_recipe(recipe)
    presentation_parts = {ref: Part(f"px.disc.presentation.{ref}") for ref in normalized["presentations"]}
    card_parts = {key: Part(f"px.card.{key}.config") for key in ("single", "battle")}
    result = Part(PART_RESULT)
    pxc = PxC()
    for ref, part in presentation_parts.items():
        pxc.set(part, _presentation(normalized["presentations"][ref], normalized["cards"]["single"]))
    part_names = {ref: f"p{index}" for index, ref in enumerate(presentation_parts)}
    for key, part in card_parts.items():
        card_value = _copy(normalized["cards"][key])
        card_value["discRecipeIds"] = [part_names[ref] for ref in card_value["discRecipeIds"]]
        pxc.set(part, card_value)
    calculation = Calculation("fn.card.compose", _compose_parts)
    pcr = PCR("card-composition")
    inputs = {"single": card_parts["single"], "battle": card_parts["battle"]}
    for index, (ref, part) in enumerate(presentation_parts.items()):
        inputs[f"p{index}"] = part
    pcr.calc("compose", calculation, id="compose-card", into=result, **inputs)
    run = pcr.run(pxc)
    output = pxc.get(result)
    module_path = Path(inspect.getsourcefile(Calculation) or "")
    source_hash = hashlib.sha256(module_path.read_bytes()).hexdigest() if module_path.exists() else None
    evidence = {"pyto": {"package": "pyto-lab", "version": package_version("pyto-lab"), "moduleSourceSha256": source_hash},
                "composition": {"pcr": run.pcr, "ticks": [asdict(tick) for tick in run.ticks]}}
    return output, evidence
