# SRT/MKV EN -> SK/CZ Prekladač

Jednoduchý lokálny Python CLI nástroj, ktorý:

- prekladá anglické `.srt` titulky do slovenčiny (`sk`) alebo češtiny (`cz`) pri zachovaní časovania a štruktúry `.srt`
- vie extrahovať subtitle stream z `.mkv` do `.srt` (cez `ffmpeg`)
- vie spraviť aj celý flow: `.mkv` -> extrakcia titulkov -> preklad do `sk`/`cz`

## Funkcie

- Vstup: anglické `.srt`
- Vstup: `.srt` alebo `.mkv`
- Výstup: slovenské alebo české `.srt`
- Zachová číslovanie, časové značky a štruktúru blokov titulkov
- Interaktívny výber jazyka (`sk` / `cz`) alebo parameter v CLI
- Výpis subtitle streamov z MKV a výber streamu na extrakciu
- Režim iba extrakcia (`.mkv` -> `.srt`) bez prekladu
- Lokálne spustenie na tvojom počítači

## Požiadavky

- Python 3.10+ (testované na Python 3.13)
- Internetové pripojenie pre prekladové požiadavky
- FFmpeg (musí obsahovať `ffmpeg` a `ffprobe` v `PATH`) pre prácu s `.mkv`

### Inštalácia FFmpeg (Windows)

Možnosť A - winget:

```powershell
winget install Gyan.FFmpeg
```

Možnosť B - chocolatey:

```powershell
choco install ffmpeg
```

Po inštalácii si over:

```powershell
ffmpeg -version
ffprobe -version
```

## Inštalácia

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

## Použitie

### Najjednoduchší spôsob vo Windows (dvojklik)

Spusti `run_translator.bat`.

Čo urobí automaticky:

- vytvorí `.venv`, ak neexistuje
- nainštaluje/aktualizuje závislosti z `requirements.txt`
- vypýta si vstupný `.srt` alebo `.mkv` súbor
- vypýta si režim (preklad alebo iba extrakcia)
- pri preklade vypýta cieľový jazyk (`sk` alebo `cz`)
- spustí preklad alebo extrakciu

### Interaktívny výber cieľového jazyka

```bash
python srt_translate.py input_en.srt
```

Skript sa opýta, či chceš `sk` alebo `cz`.

### Neinteraktívny výber cieľového jazyka

```bash
python srt_translate.py input_en.srt --target sk
python srt_translate.py input_en.srt --target cz
```

### Preklad priamo z MKV

```bash
python srt_translate.py movie.mkv --target sk
```

Skript vypíše subtitle streamy a nechá ťa vybrať stream na extrakciu.

### Výpis subtitle streamov v MKV

```bash
python srt_translate.py movie.mkv --list-subtitle-streams
```

### Výber konkrétneho subtitle streamu

```bash
python srt_translate.py movie.mkv --target cz --subtitle-stream 2
```

`--subtitle-stream` používa index streamu z `ffprobe` výpisu.

### Iba extrakcia z MKV do SRT (bez prekladu)

```bash
python srt_translate.py movie.mkv --extract-only
```

### Vlastný názov výstupného súboru

```bash
python srt_translate.py input_en.srt --target sk --output output_sk.srt
python srt_translate.py movie.mkv --extract-only --output movie.extracted.srt
```

### Nastavenie veľkosti batchu (voliteľné)

```bash
python srt_translate.py input_en.srt --target cz --batch-size 40
```

## Poznámky

- Výstup sa ukladá ako UTF-8 s BOM (`utf-8-sig`) kvôli dobrej kompatibilite.
- Predvolený názov výstupu je `<input_stem>.<target>.srt`.
- Pri `--extract-only` je predvolený názov výstupu `<input_stem>.extracted.srt`.
- Nástroj prekladá iba text titulkov, nie časovanie ani indexy.
- Extrakcia do `.srt` funguje pre textové subtitle streamy. Obrazové streamy (napr. PGS/VobSub) bez OCR nie je možné priamo previesť do textového `.srt`.

## Licencia

Tento projekt je licencovaný pod MIT licenciou. Plné znenie je v súbore `LICENSE`.

Stručne:

- môžeš to používať osobne aj komerčne
- môžeš to upravovať a ďalej šíriť
- môžeš s tým robiť, čo chceš, v rámci MIT podmienok
- je to poskytované "AS IS", teda bez záruky