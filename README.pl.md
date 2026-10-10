# ai-sys-buddy

[English](README.md) | **Polski**

Lekki, prywatny asystent terminalowy z przyjazną osobowością **kumpla-sysadmina**.
Łączy się z lokalną lub zdalną instancją [Ollamy](https://ollama.com), pomaga w
diagnostyce, uczy komend i pokazuje metryki wydajności modeli.

> **Domyślnie tylko odczyt.** `ai-sys-buddy` nigdy nie wykonuje komend za Ciebie.
> Model produkuje wyłącznie tekst i formatuje komendy w ramkach; Ty je
> przeglądasz i uruchamiasz ręcznie. Nic nie jest wysyłane poza Twój serwer
> Ollama.

## Funkcje

- **Świadomość systemu** — wykrywa Linux i Windows i dopasowuje podpowiedzi.
- **Tryb diagnostyczny** — `ai "dlaczego dysk jest pełny?"`.
- **Tryb encyklopedii** — `ai ?chmod` to krótki, praktyczny przewodnik.
- **Potoki i sudo** — `sudo journalctl -u pveproxy -n 50 | ai "co tu się dzieje?"`.
- **Tryb interaktywny** — mały REPL z krótkoterminową pamięcią rozmowy.
- **Profiler** — flaga `-v` pokazuje czas ładowania, tokeny i tokeny/sekundę.
- **Menu ustawień** — wybór modelu, URL, osobowości i backendu UI strzałkami.
- **Awaryjny tryb bez zależności** — backend `standard` działa bez `rich`.

## Instalacja

### Gotowe binarki

Pobierz najnowszy `ai-sys-buddy` (Linux) lub `ai-sys-buddy.exe` (Windows) ze
strony [Releases](https://github.com/brodatech-lab/ai-sys-buddy/releases), nadaj
prawa wykonania (Linux) i umieść plik w `PATH`.

```bash
chmod +x ai-sys-buddy
mv ai-sys-buddy ~/.local/bin/ai
```

### Ze źródeł (Python 3.10+)

```bash
git clone https://github.com/brodatech-lab/ai-sys-buddy.git
cd ai-sys-buddy
./install.sh
```

`install.sh` tworzy środowisko wirtualne, instaluje pakiet w trybie edytowalnym
i podlinkowuje komendę `ai` do `~/.local/bin`, dzięki czemu działa z dowolnego
katalogu. Jeśli ten katalog nie jest w `PATH`, skrypt wypisze jedną linię do
dodania.

Wolisz ręcznie? Pakiet udostępnia też skrypt konsolowy:

```bash
python -m venv .venv && source .venv/bin/activate
pip install .
```

## Wymagania

- Działający serwer Ollama (`ollama serve`), domyślnie `http://127.0.0.1:11434`.
- Co najmniej jeden pobrany model, np. `ollama pull llama3.2`. Przy pierwszym
  uruchomieniu narzędzie poprosi o wybór z listy zainstalowanych modeli.

## Użycie

```bash
ai                          # tryb interaktywny
ai "jak sprawdzić użycie dysku na Linuksie?"
ai ?chmod                   # hasło encyklopedii dla chmod
ai s                        # menu ustawień (alias: ai settings)
ai help                     # pomoc
sudo journalctl -u pveproxy -n 50 | ai "co tu się dzieje?"
ai -v "wylistuj otwarte porty"   # tryb verbose z metrykami wydajności
```

### Opcje

| Opcja | Opis |
| --- | --- |
| `-v`, `--verbose` | Pokaż metryki wydajności modelu. |
| `--think` | Włącz rozumowanie modelu (tylko modele myślące). |
| `--model NAME` | Nadpisz model dla tego uruchomienia. |
| `--url URL` | Nadpisz adres Ollamy dla tego uruchomienia. |
| `--backend rich\|standard` | Wybór backendu UI. |
| `--no-color` | Wyłącz kolory. |
| `--config PATH` | Użyj alternatywnego pliku konfiguracji. |
| `--version` | Pokaż wersję i zakończ. |

## Konfiguracja

Przechowywana per użytkownik:

- Linux: `~/.config/ai-sys-buddy/config.json`
- Windows: `%APPDATA%\ai-sys-buddy\config.json`

| Klucz | Domyślnie | Znaczenie |
| --- | --- | --- |
| `ollama_url` | `http://127.0.0.1:11434` | Bazowy adres Ollamy. |
| `model` | _(pusty)_ | Wybrany model; wybierany przy pierwszym starcie. |
| `persona_name` | `ai` | Nazwa kumpla w promptach (może być `buddy`). |
| `ui_backend` | `rich` | `rich` albo `standard`. |
| `history_size` | `4` | Liczba wymian w pamięci rozmowy (FIFO). |
| `verbose_default` | `false` | Zawsze pokazuj metryki. |
| `think` | `false` | Włącz rozumowanie modelu (tylko modele myślące). |
| `telemetry_enabled` | `false` | Zarezerwowane pod przyszłą telemetrię (opt-in). |
| `no_color` | `false` | Wyłącz kolory. |

## Prywatność i bezpieczeństwo

- Brak telemetrii, brak analityki, brak połączeń poza Twój adres Ollamy.
- Narzędzie nie potrafi i nie będzie wykonywać komend. Wszystko jest doradcze.
- Proponowane komendy służą do ręcznego przejrzenia; nigdy nie przekierowuj ich
  bezpośrednio do shella.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install . pyinstaller
python -m unittest discover -s tests
```

### Budowanie samodzielnej binarki

```bash
pyinstaller --onefile --name ai-sys-buddy --clean main.py
```

### Wydania

Wydania są w pełni automatyczne. Wypchnij tag, a GitHub Actions zbuduje binarki
dla Windows i Linuksa oraz utworzy wydanie, korzystając z opisu z angielskiego
[`CHANGELOG.md`](CHANGELOG.md):

```bash
git tag v0.1.0
git push origin v0.1.0
```

Lokalne skrypty pomocnicze znajdują się w nieśledzonym katalogu `scripts/`.

## Licencja

Zobacz plik `LICENSE` dołączony do repozytorium.
