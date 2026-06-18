"""v0.11 Fallout 2 read-only GUI integration.

This module layers Fallout 2 read-only tabs on top of the existing guided GUI
without enabling any Fallout 2 write path.
"""
from __future__ import annotations

from pathlib import Path

from f1se.gui.app import F1SaveEditorApp, _lazy_tk
from f1se.gui.app_v10 import _install as _install_v10
from f1se.gui.fo2_model import Fallout2GuiSession
from f1se.project.compatibility import compatibility_payload
from f1se.project.game_detection import detect_game
from f1se.project.game_profile import GameKind
from f1se.schema.enums import SKILL_NAMES, SPECIAL_NAMES, TRAIT_NAMES

_INSTALLED = False


def _iter_widgets(widget):
    for child in widget.winfo_children():
        yield child
        yield from _iter_widgets(child)


def _set_write_controls(app: F1SaveEditorApp, enabled: bool) -> None:
    state = "normal" if enabled else "disabled"
    for widget in _iter_widgets(app.root):
        try:
            text = widget.cget("text")
        except Exception:
            continue
        if text in {"Write changes", "Write raw", "Preview raw write"}:
            try:
                widget.configure(state=state)
            except Exception:
                pass


def _field_names(app: F1SaveEditorApp, prefix: str) -> list[str]:
    return sorted(
        [name for name in app.sd.fields if name.startswith(prefix)],
        key=lambda name: (app.sd.fields[name].abs_offset, name),
    )


def _build_readonly_field_rows(app: F1SaveEditorApp, parent, names: list[str], heading: str | None = None) -> None:
    if heading:
        app.ttk.Label(parent, text=heading).grid(row=0, column=0, columnspan=5, sticky="w", pady=(4, 8))
        start = 1
    else:
        start = 0
    app._header_row(parent, start)
    for row, name in enumerate(names, start=start + 1):
        if name in app.sd.fields:
            app._field_entry(parent, name, row, readonly=True)


