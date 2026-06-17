"""Tkinter GUI for Fallout 1 save slots.

The GUI is intentionally stdlib-only. All binary parsing and writing stays in
f1se.format.* and f1se.gui.model, so the interface cannot accidentally invent a
second save format implementation.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from f1se.gui.model import SaveEditorSession, format_diff
from f1se.schema.enums import KILL_COUNT_NAMES, PERK_NAMES, SKILL_NAMES, SPECIAL_NAMES, TRAIT_EFFECTS, TRAIT_NAMES
from f1se.schema.fields import Field


def _lazy_tk():
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    return tk, ttk, filedialog, messagebox


def _display_name(identifier: str) -> str:
    return identifier.replace("_", " ").title()


def _parse_int_text(text: str) -> int:
    value = text.strip()
    if ":" in value:
        value = value.split(":", 1)[0].strip()
    if value.lower() in {"none", "-", ""}:
        return -1
    return int(value, 0)


class F1SaveEditorApp:
    def __init__(self, root, initial_slot: str | Path | None = None):
        self.tk, self.ttk, self.filedialog, self.messagebox = _lazy_tk()
        self.root = root
        self.root.title("f1se - Fallout 1 Save Editor")
        self.root.geometry("1180x760")
        self.session: SaveEditorSession | None = None
        self.field_vars: dict[str, object] = {}
        self.widgets_to_rebuild: list[object] = []
        self.diff_text = None
        self.status_var = self.tk.StringVar(value="Open a Fallout 1 save slot directory containing SAVE.DAT.")
        self.slot_var = self.tk.StringVar(value=str(initial_slot or ""))
        self.allow_out_of_range_var = self.tk.BooleanVar(value=False)
        self.semantic_mode_var = self.tk.BooleanVar(value=False)
        self.raw_offset_var = self.tk.StringVar(value="0x8B40")
        self.raw_size_var = self.tk.StringVar(value="4")
        self.raw_hex_var = self.tk.StringVar(value="0000000A")
        self.raw_write_ack_var = self.tk.BooleanVar(value=False)
        self._build_shell()
        if initial_slot:
            self.open_slot(initial_slot)

    def _build_shell(self) -> None:
        ttk = self.ttk
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill="x")
        ttk.Label(top, text="Slot:").pack(side="left")
        ttk.Entry(top, textvariable=self.slot_var).pack(side="left", fill="x", expand=True, padx=(6, 6))
        ttk.Button(top, text="Open...", command=self.choose_slot).pack(side="left", padx=2)
        ttk.Button(top, text="Load", command=lambda: self.open_slot(self.slot_var.get())).pack(side="left", padx=2)
        ttk.Button(top, text="Reload", command=self.reload_slot).pack(side="left", padx=2)
        ttk.Button(top, text="Verify", command=self.verify).pack(side="left", padx=2)
        ttk.Button(top, text="Preview diff", command=self.preview_diff).pack(side="left", padx=8)
        ttk.Button(top, text="Write changes", command=self.write_changes).pack(side="left", padx=2)

        opts = ttk.Frame(self.root, padding=(8, 0, 8, 6))
        opts.pack(fill="x")
        ttk.Checkbutton(opts, text="Allow out-of-range values", variable=self.allow_out_of_range_var).pack(side="left")
        ttk.Checkbutton(opts, text="Semantic SPECIAL recalculation", variable=self.semantic_mode_var).pack(side="left", padx=16)
        ttk.Label(opts, textvariable=self.status_var).pack(side="right")

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._build_empty_tabs()

    def _build_empty_tabs(self) -> None:
        for child in self.notebook.tabs():
            self.notebook.forget(child)
        self.overview_tab = self.ttk.Frame(self.notebook)
        self.player_tab = self.ttk.Frame(self.notebook)
        self.special_tab = self.ttk.Frame(self.notebook)
        self.skills_tab = self.ttk.Frame(self.notebook)
        self.traits_tab = self.ttk.Frame(self.notebook)
        self.inventory_tab = self.ttk.Frame(self.notebook)
        self.perks_tab = self.ttk.Frame(self.notebook)
        self.kills_tab = self.ttk.Frame(self.notebook)
        self.options_tab = self.ttk.Frame(self.notebook)
        self.fields_tab = self.ttk.Frame(self.notebook)
        self.raw_tab = self.ttk.Frame(self.notebook)
        self.validation_tab = self.ttk.Frame(self.notebook)
        for tab, title in [
            (self.overview_tab, "Overview"),
            (self.player_tab, "Player"),
            (self.special_tab, "S.P.E.C.I.A.L."),
            (self.skills_tab, "Skills"),
            (self.traits_tab, "Traits"),
            (self.inventory_tab, "Inventory"),
            (self.perks_tab, "Perks"),
            (self.kills_tab, "Kills"),
            (self.options_tab, "Options"),
            (self.fields_tab, "Fields"),
            (self.raw_tab, "Raw"),
            (self.validation_tab, "Validation"),
        ]:
            self.notebook.add(tab, text=title)
        self._add_placeholder(self.overview_tab, "No slot loaded.")

    def _clear(self, frame) -> None:
        for child in frame.winfo_children():
            child.destroy()

    def _add_placeholder(self, frame, text: str) -> None:
        self._clear(frame)
        self.ttk.Label(frame, text=text, padding=20).pack(anchor="nw")

    def choose_slot(self) -> None:
        directory = self.filedialog.askdirectory(title="Select Fallout 1 save slot directory")
        if directory:
            self.slot_var.set(directory)
            self.open_slot(directory)

    def open_slot(self, slot_path: str | Path) -> None:
        try:
            self.session = SaveEditorSession(slot_path)
            self.slot_var.set(str(self.session.slot_path))
            self._rebuild_all_tabs()
            self.status_var.set("Loaded slot.")
        except Exception as exc:
            self.messagebox.showerror("Open failed", str(exc))
            self.status_var.set(f"Open failed: {exc}")

    def reload_slot(self) -> None:
        if self.session is None:
            return
        try:
            self.session.reload()
            self._rebuild_all_tabs()
            self.status_var.set("Reloaded from disk.")
        except Exception as exc:
            self.messagebox.showerror("Reload failed", str(exc))

    def _rebuild_all_tabs(self) -> None:
        self.field_vars.clear()
        for tab in [self.overview_tab, self.player_tab, self.special_tab, self.skills_tab, self.traits_tab, self.inventory_tab, self.perks_tab, self.kills_tab, self.options_tab, self.fields_tab, self.raw_tab, self.validation_tab]:
            self._clear(tab)
        self._build_overview_tab()
        self._build_player_tab()
        self._build_special_tab()
        self._build_skills_tab()
        self._build_traits_tab()
        self._build_inventory_tab()
        self._build_perks_tab()
        self._build_kills_tab()
        self._build_options_tab()
        self._build_fields_tab()
        self._build_raw_tab()
        self._build_validation_tab()

    @property
    def sd(self):
        if self.session is None:
            raise RuntimeError("no slot loaded")
        return self.session.save_dat

    def _build_overview_tab(self) -> None:
        assert self.session is not None
        ttk = self.ttk
        summary = self.session.summary()
        left = ttk.Frame(self.overview_tab, padding=8)
        left.pack(side="left", fill="both", expand=False)
        for row, key in enumerate(["slot_path", "size", "size_hex", "sha256", "signature", "version", "player_name", "save_name", "saved_date", "current_map_file", "map_id", "elevation", "function5_start", "function6_start"]):
            value = summary[key]
            if key.endswith("_start"):
                value = f"0x{value:X}"
            ttk.Label(left, text=key, width=18).grid(row=row, column=0, sticky="w", pady=1)
            ttk.Label(left, text=str(value), width=80).grid(row=row, column=1, sticky="w", pady=1)

        right = ttk.Frame(self.overview_tab, padding=8)
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="SAVE.DAT function blocks").pack(anchor="w")
        tree = ttk.Treeview(right, columns=("idx", "name", "start", "end", "size", "status"), show="headings", height=24)
        for col, width in [("idx", 45), ("name", 210), ("start", 85), ("end", 85), ("size", 80), ("status", 150)]:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="both", expand=True)
        for block in self.sd.blocks:
            tree.insert("", "end", values=(block.index, block.name, f"0x{block.start:X}", f"0x{block.end:X}", f"0x{block.size:X}", block.parser_status))

    def _field_entry(self, parent, field_name: str, row: int, *, label: str | None = None, width: int = 14, readonly: bool = False, combo_values: list[str] | None = None) -> None:
        ttk = self.ttk
        field = self.sd.fields[field_name]
        ttk.Label(parent, text=label or field_name, width=32).grid(row=row, column=0, sticky="w", padx=4, pady=2)
        var = self.tk.StringVar(value=str(field.value))
        self.field_vars[field_name] = var
        if combo_values is not None:
            widget = ttk.Combobox(parent, textvariable=var, values=combo_values, width=width, state="readonly")
            current = next((v for v in combo_values if v.startswith(f"{field.value}:")), str(field.value))
            var.set(current)
        else:
            widget = ttk.Entry(parent, textvariable=var, width=width)
            if readonly or not field.writable:
                widget.configure(state="readonly")
        widget.grid(row=row, column=1, sticky="w", padx=4, pady=2)
        ttk.Label(parent, text=f"0x{field.abs_offset:X}", width=12).grid(row=row, column=2, sticky="w", padx=4)
        ttk.Label(parent, text=field.risk, width=12).grid(row=row, column=3, sticky="w", padx=4)
        if field.description:
            ttk.Label(parent, text=field.description).grid(row=row, column=4, sticky="w", padx=4)

    def _header_row(self, parent, row: int) -> None:
        for col, title in enumerate(["Field", "Value", "Offset", "Risk", "Description"]):
            self.ttk.Label(parent, text=title).grid(row=row, column=col, sticky="w", padx=4, pady=(4, 6))

    def _scrollable(self, parent):
        tk = self.tk
        ttk = self.ttk
        outer = ttk.Frame(parent)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return inner

    def _stage_patch(self, patch: dict[str, int], label: str) -> None:
        staged = 0
        for name, value in patch.items():
            var = self.field_vars.get(name)
            if var is not None:
                var.set(str(value))
                staged += 1
        self.status_var.set(f"Staged {staged} field(s) for {label}. Use Preview diff before Write changes.")

    def _stage_preset(self, preset: str) -> None:
        if self.session is None:
            return
        try:
            self._stage_patch(self.session.save_dat.preset_patch(preset), preset)
        except Exception as exc:
            self.messagebox.showerror("Preset failed", str(exc))

    def _build_player_tab(self) -> None:
        frame = self.ttk.Frame(self.player_tab, padding=8)
        frame.pack(fill="both", expand=True)
        actions = self.ttk.Frame(frame)
        actions.grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 8))
        self.ttk.Button(actions, text="Stage heal / clear rads+poison", command=lambda: self._stage_preset("heal")).pack(side="left", padx=(0, 6))
        self.ttk.Button(actions, text="Stage clear crippled parts", command=lambda: self._stage_preset("clear-crippled")).pack(side="left", padx=(0, 6))
        self._header_row(frame, 1)
        fields = [
            "player.current_hp", "player.radiation", "player.poison", "player.crippled_body_parts",
            "pc.skill_points", "pc.level", "pc.experience", "pc.reputation", "pc.karma",
            "player.coordinates", "player.facing", "player.map_level",
        ]
        for row, name in enumerate(fields, start=2):
            self._field_entry(frame, name, row)

    def _build_special_tab(self) -> None:
        frame = self.ttk.Frame(self.special_tab, padding=8)
        frame.pack(fill="both", expand=True)
        actions = self.ttk.Frame(frame)
        actions.grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 8))
        self.ttk.Button(actions, text="Stage all base S.P.E.C.I.A.L. = 10", command=lambda: self._stage_preset("max-special")).pack(side="left", padx=(0, 6))
        self._header_row(frame, 1)
        row = 2
        self.ttk.Label(frame, text="Base S.P.E.C.I.A.L.").grid(row=row, column=0, sticky="w", pady=(8, 2))
        row += 1
        for stat in SPECIAL_NAMES:
            self._field_entry(frame, f"player.base_{stat}", row, label=f"base {stat}", width=8)
            row += 1
        row += 1
        self.ttk.Label(frame, text="Bonus S.P.E.C.I.A.L.").grid(row=row, column=0, sticky="w", pady=(8, 2))
        row += 1
        for stat in SPECIAL_NAMES:
            self._field_entry(frame, f"player.bonus_{stat}", row, label=f"bonus {stat}", width=8)
            row += 1
        row += 1
        self.ttk.Label(frame, text="Derived / advanced stats").grid(row=row, column=0, sticky="w", pady=(8, 2))
        row += 1
        for name in ["base_hitpoints", "base_action_points", "base_armor_class", "base_melee_damage", "base_carry_weight", "base_sequence", "base_healing_rate", "base_critical_chance", "radiation_resistance", "poison_resistance", "starting_age", "gender"]:
            self._field_entry(frame, f"player.{name}", row, label=name, width=8)
            row += 1

        summary = self.ttk.LabelFrame(frame, text="Effective static preview: base + bonus + always-on trait adjustment", padding=8)
        summary.grid(row=2, column=5, rowspan=max(row, 18), sticky="nsew", padx=(24, 0))
        tree = self.ttk.Treeview(summary, columns=("stat", "base", "bonus", "trait", "effective"), show="headings", height=9)
        for col, width in [("stat", 120), ("base", 60), ("bonus", 60), ("trait", 60), ("effective", 80)]:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="both", expand=True)
        if self.session is not None:
            for stat, values in self.session.effective_special().items():
                tree.insert("", "end", values=(stat, values["base"], values["bonus"], values["static_trait"], values["effective_static"]))

    def _build_skills_tab(self) -> None:
        inner = self._scrollable(self.skills_tab)
        self._header_row(inner, 0)
        row = 1
        for skill in SKILL_NAMES:
            self._field_entry(inner, f"skills.{skill}", row, label=skill, width=8)
            row += 1
        row += 1
        self.ttk.Label(inner, text="Tagged skills").grid(row=row, column=0, sticky="w", pady=(12, 2))
        row += 1
        skill_values = ["-1: none"] + [f"{i}: {name}" for i, name in enumerate(SKILL_NAMES)]
        for idx in range(4):
            self._field_entry(inner, f"tag_skills.{idx}", row, label=f"tag skill {idx}", combo_values=skill_values, width=24)
            row += 1

    def _build_traits_tab(self) -> None:
        frame = self.ttk.Frame(self.traits_tab, padding=8)
        frame.pack(fill="both", expand=True)
        self._header_row(frame, 0)
        values = ["-1: none"] + [f"{i}: {name}" for i, name in enumerate(TRAIT_NAMES)]
        for row, idx in enumerate(range(2), start=1):
            self._field_entry(frame, f"traits.trait_{idx}", row, label=f"trait {idx}", combo_values=values, width=30)
        self.ttk.Label(frame, text="Validation blocks duplicate traits. Fallout 1 permits at most two active traits.", padding=(4, 12)).grid(row=4, column=0, columnspan=5, sticky="w")
        notes = self.tk.Text(frame, height=10, wrap="word")
        notes.grid(row=5, column=0, columnspan=5, sticky="nsew", padx=4, pady=(6, 0))
        if self.session is not None:
            active_notes = self.session.trait_effect_notes()
            if active_notes:
                notes.insert("end", "Active trait effects from Fallout 1 source/runtime model:\n" + "\n".join(f"- {n}" for n in active_notes))
            else:
                notes.insert("end", "No active traits in this save.")
        notes.configure(state="disabled")

    def _build_inventory_tab(self) -> None:
        ttk = self.ttk
        top = ttk.Frame(self.inventory_tab, padding=8)
        top.pack(fill="both", expand=True)
        tree = ttk.Treeview(top, columns=("idx", "offset", "qty", "pid", "type", "name", "size", "ammo", "ammo_type"), show="headings", height=8)
        for col, width in [("idx", 45), ("offset", 85), ("qty", 70), ("pid", 70), ("type", 90), ("name", 180), ("size", 70), ("ammo", 90), ("ammo_type", 90)]:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="w")
        tree.pack(fill="x")
        for item in self.sd.player_object.inventory:
            tree.insert("", "end", values=(item.index, f"0x{item.start:X}", item.quantity, item.pid, item.type_name, item.object_name, f"0x{item.size:X}", item.ammo_or_charges, item.ammo_type))
        edit = self._scrollable(self.inventory_tab)
        self._header_row(edit, 0)
        row = 1
        for item in self.sd.player_object.inventory:
            self.ttk.Label(edit, text=f"#{item.index} {item.object_name} PID={item.pid}").grid(row=row, column=0, sticky="w", pady=(8, 2))
            row += 1
            for suffix in ["quantity", "ammo_or_charges", "ammo_type"]:
                name = f"inventory.{item.index}.{suffix}"
                if name in self.sd.fields:
                    self._field_entry(edit, name, row, label=f"{item.index}.{suffix}", width=10)
                    row += 1

    def _build_perks_tab(self) -> None:
        inner = self._scrollable(self.perks_tab)
        self._header_row(inner, 0)
        row = 1
        for perk in PERK_NAMES:
            name = f"perks.{perk}"
            if name in self.sd.fields:
                self._field_entry(inner, name, row, label=perk, width=8)
                row += 1
        self.ttk.Label(inner, text="Perk editing is raw rank editing only; engine-side side effects are not fully emulated.", padding=(4, 12)).grid(row=row, column=0, columnspan=5, sticky="w")

    def _build_kills_tab(self) -> None:
        inner = self._scrollable(self.kills_tab)
        self._header_row(inner, 0)
        row = 1
        names = [n for n in self.sd.fields if n.startswith("kill_counts.")]
        for name in sorted(names, key=lambda n: self.sd.fields[n].abs_offset):
            idx = name.rsplit("_", 1)[-1] if "_" in name else str(row - 1)
            label = f"{name.split('.', 1)[1]}"
            self._field_entry(inner, name, row, label=label, width=10)
            row += 1
        self.ttk.Label(inner, text="Kill labels are exposed as stable source-order indices to avoid guessing localized message names.", padding=(4, 12)).grid(row=row, column=0, columnspan=5, sticky="w")

    def _build_options_tab(self) -> None:
        inner = self._scrollable(self.options_tab)
        self._header_row(inner, 0)
        row = 1
        names = [n for n in self.sd.fields if n.startswith("options.")]
        for name in sorted(names, key=lambda n: self.sd.fields[n].abs_offset):
            self._field_entry(inner, name, row, label=name.split('.', 1)[1], width=10)
            row += 1
        self.ttk.Label(inner, text="Options follow the Fallout 1 save_options block. Some fields are ADVANCED until fully mapped to the in-game UI.", padding=(4, 12)).grid(row=row, column=0, columnspan=5, sticky="w")

    def _build_fields_tab(self) -> None:
        ttk = self.ttk
        frame = ttk.Frame(self.fields_tab, padding=8)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=("name", "value", "offset", "rel", "size", "risk", "writable"), show="headings")
        for col, width in [("name", 300), ("value", 100), ("offset", 90), ("rel", 80), ("size", 55), ("risk", 105), ("writable", 70)]:
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="w")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        for field in sorted(self.sd.fields.values(), key=lambda f: (f.abs_offset, f.name)):
            tree.insert("", "end", values=(field.name, field.value, f"0x{field.abs_offset:X}", f"0x{field.rel_offset:X}", field.size, field.risk, str(field.writable)))

    def _build_raw_tab(self) -> None:
        ttk = self.ttk
        frame = ttk.Frame(self.raw_tab, padding=8)
        frame.pack(fill="both", expand=True)
        row = 0
        ttk.Label(frame, text="Offset").grid(row=row, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.raw_offset_var, width=16).grid(row=row, column=1, sticky="w", padx=4)
        ttk.Label(frame, text="Size").grid(row=row, column=2, sticky="w")
        ttk.Entry(frame, textvariable=self.raw_size_var, width=8).grid(row=row, column=3, sticky="w", padx=4)
        ttk.Button(frame, text="Read", command=self.raw_read).grid(row=row, column=4, padx=4)
        row += 1
        ttk.Label(frame, text="Hex payload").grid(row=row, column=0, sticky="w", pady=(8, 2))
        ttk.Entry(frame, textvariable=self.raw_hex_var, width=80).grid(row=row, column=1, columnspan=3, sticky="we", padx=4, pady=(8, 2))
        ttk.Button(frame, text="Preview raw write", command=self.raw_preview).grid(row=row, column=4, padx=4, pady=(8, 2))
        ttk.Button(frame, text="Write raw", command=self.raw_write).grid(row=row, column=5, padx=4, pady=(8, 2))
        row += 1
        ttk.Checkbutton(frame, text="I understand raw writes are EXPERIMENTAL and bypass validators", variable=self.raw_write_ack_var).grid(row=row, column=0, columnspan=6, sticky="w", pady=(8, 8))
        row += 1
        self.raw_text = self.tk.Text(frame, height=18, wrap="none")
        self.raw_text.grid(row=row, column=0, columnspan=6, sticky="nsew")
        frame.rowconfigure(row, weight=1)
        frame.columnconfigure(3, weight=1)

    def _build_validation_tab(self) -> None:
        ttk = self.ttk
        frame = ttk.Frame(self.validation_tab, padding=8)
        frame.pack(fill="both", expand=True)
        ttk.Button(frame, text="Run verify", command=self.verify).pack(anchor="w")
        self.validation_text = self.tk.Text(frame, height=16, wrap="word")
        self.validation_text.pack(fill="both", expand=True, pady=(8, 8))
        self.diff_text = self.tk.Text(frame, height=12, wrap="none")
        self.diff_text.pack(fill="both", expand=True)
        self._write_validation_text()

    def _write_validation_text(self) -> None:
        if not hasattr(self, "validation_text"):
            return
        self.validation_text.delete("1.0", "end")
        if self.session is None:
            self.validation_text.insert("end", "No slot loaded.\n")
            return
        issues = self.session.validation_issues()
        if issues:
            self.validation_text.insert("end", "FAIL:\n")
            for issue in issues:
                self.validation_text.insert("end", f"- {issue}\n")
        else:
            self.validation_text.insert("end", "OK\n")
        warnings = self.session.summary()["warnings"]
        if warnings:
            self.validation_text.insert("end", "\nWarnings:\n")
            for warning in warnings:
                self.validation_text.insert("end", f"- {warning}\n")

    def _collect_patch(self) -> dict[str, int]:
        patch: dict[str, int] = {}
        for name, var in self.field_vars.items():
            if name not in self.sd.fields:
                continue
            field = self.sd.fields[name]
            if not field.writable or field.type_name != "i32":
                continue
            new_value = _parse_int_text(var.get())
            old_value = int(field.value)
            if new_value != old_value:
                patch[name] = new_value
        return patch

    def _mode(self) -> str:
        return "semantic" if self.semantic_mode_var.get() else "raw"

    def _render_diffs(self, diffs: Iterable) -> None:
        if self.diff_text is None:
            return
        self.diff_text.delete("1.0", "end")
        diffs = list(diffs)
        if not diffs:
            self.diff_text.insert("end", "No byte changes.\n")
            return
        for diff in diffs:
            self.diff_text.insert("end", format_diff(diff) + "\n")

    def preview_diff(self) -> None:
        if self.session is None:
            return
        try:
            patch = self._collect_patch()
            diffs = self.session.preview_patch(patch, allow_out_of_range=self.allow_out_of_range_var.get(), mode=self._mode())
            self._render_diffs(diffs)
            self.notebook.select(self.validation_tab)
            self.status_var.set(f"Preview: {len(diffs)} byte-range changes, {len(patch)} fields.")
        except Exception as exc:
            self.messagebox.showerror("Preview failed", str(exc))

    def write_changes(self) -> None:
        if self.session is None:
            return
        try:
            patch = self._collect_patch()
            diffs = self.session.preview_patch(patch, allow_out_of_range=self.allow_out_of_range_var.get(), mode=self._mode())
            if not diffs:
                self._render_diffs([])
                self.status_var.set("No changes to write.")
                return
            if not self.messagebox.askyesno("Write SAVE.DAT", f"Write {len(diffs)} byte-range changes to SAVE.DAT? A slot backup will be created first."):
                return
            result = self.session.apply_patch(patch, write=True, allow_out_of_range=self.allow_out_of_range_var.get(), mode=self._mode())
            written_diffs = list(result.diffs)
            self._rebuild_all_tabs()
            self._render_diffs(written_diffs)
            self.notebook.select(self.validation_tab)
            self.status_var.set(f"Written. Backup: {result.backup_path}")
        except Exception as exc:
            self.messagebox.showerror("Write failed", str(exc))

    def verify(self) -> None:
        if self.session is None:
            return
        self._write_validation_text()
        self.notebook.select(self.validation_tab)
        issues = self.session.validation_issues()
        self.status_var.set("Verify OK." if not issues else f"Verify found {len(issues)} issue(s).")

    def raw_read(self) -> None:
        if self.session is None:
            return
        try:
            offset = int(self.raw_offset_var.get(), 0)
            size = int(self.raw_size_var.get(), 0)
            payload = self.session.raw_read(offset, size)
            self.raw_text.delete("1.0", "end")
            self.raw_text.insert("end", payload.hex())
            self.raw_hex_var.set(payload.hex())
            self.status_var.set(f"Read {size} bytes from SAVE.DAT:0x{offset:X}")
        except Exception as exc:
            self.messagebox.showerror("Raw read failed", str(exc))

    def raw_preview(self) -> None:
        if self.session is None:
            return
        try:
            offset = int(self.raw_offset_var.get(), 0)
            payload = bytes.fromhex(self.raw_hex_var.get().strip())
            diffs = self.session.raw_preview(offset, payload)
            self._render_diffs(diffs)
            self.notebook.select(self.validation_tab)
            self.status_var.set(f"Raw preview: {len(diffs)} byte-range changes.")
        except Exception as exc:
            self.messagebox.showerror("Raw preview failed", str(exc))

    def raw_write(self) -> None:
        if self.session is None:
            return
        try:
            offset = int(self.raw_offset_var.get(), 0)
            payload = bytes.fromhex(self.raw_hex_var.get().strip())
            if not self.raw_write_ack_var.get():
                self.messagebox.showerror("Raw write blocked", "Enable the explicit EXPERIMENTAL raw-write checkbox first.")
                return
            if not self.messagebox.askyesno("Raw write", "Raw writes bypass field validators. Write anyway after creating backup?"):
                return
            result = self.session.raw_write(offset, payload, write=True)
            written_diffs = list(result.diffs)
            self._rebuild_all_tabs()
            self._render_diffs(written_diffs)
            self.notebook.select(self.validation_tab)
            self.status_var.set(f"Raw write completed. Backup: {result.backup_path}")
        except Exception as exc:
            self.messagebox.showerror("Raw write failed", str(exc))


def run_gui(slot: str | Path | None = None) -> int:
    tk, _ttk, _filedialog, messagebox = _lazy_tk()
    root = tk.Tk()
    try:
        F1SaveEditorApp(root, slot)
        root.mainloop()
    except Exception as exc:  # late GUI-level safety net
        messagebox.showerror("f1se GUI error", str(exc))
        return 1
    return 0
