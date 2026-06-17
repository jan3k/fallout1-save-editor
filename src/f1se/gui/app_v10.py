"""v0.10 guided GUI workflow extensions.

This module wraps the existing Tk app without adding a second parser or writer.
All payloads come from f1se.gui.model.
"""
from __future__ import annotations

from pathlib import Path

from f1se.gui.app import F1SaveEditorApp, _lazy_tk

_INSTALLED = False


def _simple_tree(app, parent, columns: tuple[str, ...], rows: list[tuple]) -> None:
    ttk = app.ttk
    frame = ttk.Frame(parent, padding=8)
    frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=140, anchor="w")
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    for row in rows:
        tree.insert("", "end", values=row)


def _install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    original_build_empty_tabs = F1SaveEditorApp._build_empty_tabs
    original_rebuild_all_tabs = F1SaveEditorApp._rebuild_all_tabs
    original_build_shell = F1SaveEditorApp._build_shell
    original_write_changes = F1SaveEditorApp.write_changes
    original_preview_diff = F1SaveEditorApp.preview_diff

    def _build_shell(self):
        original_build_shell(self)
        self.advanced_write_ack_var = self.tk.BooleanVar(value=False)
        self.dirty_state_var = self.tk.StringVar(value="Dirty: no changes")
        opts = self.root.winfo_children()[1]
        self.ttk.Checkbutton(opts, text="I understand ADVANCED fields may have engine-side effects", variable=self.advanced_write_ack_var).pack(side="left", padx=16)
        self.ttk.Button(opts, text="Reset Changes", command=self.reset_changes).pack(side="left", padx=4)
        self.ttk.Label(opts, textvariable=self.dirty_state_var).pack(side="left", padx=12)

    def _build_empty_tabs(self):
        original_build_empty_tabs(self)
        self.artifacts_tab = self.ttk.Frame(self.notebook)
        self.raw_blocks_tab = self.ttk.Frame(self.notebook)
        self.global_scan_tab = self.ttk.Frame(self.notebook)
        self.map_scan_tab = self.ttk.Frame(self.notebook)
        for tab, title in [
            (self.artifacts_tab, "Artifacts"),
            (self.raw_blocks_tab, "Raw Blocks"),
            (self.global_scan_tab, "Global Scan"),
            (self.map_scan_tab, "Map Scan"),
        ]:
            self.notebook.add(tab, text=title)

    def _rebuild_all_tabs(self):
        original_rebuild_all_tabs(self)
        for tab in [self.artifacts_tab, self.raw_blocks_tab, self.global_scan_tab, self.map_scan_tab]:
            self._clear(tab)
        self._build_artifacts_tab()
        self._build_raw_blocks_diag_tab()
        self._build_global_scan_diag_tab()
        self._build_map_scan_diag_tab()
        self._update_dirty_indicator({})

    def _build_artifacts_tab(self):
        rows = []
        for artifact in self.session.artifacts_payload()["artifacts"]:
            rows.append((artifact["name"], artifact["kind"], artifact["size"], artifact["sha256"], artifact["parser_status"], "read-only"))
        _simple_tree(self, self.artifacts_tab, ("name", "kind", "size", "sha256", "status", "risk"), rows)

    def _build_raw_blocks_diag_tab(self):
        rows = []
        for block in self.session.raw_blocks_payload()["raw_blocks"]:
            rows.append((block["index"], block["name"], block["start_hex"], block["end_hex"], block["size_hex"], block["parser_status"], block["entropy_hint"], "read-only"))
        _simple_tree(self, self.raw_blocks_tab, ("idx", "name", "start", "end", "size", "status", "hint", "risk"), rows)

    def _build_global_scan_diag_tab(self):
        rows = []
        for item in self.session.globals_scan_payload()["candidates"]:
            rows.append((item["block_index"], item["block_name"], item["start_hex"], item["end_hex"], item["i32_count"], item["nonzero_i32_count"], item["confidence"], "read-only"))
        _simple_tree(self, self.global_scan_tab, ("idx", "name", "start", "end", "i32", "nonzero", "confidence", "risk"), rows)

    def _build_map_scan_diag_tab(self):
        rows = []
        for item in self.session.map_scan_payload()["maps"]:
            rows.append((item["file_name"], item["size"], item["sha256"], item["parser_status"], item["candidate_count"], "heuristic-read-only"))
        _simple_tree(self, self.map_scan_tab, ("file", "size", "sha256", "status", "candidates", "risk"), rows)

    def _update_dirty_indicator(self, patch):
        if not hasattr(self, "dirty_state_var") or self.session is None:
            return
        state = self.session.dirty_state(patch).to_dict()
        risks = ",".join(state["risks"]) if state["risks"] else "none"
        self.dirty_state_var.set(f"Dirty: {state['changed_field_count']} field(s), risks={risks}")

    def reset_changes(self):
        if self.session is None:
            return
        for name, value in self.session.reset_changes_model().items():
            var = self.field_vars.get(name)
            if var is not None:
                var.set(str(value))
        self._update_dirty_indicator({})
        self.status_var.set("Reset form values from current SAVE.DAT; no files modified.")

    def preview_diff(self):
        original_preview_diff(self)
        if self.session is not None:
            self._update_dirty_indicator(self._collect_patch())

    def write_changes(self):
        if self.session is None:
            return
        patch = self._collect_patch()
        if self.session.requires_advanced_confirmation(patch) and not self.advanced_write_ack_var.get():
            self.messagebox.showerror("Advanced write blocked", "Enable the ADVANCED confirmation checkbox first.")
            return
        original_write_changes(self)

    F1SaveEditorApp._build_shell = _build_shell
    F1SaveEditorApp._build_empty_tabs = _build_empty_tabs
    F1SaveEditorApp._rebuild_all_tabs = _rebuild_all_tabs
    F1SaveEditorApp._build_artifacts_tab = _build_artifacts_tab
    F1SaveEditorApp._build_raw_blocks_diag_tab = _build_raw_blocks_diag_tab
    F1SaveEditorApp._build_global_scan_diag_tab = _build_global_scan_diag_tab
    F1SaveEditorApp._build_map_scan_diag_tab = _build_map_scan_diag_tab
    F1SaveEditorApp._update_dirty_indicator = _update_dirty_indicator
    F1SaveEditorApp.reset_changes = reset_changes
    F1SaveEditorApp.preview_diff = preview_diff
    F1SaveEditorApp.write_changes = write_changes
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
