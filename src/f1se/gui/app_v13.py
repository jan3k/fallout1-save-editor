"""v0.13 GUI write-control finalizer.

Keeps the raw Fallout 2 controls blocked while enabling the normal
"Write changes" button for the v0.12 allowlisted GUI editor.
"""
from __future__ import annotations

from pathlib import Path

from f1se.gui.app import F1SaveEditorApp, _lazy_tk
from f1se.gui.app_v11 import _iter_widgets
from f1se.gui.app_v12 import _install as _install_v12
from f1se.project.game_profile import GameKind

_INSTALLED = False


def _is_fallout2(app: F1SaveEditorApp) -> bool:
    return app.session is not None and getattr(app.session, "game_kind", None) is GameKind.FALLOUT2


def _enable_write_changes(app: F1SaveEditorApp) -> None:
    for widget in _iter_widgets(app.root):
        try:
            text = widget.cget("text")
        except Exception:
            continue
        if text == "Write changes":
            try:
                widget.configure(state="normal")
            except Exception:
                pass


def _install() -> None:
    global _INSTALLED
    if _INSTALLED:
        return
    _install_v12()

    original_rebuild_all_tabs = F1SaveEditorApp._rebuild_all_tabs
    original_open_slot = F1SaveEditorApp.open_slot
    original_reload_slot = F1SaveEditorApp.reload_slot

    def _after_fallout2_gui_refresh(self: F1SaveEditorApp) -> None:
        if _is_fallout2(self):
            _enable_write_changes(self)
            self.status_var.set("Loaded Fallout 2 save with allowlisted GUI editing. Use Preview diff before Write changes.")

    def _rebuild_all_tabs(self: F1SaveEditorApp):
        result = original_rebuild_all_tabs(self)
        _after_fallout2_gui_refresh(self)
        return result

    def open_slot(self: F1SaveEditorApp, slot_path: str | Path) -> None:
        result = original_open_slot(self, slot_path)
        _after_fallout2_gui_refresh(self)
        return result

    def reload_slot(self: F1SaveEditorApp) -> None:
        result = original_reload_slot(self)
        _after_fallout2_gui_refresh(self)
        return result

    F1SaveEditorApp._rebuild_all_tabs = _rebuild_all_tabs
    F1SaveEditorApp.open_slot = open_slot
    F1SaveEditorApp.reload_slot = reload_slot
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
