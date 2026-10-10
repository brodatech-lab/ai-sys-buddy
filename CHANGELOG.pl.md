# Historia zmian

Wszystkie istotne zmiany w projekcie są opisane w tym pliku.

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/),
wersjonowanie zgodne z [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Wydania powstają automatycznie: wypchnięcie tagu, np. `v0.1.1`, uruchamia
workflow wydania, który publikuje opis z sekcji "What's New", "Fixed" i
"Changed" angielskiego pliku `CHANGELOG.md` (to on trafia do GitHub Releases).

## [Unreleased]

## [0.1.2] - 2026-10-10

### What's New
- Instalator dla Windows `install.ps1`: instaluje `ai-sys-buddy.exe`, tworzy
  komendę `ai`, dodaje ją do PATH użytkownika i konfiguruje adres Ollamy oraz
  model. Instalator jest też dołączany do każdego wydania.

### Fixed
- Plik konfiguracji jest teraz czytany z tolerancją na BOM UTF-8, dzięki czemu
  configi zapisane/edytowane przez narzędzia Windows są akceptowane.

### Changed
- Na razie brak.

## [0.1.1] - 2026-10-10

### What's New
- Panel ustawień pozwala podejrzeć i wyładować aktualnie załadowane modele, a
  przy zmianie modelu proponuje zwolnienie poprzedniego, aby nigdy nie trzymać
  dwóch naraz.
- Rozumowanie można przełączać: flaga `--think` w wierszu poleceń lub
  przełącznik „Reasoning (think)" w ustawieniach.

### Fixed
- Modele myślące (np. Qwen3) odpowiadają teraz od razu: rozumowanie jest
  domyślnie wyłączone flagą Ollamy `think`, więc model nie „wisi" przed
  odpowiedzią.
- Modele myślące (np. Qwen3) nie „wiszą" już: tokeny rozumowania wysyłane w
  `message.thinking` są teraz strumieniowane (przygaszone) zamiast ignorowane.

### Changed
- `--config` jest teraz respektowany przy zapisie, a otwarcie ustawień nie
  zjada już wejścia z potoku.
- Binarki wydania nazywają się teraz `ai-sys-buddy` (Linux) oraz
  `ai-sys-buddy.exe` (Windows).

## [0.1.0] - 2026-10-10

### What's New
- Pierwsze publiczne wydanie `ai-sys-buddy`, terminalowego kumpla-sysadmina
  działającego wyłącznie w trybie odczytu.
- Wykrywanie systemu (Linux i Windows) z podpowiedziami zależnymi od platformy.
- Tryb diagnostyczny: `ai "<pytanie>"`.
- Tryb encyklopedii dla komend: `ai ?chmod`.
- Obsługa potoków i sudo, np. `sudo journalctl -u pveproxy -n 50 | ai "co tu się dzieje?"`.
- Tryb interaktywny z krótkoterminową pamięcią rozmowy (bufor FIFO).
- Profiler w trybie `-v`: czas ładowania, liczba tokenów i tokeny na sekundę.
- Menu ustawień obsługiwane strzałkami (questionary) oraz awaryjny backend
  `standard` bez żadnych zależności.

### Fixed
- Nieblokujące wykrywanie stdin, dzięki czemu narzędzie nie zawiesza się na
  otwartym, pustym potoku.

### Changed
- Na razie brak.

[Unreleased]: https://github.com/brodatech-lab/ai-sys-buddy/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/brodatech-lab/ai-sys-buddy/releases/tag/v0.1.2
[0.1.1]: https://github.com/brodatech-lab/ai-sys-buddy/releases/tag/v0.1.1
[0.1.0]: https://github.com/brodatech-lab/ai-sys-buddy/releases/tag/v0.1.0
