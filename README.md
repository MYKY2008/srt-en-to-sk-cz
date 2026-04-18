# SRT EN -> SK/CZ Prekladač

Jednoduchý lokálny Python CLI nástroj, ktorý prekladá anglické `.srt` titulky do slovenčiny (`sk`) alebo češtiny (`cz`) pri zachovaní časovania a štruktúry `.srt`.

## Funkcie

- Vstup: anglické `.srt`
- Výstup: slovenské alebo české `.srt`
- Zachová číslovanie, časové značky a štruktúru blokov titulkov
- Interaktívny výber jazyka (`sk` / `cz`) alebo parameter v CLI
- Lokálne spustenie na tvojom počítači

## Požiadavky

- Python 3.10+ (testované na Python 3.13)
- Internetové pripojenie pre prekladové požiadavky

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
- vypýta si vstupný EN `.srt` súbor
- vypýta si cieľový jazyk (`sk` alebo `cz`)
- spustí preklad

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

### Vlastný názov výstupného súboru

```bash
python srt_translate.py input_en.srt --target sk --output output_sk.srt
```

### Nastavenie veľkosti batchu (voliteľné)

```bash
python srt_translate.py input_en.srt --target cz --batch-size 40
```

## Poznámky

- Výstup sa ukladá ako UTF-8 s BOM (`utf-8-sig`) kvôli dobrej kompatibilite.
- Predvolený názov výstupu je `<input_stem>.<target>.srt`.
- Nástroj prekladá iba text titulkov, nie časovanie ani indexy.

## Licencia

Tento projekt je licencovaný pod MIT licenciou. Plné znenie je v súbore `LICENSE`.

Stručne:

- môžeš to používať osobne aj komerčne
- môžeš to upravovať a ďalej šíriť
- môžeš s tým robiť, čo chceš, v rámci MIT podmienok
- je to poskytované "AS IS", teda bez záruky