def _install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    _install_v10()

    original_build_empty_tabs = F1SaveEditorApp._build_empty_tabs
    original_rebuild_all_tabs = F1SaveEditorApp._rebuild_all_tabs
    original_open_slot = F1SaveEditorApp.open_slot
    original_reload_slot = F1SaveEditorApp.reload_slot
    original_write_changes = F1SaveEditorApp.write_changes
    original_raw_preview = F1SaveEditorApp.raw_preview
    original_raw_write = F1SaveEditorApp.raw_write

    def _build_empty_tabs(self):
        original_build_empty_tabs(self)
        self.compatibility_tab = self.ttk.Frame(self.notebook)
        self.notebook.add(self.compatibility_tab, text="Compatibility")

    def _is_fallout2(self) -> bool:
        return self.session is not None and getattr(self.session, "game_kind", None) is GameKind.FALLOUT2

    def _rebuild_all_tabs(self):
        if _is_fallout2(self):
            self._rebuild_fallout2_tabs()
            self._update_dirty_indicator({})
            _set_write_controls(self, False)
            return
        original_rebuild_all_tabs(self)
        self._clear(self.compatibility_tab)
        self._build_compatibility_tab()
        _set_write_controls(self, True)

    def open_slot(self, slot_path: str | Path) -> None:
        try:
            detection = detect_game(slot_path)
            if detection.game_kind is GameKind.FALLOUT2:
                self.session = Fallout2GuiSession(slot_path)
                self.slot_var.set(str(self.session.slot_path))
                self._rebuild_all_tabs()
                self.status_var.set("Loaded Fallout 2 save in read-only mode. Write controls are disabled.")
                self.root.title("f1se - Fallout 2 Save Inspector")
                _set_write_controls(self, False)
                return
            original_open_slot(self, slot_path)
            if self.session is not None:
                self.root.title("f1se - Fallout 1 Save Editor")
                _set_write_controls(self, True)
        except Exception as exc:
            self.messagebox.showerror("Open failed", str(exc))
            self.status_var.set(f"Open failed: {exc}")

    def reload_slot(self) -> None:
        if _is_fallout2(self):
            try:
                self.session.reload()
                self._rebuild_all_tabs()
                self.status_var.set("Reloaded Fallout 2 save in read-only mode.")
                _set_write_controls(self, False)
            except Exception as exc:
                self.messagebox.showerror("Reload failed", str(exc))
            return
        original_reload_slot(self)

    def _clear_all_known_tabs(self) -> None:
        tabs = [
            self.overview_tab,
            self.player_tab,
            self.special_tab,
            self.skills_tab,
            self.traits_tab,
            self.inventory_tab,
            self.perks_tab,
            self.kills_tab,
            self.options_tab,
            self.fields_tab,
            self.raw_tab,
            self.validation_tab,
            self.artifacts_tab,
            self.raw_blocks_tab,
            self.global_scan_tab,
            self.map_scan_tab,
            self.compatibility_tab,
        ]
        self.field_vars.clear()
        for tab in tabs:
            self._clear(tab)

    def _rebuild_fallout2_tabs(self) -> None:
        _clear_all_known_tabs(self)
        self._build_fallout2_overview_tab()
        self._build_fallout2_player_tab()
        self._build_fallout2_special_tab()
        self._build_fallout2_skills_tab()
        self._build_fallout2_traits_tab()
        self._build_fallout2_inventory_tab()
        self._build_fallout2_perks_tab()
        self._build_fallout2_kills_tab()
        self._build_fallout2_options_tab()
        self._build_fallout2_fields_tab()
        self._build_fallout2_raw_tab()
        self._build_fallout2_validation_tab()
        self._build_artifacts_tab()
        self._build_raw_blocks_diag_tab()
        self._build_global_scan_diag_tab()
        self._build_map_scan_diag_tab()
        self._build_compatibility_tab()

    def _build_fallout2_overview_tab(self) -> None:
        assert self.session is not None
        ttk = self.ttk
        summary = self.session.summary()
        left = ttk.Frame(self.overview_tab, padding=8)
        left.pack(side="left", fill="both", expand=False)
        rows = [
            "game_kind",
            "read_only",
            "slot_path",
            "size",
            "size_hex",
            "sha256",
            "signature",
            "version",
            "player_name",
            "save_name",
            "saved_date",
            "current_map_file",
            "map_id",
            "elevation",
            "function5_start",
            "function6_start",
            "parser_status",
        ]
        for row, key in enumerate(rows):
            value = summary.get(key, "")
            if key.endswith("_start") and isinstance(value, int):
                value = f"0x{value:X}"
            ttk.Label(left, text=key, width=18).grid(row=row, column=0, sticky="w", pady=1)
            ttk.Label(left, text=str(value), width=80).grid(row=row, column=1, sticky="w", pady=1)

        right = ttk.Frame(self.overview_tab, padding=8)
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="Fallout 2 read-only sections").pack(anchor="w")
        tree = ttk.Treeview(right, columns=("name", "start", "end", "size", "confidence"), show="headings", height=18)
        for col, width in [("name", 240), ("start", 90), ("end", 90), ("size", 90), ("confidence", 100)]:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="both", expand=True)
        for section in self.sd.sections.values():
            tree.insert("", "end", values=(section.name, f"0x{section.start:X}", f"0x{section.end:X}", f"0x{section.end - section.start:X}", section.confidence))

    def _build_fallout2_player_tab(self) -> None:
        frame = self.ttk.Frame(self.player_tab, padding=8)
        frame.pack(fill="both", expand=True)
        names = [
            name
            for name in [
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
            if name in self.sd.fields
        ]
        self.ttk.Label(frame, text="Fallout 2 player fields are read-only. Write support is intentionally disabled.").grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 8))
        _build_readonly_field_rows(self, frame, names)

    def _build_fallout2_special_tab(self) -> None:
        inner = self._scrollable(self.special_tab)
        row = 0
        self.ttk.Label(inner, text="Base S.P.E.C.I.A.L.").grid(row=row, column=0, sticky="w", pady=(4, 8))
        row += 1
        self._header_row(inner, row)
        row += 1
        for stat in SPECIAL_NAMES:
            name = f"player.base_{stat}"
            if name in self.sd.fields:
                self._field_entry(inner, name, row, label=f"base {stat}", readonly=True, width=8)
                row += 1
        row += 1
        self.ttk.Label(inner, text="Bonus S.P.E.C.I.A.L.").grid(row=row, column=0, sticky="w", pady=(12, 8))
        row += 1
        for stat in SPECIAL_NAMES:
            name = f"player.bonus_{stat}"
            if name in self.sd.fields:
                self._field_entry(inner, name, row, label=f"bonus {stat}", readonly=True, width=8)
                row += 1
        row += 1
        self.ttk.Label(inner, text="Derived / advanced stats").grid(row=row, column=0, sticky="w", pady=(12, 8))
        row += 1
        for name in ["base_hitpoints", "bonus_hitpoints", "base_action_points", "base_armor_class", "base_melee_damage", "starting_age", "gender"]:
            field = f"player.{name}"
            if field in self.sd.fields:
                self._field_entry(inner, field, row, label=name, readonly=True, width=8)
                row += 1

    def _build_fallout2_skills_tab(self) -> None:
        inner = self._scrollable(self.skills_tab)
        row = 0
        self.ttk.Label(inner, text="Fallout 2 skills and tag skills are read-only.").grid(row=row, column=0, columnspan=5, sticky="w", pady=(4, 8))
        row += 1
        self._header_row(inner, row)
        row += 1
        for skill in SKILL_NAMES:
            name = f"skills.{skill}"
            if name in self.sd.fields:
                self._field_entry(inner, name, row, label=skill, readonly=True, width=8)
                row += 1
        row += 1
        self.ttk.Label(inner, text="Tagged skills").grid(row=row, column=0, sticky="w", pady=(12, 2))
        row += 1
        for idx in range(4):
            name = f"tag_skills.{idx}"
            if name in self.sd.fields:
                self._field_entry(inner, name, row, label=f"tag skill {idx}", readonly=True, width=8)
                row += 1

    def _build_fallout2_traits_tab(self) -> None:
        frame = self.ttk.Frame(self.traits_tab, padding=8)
        frame.pack(fill="both", expand=True)
        self.ttk.Label(frame, text="Fallout 2 traits are shown as raw read-only trait ids.").grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 8))
        self._header_row(frame, 1)
        values = {-1: "none", **{idx: name for idx, name in enumerate(TRAIT_NAMES)}}
        row = 2
        for idx in range(2):
            name = f"traits.{idx}"
            if name in self.sd.fields:
                field = self.sd.fields[name]
                label = f"trait {idx}: {values.get(int(field.value), 'unknown')}"
                self._field_entry(frame, name, row, label=label, readonly=True, width=12)
                row += 1

    def _build_fallout2_inventory_tab(self) -> None:
        ttk = self.ttk
        top = ttk.Frame(self.inventory_tab, padding=8)
        top.pack(fill="both", expand=True)
        ttk.Label(top, text="Fallout 2 inventory is read-only. Add/remove/create-object operations are blocked.").pack(anchor="w", pady=(0, 8))
        tree = ttk.Treeview(top, columns=("idx", "offset", "qty", "pid", "size", "confidence", "warnings"), show="headings", height=12)
        for col, width in [("idx", 45), ("offset", 90), ("qty", 70), ("pid", 90), ("size", 75), ("confidence", 95), ("warnings", 420)]:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="both", expand=True)
        for item in self.sd.inventory:
            tree.insert("", "end", values=(item.index, f"0x{item.start:X}", item.quantity, item.pid, f"0x{item.end - item.start:X}", item.confidence, "; ".join(item.warnings)))
        if not self.sd.inventory:
            ttk.Label(top, text="No inventory entries detected in this save.").pack(anchor="w", pady=(8, 0))

    def _build_fallout2_perks_tab(self) -> None:
        inner = self._scrollable(self.perks_tab)
        names = _field_names(self, "perks.")
        _build_readonly_field_rows(self, inner, names, "Fallout 2 perk ranks are raw read-only ranks; semantic side effects are not modeled.")

    def _build_fallout2_kills_tab(self) -> None:
        inner = self._scrollable(self.kills_tab)
        names = _field_names(self, "kill_counts.")
        _build_readonly_field_rows(self, inner, names, "Fallout 2 kill counters are read-only and exposed as stable indices where labels are uncertain.")

    def _build_fallout2_options_tab(self) -> None:
        self._add_placeholder(self.options_tab, "Fallout 2 options/preferences block is not exposed in the read-only skeleton yet.")

    def _build_fallout2_fields_tab(self) -> None:
        ttk = self.ttk
        frame = ttk.Frame(self.fields_tab, padding=8)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=("name", "value", "offset", "rel", "size", "risk", "confidence", "writable"), show="headings")
        for col, width in [("name", 330), ("value", 100), ("offset", 90), ("rel", 80), ("size", 55), ("risk", 105), ("confidence", 100), ("writable", 75)]:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="w")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        for field in sorted(self.sd.fields.values(), key=lambda f: (f.abs_offset, f.name)):
            tree.insert("", "end", values=(field.name, field.value, f"0x{field.abs_offset:X}", f"0x{field.rel_offset:X}", field.size, field.risk, getattr(field, "confidence", "n/a"), str(field.writable)))

    def _build_fallout2_raw_tab(self) -> None:
        ttk = self.ttk
        frame = ttk.Frame(self.raw_tab, padding=8)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Raw read is available for diagnostics. Raw write is disabled for Fallout 2.").grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 8))
        ttk.Label(frame, text="Offset").grid(row=1, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.raw_offset_var, width=16).grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(frame, text="Size").grid(row=1, column=2, sticky="w")
        ttk.Entry(frame, textvariable=self.raw_size_var, width=8).grid(row=1, column=3, sticky="w", padx=4)
        ttk.Button(frame, text="Read", command=self.raw_read).grid(row=1, column=4, padx=4)
        self.raw_text = self.tk.Text(frame, height=22, wrap="none")
        self.raw_text.grid(row=2, column=0, columnspan=5, sticky="nsew", pady=(8, 0))
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(3, weight=1)

    def _build_fallout2_validation_tab(self) -> None:
        frame = self.ttk.Frame(self.validation_tab, padding=8)
        frame.pack(fill="both", expand=True)
        self.validation_text = self.tk.Text(frame, height=20, wrap="word")
        self.validation_text.pack(fill="both", expand=True)
        self.diff_text = self.tk.Text(frame, height=8, wrap="none")
        self.diff_text.pack(fill="both", expand=True, pady=(8, 0))
        self.validation_text.insert("end", "Fallout 2 read-only parser status:\n")
        self.validation_text.insert("end", f"- {self.sd.parser_status}\n\n")
        if self.sd.warnings:
            self.validation_text.insert("end", "Warnings:\n")
            for warning in sorted(set(self.sd.warnings)):
                self.validation_text.insert("end", f"- {warning}\n")
        else:
            self.validation_text.insert("end", "No parser warnings.\n")
        self.validation_text.configure(state="disabled")
        self.diff_text.insert("end", "Write preview is disabled for Fallout 2.\n")
        self.diff_text.configure(state="disabled")

    def _build_compatibility_tab(self) -> None:
        ttk = self.ttk
        frame = ttk.Frame(self.compatibility_tab, padding=8)
        frame.pack(fill="both", expand=True)
        matrix = compatibility_payload()
        game = "fallout2" if _is_fallout2(self) else "fallout1"
        ttk.Label(frame, text=f"Compatibility matrix for {game}").pack(anchor="w", pady=(0, 8))
        tree = ttk.Treeview(frame, columns=("command", "status", "reason", "fixtures"), show="headings")
        for col, width in [("command", 130), ("status", 110), ("reason", 520), ("fixtures", 220)]:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="w")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        for command, row in matrix["games"][game].items():
            if command == "profile":
                continue
            tree.insert("", "end", values=(command, row["status"], row["reason"], ", ".join(row["required_fixtures"])))

    def write_changes(self) -> None:
        if _is_fallout2(self):
            self.messagebox.showerror("Write disabled", "Fallout 2 GUI support is read-only. No SAVE.DAT changes were written.")
            self.status_var.set("Fallout 2 write blocked.")
            return
        original_write_changes(self)

    def raw_preview(self) -> None:
        if _is_fallout2(self):
            self.messagebox.showerror("Raw write disabled", "Fallout 2 raw write preview is disabled.")
            self.status_var.set("Fallout 2 raw write preview blocked.")
            return
        original_raw_preview(self)

    def raw_write(self) -> None:
        if _is_fallout2(self):
            self.messagebox.showerror("Raw write disabled", "Fallout 2 raw writes are disabled.")
            self.status_var.set("Fallout 2 raw write blocked.")
            return
        original_raw_write(self)

    F1SaveEditorApp._build_empty_tabs = _build_empty_tabs
    F1SaveEditorApp._rebuild_all_tabs = _rebuild_all_tabs
    F1SaveEditorApp.open_slot = open_slot
    F1SaveEditorApp.reload_slot = reload_slot
    F1SaveEditorApp._rebuild_fallout2_tabs = _rebuild_fallout2_tabs
    F1SaveEditorApp._build_fallout2_overview_tab = _build_fallout2_overview_tab
    F1SaveEditorApp._build_fallout2_player_tab = _build_fallout2_player_tab
    F1SaveEditorApp._build_fallout2_special_tab = _build_fallout2_special_tab
    F1SaveEditorApp._build_fallout2_skills_tab = _build_fallout2_skills_tab
    F1SaveEditorApp._build_fallout2_traits_tab = _build_fallout2_traits_tab
    F1SaveEditorApp._build_fallout2_inventory_tab = _build_fallout2_inventory_tab
    F1SaveEditorApp._build_fallout2_perks_tab = _build_fallout2_perks_tab
    F1SaveEditorApp._build_fallout2_kills_tab = _build_fallout2_kills_tab
    F1SaveEditorApp._build_fallout2_options_tab = _build_fallout2_options_tab
    F1SaveEditorApp._build_fallout2_fields_tab = _build_fallout2_fields_tab
    F1SaveEditorApp._build_fallout2_raw_tab = _build_fallout2_raw_tab
    F1SaveEditorApp._build_fallout2_validation_tab = _build_fallout2_validation_tab
    F1SaveEditorApp._build_compatibility_tab = _build_compatibility_tab
    F1SaveEditorApp.write_changes = write_changes
    F1SaveEditorApp.raw_preview = raw_preview
    F1SaveEditorApp.raw_write = raw_write
    _INSTALLED = True


def run_gui(slot: str | Path | None = None) -> int:
    _install()
    tk, _ttk, _filedialog, messagebox = _lazy_tk()
    root = tk.Tk()
    try:
        F1SaveEditorApp(root, slot)
        root.mainloop()
    except Exception as exc:
        messagebox.showerror("f1se GUI error", str(exc))
        return 1
    return 0
