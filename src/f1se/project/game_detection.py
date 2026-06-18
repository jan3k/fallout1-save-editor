"""Game detection for Fallout SAVE.DAT files and slot directories."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from f1se.format.fallout2.save_dat import probe_fallout2
from f1se.format.save_dat import SaveDat
from f1se.project.game_profile import GameKind, get_profile


@dataclass(frozen=True, slots=True)
class GameDetectionResult:
    game_kind: GameKind
    confidence: int
    signature: str
    version: str | None
    reason: str
    read_only: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "game_kind": self.game_kind.value,
            "confidence": self.confidence,
            "signature": self.signature,
            "version": self.version,
            "reason": self.reason,
            "read_only": self.read_only,
            "profile": get_profile(self.game_kind).to_dict(),
        }


def resolve_save_dat_path(path: str | Path) -> Path:
    p = Path(path)
    if p.is_file():
        return p
    save = p / "SAVE.DAT"
    if save.is_file():
        return save
    raise FileNotFoundError(f"SAVE.DAT not found: {p}")


def _probe_fallout1(data: bytes, path: Path) -> dict[str, Any]:
    try:
        save = SaveDat.from_bytes(data, path)
    except Exception as exc:
        return {
            "game_kind": "unknown",
            "confidence": 0,
            "signature": "",
            "version": None,
            "reason": f"Fallout 1 parser rejected SAVE.DAT: {exc}",
            "read_only": True,
        }
    issues = save.verify()
    confidence = 85 if not issues else 65
    reason = "Fallout 1 parser accepted SAVE.DAT"
    if issues:
        reason += f" with verify warnings: {'; '.join(issues[:3])}"
    return {
        "game_kind": "fallout1",
        "confidence": confidence,
        "signature": save.header.signature,
        "version": save.header.version,
        "reason": reason,
        "read_only": False,
    }


def detect_game(path: str | Path) -> GameDetectionResult:
    save_path = resolve_save_dat_path(path)
    data = save_path.read_bytes()
    f1 = _probe_fallout1(data, save_path)
    f2 = probe_fallout2(data)

    f1_score = int(f1.get("confidence", 0))
    f2_score = int(f2.get("confidence", 0))
    if f1_score >= 60 and f1_score >= f2_score:
        return GameDetectionResult(
            game_kind=GameKind.FALLOUT1,
            confidence=f1_score,
            signature=str(f1.get("signature") or ""),
            version=f1.get("version"),
            reason=str(f1.get("reason") or "Fallout 1 profile selected"),
            read_only=False,
        )
    if f2_score >= 60:
        return GameDetectionResult(
            game_kind=GameKind.FALLOUT2,
            confidence=f2_score,
            signature=str(f2.get("signature") or ""),
            version=f2.get("version"),
            reason=str(f2.get("reason") or "Fallout 2 profile selected"),
            read_only=True,
        )
    reasons = [str(row.get("reason")) for row in (f1, f2) if row.get("reason")]
    return GameDetectionResult(
        game_kind=GameKind.UNKNOWN,
        confidence=max(f1_score, f2_score),
        signature=str(f2.get("signature") or f1.get("signature") or ""),
        version=f2.get("version") or f1.get("version"),
        reason="; ".join(reasons) or "no Fallout 1 or Fallout 2 profile matched",
        read_only=True,
    )
