#!/usr/bin/env python3
"""Preklad EN .srt titulkov do slovenčiny alebo češtiny pri zachovaní .srt formátu."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

import pysrt
from deep_translator import GoogleTranslator

NL_TOKEN = "__SRT_NEWLINE_TOKEN__"
SUPPORTED_TARGETS = {"sk": "slovenčiny", "cz": "češtiny"}
ENCODING_CANDIDATES = ("utf-8-sig", "utf-8", "cp1250", "latin-1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preklad EN .srt titulkov do slovenčiny (sk) alebo češtiny (cz)."
    )
    parser.add_argument("input", type=Path, help="Cesta k vstupnému EN .srt súboru")
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
    if not input_path.exists() or input_path.suffix.lower() != ".srt":
        print("Chyba: vstup musí byť existujúci .srt súbor.", file=sys.stderr)
        return 1

    target = args.target or choose_target_interactively()
    output_path = resolve_output_path(input_path, target, args.output)

    if args.batch_size < 1:
        print("Chyba: --batch-size musí byť >= 1", file=sys.stderr)
        return 1

    try:
        subs = load_srt(input_path)
        translated, total = translate_subtitles(subs, target, args.batch_size)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        subs.save(str(output_path), encoding="utf-8-sig")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Preklad zlyhal: {exc}", file=sys.stderr)
        return 1

    print(
        f"Hotovo. Preložené {translated}/{total} blokov titulkov do {SUPPORTED_TARGETS[target]}.",
        flush=True,
    )
    print(f"Výstup uložený: {output_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
