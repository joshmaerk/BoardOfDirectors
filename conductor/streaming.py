"""Rich-based multi-pane live streaming for the roundtable."""
from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Callable

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .client import TokenLedger


@dataclass
class PaneState:
    title: str
    avatar: str
    text: str = ""
    style: str = "white"


@dataclass
class RoundtableDisplay:
    """Multi-pane live display. One panel per active persona, plus header and footer."""

    console: Console = field(default_factory=Console)
    ledger: TokenLedger | None = None
    header: str = ""
    panes: "OrderedDict[str, PaneState]" = field(default_factory=OrderedDict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _live: Live | None = None

    def open(self) -> None:
        self._live = Live(
            self._render(), console=self.console, refresh_per_second=12, transient=False
        )
        self._live.start()

    def close(self) -> None:
        if self._live is not None:
            self._live.update(self._render())
            self._live.stop()
            self._live = None

    def __enter__(self) -> "RoundtableDisplay":
        self.open()
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def set_header(self, text: str) -> None:
        with self._lock:
            self.header = text
        self._refresh()

    def reset_panes(self) -> None:
        with self._lock:
            self.panes.clear()
        self._refresh()

    def add_pane(self, key: str, title: str, avatar: str, style: str = "white") -> None:
        with self._lock:
            self.panes[key] = PaneState(title=title, avatar=avatar, style=style)
        self._refresh()

    def appender(self, key: str) -> Callable[[str], None]:
        def append(chunk: str) -> None:
            with self._lock:
                if key in self.panes:
                    self.panes[key].text += chunk
            self._refresh()

        return append

    def set_full_text(self, key: str, text: str) -> None:
        with self._lock:
            if key in self.panes:
                self.panes[key].text = text
        self._refresh()

    def _render(self) -> Group:
        items = []
        if self.header:
            items.append(
                Panel(Text(self.header, style="bold cyan"), border_style="cyan")
            )
        for pane in self.panes.values():
            body = Text(pane.text or "...", style=pane.style)
            title = f"{pane.avatar}  {pane.title}"
            items.append(Panel(body, title=title, border_style=pane.style))
        items.append(Panel(Text(self._footer_text(), style="bold"), border_style="grey50"))
        return Group(*items)

    def _footer_text(self) -> str:
        if not self.ledger:
            return ""
        status = self.ledger.status
        return (
            f"Tokens: in {self.ledger.input}  out {self.ledger.output}/"
            f"{self.ledger.budget_total}  ({status})"
        )

    def _refresh(self) -> None:
        if self._live is not None:
            self._live.update(self._render())
