"""click-based CLI entry point."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console

from .archive import Archive
from .conductor import SessionRunner
from .config import Config
from .streaming import RoundtableDisplay

DEFAULT_CONFIG_PATH = "config.yaml"


def _load_config(path: str) -> Config:
    try:
        return Config.load(path)
    except FileNotFoundError as e:
        click.echo(str(e), err=True)
        sys.exit(2)


@click.group()
@click.option(
    "--config",
    "config_path",
    default=DEFAULT_CONFIG_PATH,
    show_default=True,
    help="Pfad zur config.yaml",
)
@click.pass_context
def main(ctx: click.Context, config_path: str) -> None:
    """Personal Board of Directors - Roundtable-Sparring im Terminal."""
    load_dotenv()
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path


@main.command()
@click.argument("question", required=False)
@click.option(
    "--topic-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Datei mit der Frage anstelle eines Argument-Strings.",
)
@click.option(
    "--memory",
    is_flag=True,
    default=False,
    help="Persona-Memories aus früheren Sessions laden und am Ende anhängen.",
)
@click.option(
    "--persona-only",
    default=None,
    help="Komma-getrennte Liste aktiver Personen (Moderator läuft immer mit).",
)
@click.option(
    "--no-stream",
    is_flag=True,
    default=False,
    help="Live-Streaming-Display deaktivieren (z.B. für non-TTY-Output).",
)
@click.pass_context
def ask(
    ctx: click.Context,
    question: str | None,
    topic_file: Path | None,
    memory: bool,
    persona_only: str | None,
    no_stream: bool,
) -> None:
    """Stelle dem Board eine Frage."""
    if topic_file is not None:
        question = topic_file.read_text(encoding="utf-8").strip()
    if not question:
        raise click.UsageError("Bitte eine Frage als Argument oder via --topic-file übergeben.")

    config = _load_config(ctx.obj["config_path"])
    filter_list: list[str] | None = None
    if persona_only:
        filter_list = [p.strip() for p in persona_only.split(",") if p.strip()]

    runner = SessionRunner(config)
    display = None if no_stream else RoundtableDisplay()

    async def _go():
        if display is not None:
            with display:
                return await runner.run(
                    question,
                    memory=memory,
                    persona_filter=filter_list,
                    display=display,
                )
        return await runner.run(
            question,
            memory=memory,
            persona_filter=filter_list,
            display=None,
        )

    try:
        state, path = asyncio.run(_go())
    except KeyboardInterrupt:
        click.echo("\nSession abgebrochen. Teil-Archiv wurde geschrieben.", err=True)
        sys.exit(130)

    click.echo(f"\nArchiv geschrieben: {path}")
    if state.aborted:
        click.echo(f"Hinweis: Session vorzeitig beendet ({state.abort_reason})", err=True)


@main.group("archive")
def archive_cmd() -> None:
    """Archiv-Subkommandos."""


@archive_cmd.command("list")
@click.pass_context
def archive_list(ctx: click.Context) -> None:
    config = _load_config(ctx.obj["config_path"])
    arc = Archive(config.archive)
    files = arc.list()
    if not files:
        click.echo("Keine Archive vorhanden.")
        return
    for f in files:
        click.echo(f.name)


@archive_cmd.command("show")
@click.argument("filename")
@click.pass_context
def archive_show(ctx: click.Context, filename: str) -> None:
    config = _load_config(ctx.obj["config_path"])
    path = Path(config.archive.output_dir) / filename
    if not path.exists():
        raise click.UsageError(f"Archiv nicht gefunden: {path}")
    console = Console()
    console.print(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
