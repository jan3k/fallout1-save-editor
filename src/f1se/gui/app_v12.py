"""v0.12 Fallout 2 GUI editing layer.

Adds GUI editing for the same allowlisted Fallout 2 semantic fields exposed by
CLI helpers. Object graph operations such as inventory item creation remain
blocked until a safe object-template model exists.
"""
from __future__ import annotations

from pathlib import Path

from f1se.gui.app import F1SaveEditorApp, _parse_int_text, format_diff
from f1se.gui.app_v11 import _install as _install_v11
from f1se.project.fallout2_write import set_field as fallout2_set_field
from f1se.project.fallout2_write import writable_fields_payload
from f1se.project.game_profile import GameKind
from f1se.schema.enums import KILL_COUNT_NAMES, PERK_NAMES, SKILL_NAMES, SPECIAL_NAMES, TRAIT_NAMES

_INSTALLED = False


def _is_fallout2(app: F1SaveEditorApp) -> bool:
    return app.session is not None and getattr(app.session, "game_kind", None) is GameKind.FALLOUT2


def _fo2_writable_map(app: F1SaveEditorApp) -> dict:
    if app.session is None:
        return {}
    return writable_fields_payload(app.session.slot_path, allow_advanced=True)["fields"]


def _fo2_is_editable(app: F1SaveEditorApp, field_name: str) -> bool:
    row = _fo2_writable_map(app).get(field_name)
    return bool(row and row.get("writable"))


def _fo2_field_entry(app: F1SaveEditorApp, parent, field_name: str, row: int, *, label: str | None = None, width: int = 12, readonly: bool | None = None, combo_values: list[str] | None = None) -> None:
    ttk = app.ttk
    field = app.sd.fields[field_name]
    writable_row = _fo2_writable_map(app).get(field_name, {})
    editable = bool(writable_row.get("writable")) if readonly is None else not readonly
    ttk.Label(parent, text=label or field_name, width=32).grid(row=row, column=0, sticky="w", padx=4, pady=2)
    var = app.tk.StringVar(value=str(field.value))
    app.field_vars[field_name] = var
    if combo_values is not None:
        widget = ttk.Combobox(parent, textvariable=var, values=combo_values, width=width, state="readonly" if editable else "disabled")
        current = next((v for v in combo_values if v.startswith(f"{field.value}:")), str(field.value))
        var.set(current)
    else:
        widget = ttk.Entry(parent, textvariable=var, width=width)
        if not editable:
            widget.configure(state="readonly")
    widget.grid(row=row, column=1, sticky="w", padx=4, pady=2)
    ttk.Label(parent, text=f"0x{field.abs_offset:X}", width=12).grid(row=row, column=2, sticky="w", padx=4)
    ttk.Label(parent, text=f"{field.risk}/{getattr(field, 'confidence', '')}", width=16).grid(row=row, column=3, sticky="w", padx=4)
    reason = writable_row.get("write_reason") or field.description
    if reason:
        ttk.Label(parent, text=str(reason)).grid(row=row, column=4, sticky="w", padx=4)


def _fo2_collect_patch(app: F1SaveEditorApp) -> dict[str, int]:
    patch: dict[str, int] = {}
    writable = _fo2_writable_map(app)
    for name, var in app.field_vars.items():
        if name not in app.sd.fields or not writable.get(name, {}).get("writable"):
            continue
        field = app.sd.fields[name]
        if getattr(field, "type_name", "") != "i32":
            continue
        new_value = _parse_int_text(var.get())
        old_value = int(field.value)
        if new_value != old_value:
            patch[name] = new_value
    return patch


def _fo2_write_diff_line(payload: dict) -> str:
    diff = payload["diff"]
    return f"SAVE.DAT:{diff['offset_hex']} {diff['old_bytes']} -> {diff['new_bytes']} {diff['field']} ({diff['old_value']} -> {diff['new_value']})"


