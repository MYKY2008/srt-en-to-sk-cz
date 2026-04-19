#!/usr/bin/env python3
"""Preklad EN .srt titulkov do slovenčiny alebo češtiny pri zachovaní .srt formátu."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

import pysrt
from deep_translator import GoogleTranslator

NL_TOKEN = "__SRT_NEWLINE_TOKEN__"
SUPPORTED_TARGETS = {"sk": "slovenčiny", "cz": "češtiny"}
ENCODING_CANDIDATES = ("utf-8-sig", "utf-8", "cp1250", "latin-1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preklad EN .srt titulkov do slovenčiny (sk) alebo češtiny (cz), "
            "voliteľne s extrakciou titulkov z .mkv."
        )
    )
    parser.add_argument("input", type=Path, help="Cesta k vstupnému EN .srt alebo .mkv súboru")
    parser.add_argument(
        "-t",
        "--target",
        choices=sorted(SUPPORTED_TARGETS.keys()),
        help="Kód cieľového jazyka: sk alebo cz",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Cesta k výstupnému .srt súboru (predvolené: <input_stem>.<target>.srt)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Počet blokov titulkov pre jeden prekladový request (predvolené: 50)",
    )
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Iba extrahuje titulky z .mkv do .srt bez prekladu",
    )
    parser.add_argument(
        "--subtitle-stream",
        type=int,
        help="Index subtitle streamu v MKV (z ffprobe), napr. 2",
    )
    parser.add_argument(
        "--list-subtitle-streams",
        action="store_true",
        help="Vypíše dostupné subtitle streamy v .mkv a skončí",
    )
    return parser.parse_args()


def choose_target_interactively() -> str:
    print("Vyber cieľový jazyk:")
    print("1) sk (slovenčina)")
    print("2) cz (čeština)")
    while True:
        raw = input("Zadaj 1/2 alebo sk/cz: ").strip().lower()
        if raw in {"1", "sk"}:
            return "sk"
        if raw in {"2", "cz"}:
            return "cz"
        print("Neplatná voľba. Zadaj 1, 2, sk alebo cz.")


def resolve_output_path(input_path: Path, target: str, output: Path | None) -> Path:
    if output is not None:
        return output
    return input_path.with_name(f"{input_path.stem}.{target}.srt")


def resolve_extract_output_path(input_path: Path, output: Path | None) -> Path:
    if output is not None:
        return output
    return input_path.with_name(f"{input_path.stem}.extracted.srt")


def load_srt(path: Path) -> pysrt.SubRipFile:
    last_error: Exception | None = None
    for encoding in ENCODING_CANDIDATES:
        try:
            return pysrt.open(str(path), encoding=encoding)
        except Exception as exc:  # pylint: disable=broad-except
            last_error = exc
    assert last_error is not None
    raise RuntimeError(f"Nepodarilo sa načítať {path} podporovanými kódovaniami") from last_error


def chunked(items: list[str], size: int) -> Iterable[list[str]]:
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def needs_translation(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text))


def prepare_text(text: str) -> str:
    return text.replace("\n", f" {NL_TOKEN} ")


def restore_text(text: str) -> str:
    text = re.sub(rf"\s*{re.escape(NL_TOKEN)}\s*", "\n", text)
    return text.strip()


def ensure_ffmpeg_available() -> None:
    missing: list[str] = []
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            missing.append(tool)
    if missing:
        missing_joined = ", ".join(missing)
        raise RuntimeError(
            "Chýba nástroj: "
            f"{missing_joined}. Nainštaluj FFmpeg a pridaj ffmpeg/ffprobe do PATH."
        )


def probe_subtitle_streams(mkv_path: Path) -> list[dict[str, str | int]]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-select_streams",
        "s",
        str(mkv_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        stderr = proc.stderr.strip() or "ffprobe zlyhal bez detailu"
        raise RuntimeError(f"ffprobe zlyhal: {stderr}")

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("ffprobe vrátil neplatný JSON výstup") from exc

    streams = payload.get("streams", [])
    result: list[dict[str, str | int]] = []
    for stream in streams:
        tags = stream.get("tags", {}) if isinstance(stream.get("tags", {}), dict) else {}
        result.append(
            {
                "index": stream.get("index", -1),
                "codec": stream.get("codec_name", "unknown"),
                "language": tags.get("language", "und"),
                "title": tags.get("title", ""),
            }
        )

    return result


def print_subtitle_streams(streams: list[dict[str, str | int]]) -> None:
    if not streams:
        print("V súbore nie sú žiadne subtitle streamy.", flush=True)
        return

    print("Dostupné subtitle streamy:", flush=True)
    for idx, stream in enumerate(streams, start=1):
        title = f", title={stream['title']}" if stream["title"] else ""
        print(
            f"  {idx}) stream_index={stream['index']}, codec={stream['codec']}, "
            f"lang={stream['language']}{title}",
            flush=True,
        )


def choose_stream_interactively(streams: list[dict[str, str | int]]) -> int:
    print_subtitle_streams(streams)
    if not streams:
        raise RuntimeError("V MKV sa nenašli subtitle streamy")

    while True:
        raw = input("Vyber číslo streamu na extrakciu (1..N): ").strip()
        if not raw.isdigit():
            print("Neplatná voľba. Zadaj číslo.")
            continue
        choice = int(raw)
        if 1 <= choice <= len(streams):
            return int(streams[choice - 1]["index"])
        print("Neplatná voľba. Zadaj číslo z ponuky.")


def select_subtitle_stream(
    streams: list[dict[str, str | int]], selected_index: int | None
) -> int:
    if not streams:
        raise RuntimeError("V MKV sa nenašli subtitle streamy")

    if selected_index is not None:
        available_indices = {int(stream["index"]) for stream in streams}
        if selected_index not in available_indices:
            available_text = ", ".join(str(i) for i in sorted(available_indices))
            raise RuntimeError(
                f"Subtitle stream index {selected_index} neexistuje. "
                f"Dostupné indexy: {available_text}"
            )
        return selected_index

    return choose_stream_interactively(streams)


def extract_mkv_subtitles_to_srt(mkv_path: Path, output_srt: Path, stream_index: int) -> None:
    output_srt.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(mkv_path),
        "-map",
        f"0:{stream_index}",
        "-c:s",
        "srt",
        str(output_srt),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        if "Subtitle encoding currently only possible" in stderr or "Error initializing output stream" in stderr:
            raise RuntimeError(
                "Nepodarilo sa skonvertovať subtitle stream do SRT. "
                "Stream môže byť obrazový (PGS/VobSub), ktorý sa bez OCR nedá priamo previesť."
            )
        raise RuntimeError(f"Extrakcia titulkov zlyhala: {stderr or 'ffmpeg zlyhal bez detailu'}")


def translate_subtitles(subs: pysrt.SubRipFile, target: str, batch_size: int) -> tuple[int, int]:
    target_lang = "sk" if target == "sk" else "cs"
    translator = GoogleTranslator(source="en", target=target_lang)

    translatable_indices: list[int] = []
    translatable_texts: list[str] = []

    for idx, sub in enumerate(subs):
        if needs_translation(sub.text):
            translatable_indices.append(idx)
            translatable_texts.append(prepare_text(sub.text))

    if not translatable_texts:
        return 0, len(subs)

    translated_count = 0
    translated_texts: list[str] = []

    for batch in chunked(translatable_texts, batch_size):
        translated_batch = translator.translate_batch(batch)
        if isinstance(translated_batch, str):
            translated_batch = [translated_batch]
        translated_texts.extend(translated_batch)
        translated_count += len(translated_batch)
        print(f"Preložené {translated_count}/{len(translatable_texts)} blokov titulkov...", flush=True)

    for idx, translated in zip(translatable_indices, translated_texts):
        subs[idx].text = restore_text(translated)

    return len(translatable_texts), len(subs)


def main() -> int:
    args = parse_args()

    input_path: Path = args.input
    if not input_path.exists():
        print("Chyba: vstupný súbor neexistuje.", file=sys.stderr)
        return 1

    input_suffix = input_path.suffix.lower()
    if input_suffix not in {".srt", ".mkv"}:
        print("Chyba: vstup musí byť .srt alebo .mkv súbor.", file=sys.stderr)
        return 1

    if args.batch_size < 1:
        print("Chyba: --batch-size musí byť >= 1", file=sys.stderr)
        return 1

    if args.extract_only and input_suffix != ".mkv":
        print("Chyba: --extract-only je dostupné iba pre .mkv vstup.", file=sys.stderr)
        return 1

    if args.list_subtitle_streams and input_suffix != ".mkv":
        print("Chyba: --list-subtitle-streams je dostupné iba pre .mkv vstup.", file=sys.stderr)
        return 1

    subtitle_source_path = input_path

    if input_suffix == ".mkv":
        try:
            ensure_ffmpeg_available()
            streams = probe_subtitle_streams(input_path)
            if args.list_subtitle_streams:
                print_subtitle_streams(streams)
                return 0

            stream_index = select_subtitle_stream(streams, args.subtitle_stream)

            if args.extract_only:
                output_extract_path = resolve_extract_output_path(input_path, args.output)
                extract_mkv_subtitles_to_srt(input_path, output_extract_path, stream_index)
                print(f"Hotovo. Extrahované titulky uložené: {output_extract_path}", flush=True)
                return 0

            with tempfile.NamedTemporaryFile(prefix="mkv_subs_", suffix=".srt", delete=False) as tmp:
                temp_srt_path = Path(tmp.name)

            try:
                extract_mkv_subtitles_to_srt(input_path, temp_srt_path, stream_index)
                subtitle_source_path = temp_srt_path
            except Exception:
                if temp_srt_path.exists():
                    temp_srt_path.unlink(missing_ok=True)
                raise
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Extrakcia z MKV zlyhala: {exc}", file=sys.stderr)
            return 1

    target = args.target or choose_target_interactively()
    output_path = resolve_output_path(input_path, target, args.output)

    temp_to_cleanup: Path | None = subtitle_source_path if input_suffix == ".mkv" else None

    try:
        subs = load_srt(subtitle_source_path)
        translated, total = translate_subtitles(subs, target, args.batch_size)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        subs.save(str(output_path), encoding="utf-8-sig")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Preklad zlyhal: {exc}", file=sys.stderr)
        if temp_to_cleanup and temp_to_cleanup.exists():
            temp_to_cleanup.unlink(missing_ok=True)
        return 1
    finally:
        if temp_to_cleanup and temp_to_cleanup.exists():
            temp_to_cleanup.unlink(missing_ok=True)

    print(
        f"Hotovo. Preložené {translated}/{total} blokov titulkov do {SUPPORTED_TARGETS[target]}.",
        flush=True,
    )
    print(f"Výstup uložený: {output_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
