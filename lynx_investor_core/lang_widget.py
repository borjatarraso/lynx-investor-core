"""Reusable bottom-right "language toggle" widgets.

Two thin helpers that every Suite GUI / TUI app calls so the user
sees the same little badge in the same corner everywhere:

* :func:`mount_tk_language_button` — Tkinter ``Button`` placed in the
  bottom-right corner of a ``tk.Tk`` / ``tk.Toplevel``. Shows the
  current language code (``EN`` / ``ES`` / …) and cycles on click.
  Right-click pops a chooser menu so the user can jump straight to
  any supported language.

* :func:`textual_language_bindings` — returns a list of Textual
  ``Binding`` instances and a small status-bar widget class that the
  caller can mount in a footer / header. Pressing ``L`` cycles; the
  badge updates automatically.

Both helpers share state via :mod:`lynx_investor_core.translations`,
so toggling in one app persists to the user-config file and applies
across the whole Suite the next time apps start.
"""

from __future__ import annotations

from typing import Callable, Optional

from lynx_investor_core import translations as _tr


# ---------------------------------------------------------------------------
# Tkinter helper
# ---------------------------------------------------------------------------

def mount_tk_language_button(
    root,
    *,
    on_change: Optional[Callable[[str], None]] = None,
    bg: str = "#2a2a3d",
    fg: str = "#cdd6f4",
    accent: str = "#89b4fa",
):
    """Mount a small language-toggle button in the bottom-right of *root*.

    Returns the created widget so the caller can ``.lift()`` it on top
    of any Frame that gets re-packed later. Re-mounting is idempotent —
    the button keeps a single ``_lynx_language_btn`` attribute on
    *root* that subsequent calls reuse.
    """
    import tkinter as tk

    existing = getattr(root, "_lynx_language_btn", None)
    if existing is not None and str(existing) in str(existing.tk):
        return existing

    label_var = tk.StringVar(value=_tr.language_code_label())

    btn = tk.Button(
        root,
        textvariable=label_var,
        bg=accent,
        fg="#1e1e2e",
        activebackground=bg,
        activeforeground=fg,
        bd=0,
        padx=12,
        pady=4,
        cursor="hand2",
        font=("Helvetica", 11, "bold"),
        relief="flat",
        highlightthickness=2,
        highlightbackground=accent,
        highlightcolor=accent,
    )
    btn.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)
    try:
        btn.lift()
        # Re-lift after every window event so packed widgets don't bury it.
        root.bind("<Configure>", lambda _e, b=btn: b.lift(), add="+")
    except Exception:
        pass

    def _show_restart_toast(new_code: str) -> None:
        """Briefly inform the user that they need to restart for the new
        language to apply across the whole UI. The toast auto-dismisses
        so it doesn't block keyboard input."""
        try:
            msg = _tr.t("lang_restart_required", lang=new_code)
            badge = _tr.language_code_label(new_code)
            toast = tk.Toplevel(root)
            toast.wm_overrideredirect(True)
            toast.configure(bg=accent)
            try:
                toast.attributes("-topmost", True)
            except tk.TclError:
                pass
            tk.Label(
                toast, text=f"  {badge}  {msg}  ",
                bg=accent, fg="#1e1e2e",
                font=("Helvetica", 11, "bold"),
                padx=10, pady=6,
            ).pack()
            toast.update_idletasks()
            try:
                rx, ry = root.winfo_rootx(), root.winfo_rooty()
                rw, rh = root.winfo_width(), root.winfo_height()
                tw, th = toast.winfo_width(), toast.winfo_height()
                toast.geometry(f"+{rx + (rw - tw) // 2}+{ry + rh - th - 60}")
            except tk.TclError:
                pass
            toast.after(3500, lambda: toast.destroy() if toast.winfo_exists() else None)
        except Exception:
            pass

    def _cycle(_event=None):
        new_code = _tr.cycle_language()
        label_var.set(_tr.language_code_label(new_code))
        _show_restart_toast(new_code)
        if on_change:
            try:
                on_change(new_code)
            except Exception:
                pass

    def _menu(event):
        m = tk.Menu(root, tearoff=0, bg=bg, fg=fg,
                     activebackground=accent, activeforeground="#1e1e2e")
        for code, full in _tr.supported_language_options():
            mark = "● " if code == _tr.current_language() else "○ "
            m.add_command(
                label=f"{mark}{_tr.language_code_label(code)}  —  {full}",
                command=lambda c=code: _set(c),
            )
        try:
            m.tk_popup(event.x_root, event.y_root)
        finally:
            m.grab_release()

    def _set(code: str):
        new_code = _tr.set_language(code)
        label_var.set(_tr.language_code_label(new_code))
        _show_restart_toast(new_code)
        if on_change:
            try:
                on_change(new_code)
            except Exception:
                pass

    btn.configure(command=_cycle)
    btn.bind("<Button-3>", _menu)
    # Tooltip — quick on-hover hint.
    _attach_tooltip(btn, lambda: f"Language: {_tr.language_full_name()}\n"
                                  "Click to cycle • Right-click for menu")

    root._lynx_language_btn = btn
    return btn


def _attach_tooltip(widget, text_provider: Callable[[], str]) -> None:
    import tkinter as tk

    state = {"win": None}

    def _show(_event):
        if state["win"] is not None:
            return
        try:
            x, y = widget.winfo_rootx(), widget.winfo_rooty()
        except Exception:
            return
        win = tk.Toplevel(widget)
        win.wm_overrideredirect(True)
        win.geometry(f"+{x - 60}+{y - 50}")
        lbl = tk.Label(
            win, text=text_provider(),
            bg="#1e1e2e", fg="#cdd6f4",
            justify="left",
            padx=8, pady=4,
            relief="solid", borderwidth=1,
            font=("Helvetica", 9),
        )
        lbl.pack()
        state["win"] = win

    def _hide(_event=None):
        win = state["win"]
        if win is not None:
            try:
                win.destroy()
            except Exception:
                pass
            state["win"] = None

    widget.bind("<Enter>", _show)
    widget.bind("<Leave>", _hide)
    widget.bind("<ButtonPress-1>", _hide, add="+")


# ---------------------------------------------------------------------------
# Textual helper
# ---------------------------------------------------------------------------

def textual_cycle_action():
    """Return a coroutine-friendly action to cycle the language.

    Used by Textual apps that want a single keybinding handler::

        BINDINGS = [Binding("L", "cycle_language", "Language")]

        def action_cycle_language(self):
            new_code = textual_cycle_action()()
            self.notify(f"Language: {new_code.upper()}", timeout=2)
    """
    def _do() -> str:
        return _tr.cycle_language()
    return _do


def language_status_text() -> str:
    """Return the markup the Textual footer / status-bar should show."""
    return f"[bold]🌐 {_tr.language_code_label()}[/]"