def _install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _install_v11()

    original_rebuild_fallout2_tabs = F1SaveEditorApp._rebuild_fallout2_tabs
    original_preview_diff = F1SaveEditorApp.preview_diff
    original_write_changes = F1SaveEditorApp.write_changes

    def _build_fallout2_editor_notice(self, parent, text: str) -> None:
        self.ttk.Label(parent, text=text, foreground="#704000").grid(row=0, column=0, columnspan=5, sticky="w", pady=(4, 8))

    def _build_fallout2_player_tab(self) -> None:
        frame = self.ttk.Frame(self.player_tab, padding=8)
        frame.pack(fill="both", expand=True)
        _build_fallout2_editor_notice(self, frame, "Editable Fallout 2 allowlisted player fields. Use Preview diff before Write changes.")
        self._header_row(frame, 1)
        names = [
            "player.current_hp",
            "player.radiation",
            "player.poison",
            "player.crippled_body_parts",
            "pc.skill_points",
            "pc.level",
            "pc.experience",
            "pc.reputation_or_unknown",
            "pc.karma_or_unknown",
        ]
        row = 2
        for name in names:
            if name in self.sd.fields:
                _fo2_field_entry(self, frame, name, row)
                row += 1

    def _build_fallout2_special_tab(self) -> None:
        inner = self._scrollable(self.special_tab)
        row = 0
        self.ttk.Label(inner, text="Base S.P.E.C.I.A.L. — editable").grid(row=row, column=0, sticky="w", pady=(4, 8))
        row += 1
        self._header_row(inner, row)
        row += 1
        for stat in SPECIAL_NAMES:
            name = f"player.base_{stat}"
            if name in self.sd.fields:
                _fo2_field_entry(self, inner, name, row, label=f"base {stat}", width=8)
                row += 1
        row += 1
        self.ttk.Label(inner, text="Bonus / derived / advanced stats — editable where allowlisted").grid(row=row, column=0, sticky="w", pady=(12, 8))
        row += 1
        for stat in SPECIAL_NAMES:
            name = f"player.bonus_{stat}"
            if name in self.sd.fields:
                _fo2_field_entry(self, inner, name, row, label=f"bonus {stat}", width=8)
                row += 1
        for name in ["base_hitpoints", "bonus_hitpoints", "base_action_points", "base_armor_class", "base_melee_damage", "starting_age", "gender"]:
            field = f"player.{name}"
            if field in self.sd.fields:
                _fo2_field_entry(self, inner, field, row, label=name, width=8)
                row += 1

    def _build_fallout2_skills_tab(self) -> None:
        inner = self._scrollable(self.skills_tab)
        row = 0
        self.ttk.Label(inner, text="Fallout 2 skills are editable. Retoryka = speech / skills.speech.").grid(row=row, column=0, columnspan=5, sticky="w", pady=(4, 8))
        row += 1
        self._header_row(inner, row)
        row += 1
        for skill in SKILL_NAMES:
            name = f"skills.{skill}"
            if name in self.sd.fields:
                label = "retoryka / speech" if skill == "speech" else skill
                _fo2_field_entry(self, inner, name, row, label=label, width=8)
                row += 1
        row += 1
        self.ttk.Label(inner, text="Tagged skills").grid(row=row, column=0, sticky="w", pady=(12, 2))
        row += 1
        skill_values = ["-1: none"] + [f"{i}: {name}" for i, name in enumerate(SKILL_NAMES)]
        for idx in range(4):
            name = f"tag_skills.{idx}"
            if name in self.sd.fields:
                _fo2_field_entry(self, inner, name, row, label=f"tag skill {idx}", combo_values=skill_values, width=24)
                row += 1

    def _build_fallout2_traits_tab(self) -> None:
        frame = self.ttk.Frame(self.traits_tab, padding=8)
        frame.pack(fill="both", expand=True)
        self.ttk.Label(frame, text="Fallout 2 traits are editable as trait ids.").grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 8))
        self._header_row(frame, 1)
        values = ["-1: none"] + [f"{idx}: {name}" for idx, name in enumerate(TRAIT_NAMES)]
        row = 2
        for idx in range(2):
            name = f"traits.{idx}"
            if name in self.sd.fields:
                _fo2_field_entry(self, frame, name, row, label=f"trait {idx}", combo_values=values, width=30)
                row += 1

    def _build_fallout2_inventory_tab(self) -> None:
        ttk = self.ttk
        top = ttk.Frame(self.inventory_tab, padding=8)
        top.pack(fill="both", expand=True)
        ttk.Label(top, text="Fallout 2 inventory object creation/add/remove remains blocked. Existing allowlisted quantity fields can be edited if detected.").pack(anchor="w", pady=(0, 8))
        tree = ttk.Treeview(top, columns=("idx", "offset", "qty", "pid", "size", "confidence", "warnings"), show="headings", height=10)
        for col, width in [("idx", 45), ("offset", 90), ("qty", 70), ("pid", 90), ("size", 75), ("confidence", 95), ("warnings", 420)]:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="x")
        for item in self.sd.inventory:
            tree.insert("", "end", values=(item.index, f"0x{item.start:X}", item.quantity, item.pid, f"0x{item.end - item.start:X}", item.confidence, "; ".join(item.warnings)))
        edit = self._scrollable(self.inventory_tab)
        self._header_row(edit, 0)
        row = 1
        for item in self.sd.inventory:
            name = f"inventory.{item.index}.quantity"
            if name in self.sd.fields:
                _fo2_field_entry(self, edit, name, row, label=f"{item.index}.quantity", width=10)
                row += 1
        if row == 1:
            ttk.Label(edit, text="No editable inventory quantity fields detected. Item add/create is intentionally not implemented.").grid(row=row, column=0, sticky="w", pady=(8, 0))

    def _build_fallout2_perks_tab(self) -> None:
        inner = self._scrollable(self.perks_tab)
        self.ttk.Label(inner, text="Fallout 2 perk ranks are editable as raw ranks. Engine-side side effects are not emulated.").grid(row=0, column=0, columnspan=5, sticky="w", pady=(4, 8))
        self._header_row(inner, 1)
        row = 2
        for perk in PERK_NAMES:
            name = f"perks.{perk}"
            if name in self.sd.fields:
                _fo2_field_entry(self, inner, name, row, label=perk, width=8)
                row += 1

    def _build_fallout2_kills_tab(self) -> None:
        inner = self._scrollable(self.kills_tab)
        self.ttk.Label(inner, text="Fallout 2 kill counters are editable as source-order counters.").grid(row=0, column=0, columnspan=5, sticky="w", pady=(4, 8))
        self._header_row(inner, 1)
        row = 2
        names = [n for n in self.sd.fields if n.startswith("kill_counts.")]
        for name in sorted(names, key=lambda n: self.sd.fields[n].abs_offset):
            label = name.split(".", 1)[1]
            _fo2_field_entry(self, inner, name, row, label=label, width=10)
            row += 1

    def preview_diff(self) -> None:
        if not _is_fallout2(self):
            original_preview_diff(self)
            return
        try:
            patch = _fo2_collect_patch(self)
            if self.diff_text is None:
                self.notebook.select(self.validation_tab)
            if self.diff_text is None:
                return
            self.diff_text.configure(state="normal")
            self.diff_text.delete("1.0", "end")
            if not patch:
                self.diff_text.insert("end", "No byte changes.\n")
                self.status_var.set("No Fallout 2 GUI changes staged.")
                return
            for name, value in patch.items():
                payload = fallout2_set_field(self.session.slot_path, name, value, write=False, allow_advanced=True)
                self.diff_text.insert("end", _fo2_write_diff_line(payload) + "\n")
            self.status_var.set(f"Previewed {len(patch)} Fallout 2 field change(s).")
        except Exception as exc:
            self.messagebox.showerror("Preview failed", str(exc))
            self.status_var.set(f"Fallout 2 preview failed: {exc}")

    def write_changes(self) -> None:
        if not _is_fallout2(self):
            original_write_changes(self)
            return
        try:
            patch = _fo2_collect_patch(self)
            if not patch:
                self.status_var.set("No Fallout 2 GUI changes to write.")
                return
            if not self.messagebox.askyesno("Write Fallout 2 changes", f"Write {len(patch)} Fallout 2 field change(s)? Backups will be created before writes."):
                return
            backups: list[str] = []
            for name, value in patch.items():
                payload = fallout2_set_field(self.session.slot_path, name, value, write=True, allow_advanced=True)
                if payload.get("backup_path"):
                    backups.append(payload["backup_path"])
            self.session.reload()
            self._rebuild_all_tabs()
            self.status_var.set(f"Wrote {len(patch)} Fallout 2 field change(s). Backups: {len(backups)}")
        except Exception as exc:
            self.messagebox.showerror("Write failed", str(exc))
            self.status_var.set(f"Fallout 2 write failed: {exc}")

    F1SaveEditorApp._build_fallout2_player_tab = _build_fallout2_player_tab
    F1SaveEditorApp._build_fallout2_special_tab = _build_fallout2_special_tab
    F1SaveEditorApp._build_fallout2_skills_tab = _build_fallout2_skills_tab
    F1SaveEditorApp._build_fallout2_traits_tab = _build_fallout2_traits_tab
    F1SaveEditorApp._build_fallout2_inventory_tab = _build_fallout2_inventory_tab
    F1SaveEditorApp._build_fallout2_perks_tab = _build_fallout2_perks_tab
    F1SaveEditorApp._build_fallout2_kills_tab = _build_fallout2_kills_tab
    F1SaveEditorApp.preview_diff = preview_diff
    F1SaveEditorApp.write_changes = write_changes
    _INSTALLED = True


def run_gui(slot: str | Path | None = None) -> int:
    _install()
    from f1se.gui.app_v11 import run_gui as run_v11_gui
    return run_v11_gui(slot)
