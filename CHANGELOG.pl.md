# Historia zmian

Wszystkie istotne zmiany w projekcie są opisane w tym pliku.

Format oparty na [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/),
wersjonowanie zgodne z [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Wydania powstają automatycznie: wypchnięcie tagu, np. `v0.1.0`, uruchamia
workflow wydania, który publikuje opis z sekcji "What's New", "Fixed" i
"Changed" angielskiego pliku `CHANGELOG.md` (to on trafia do GitHub Releases).

## [Unreleased]

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

[Unreleased]: https://github.com/brodatech-lab/ai-sys-buddy/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/brodatech-lab/ai-sys-buddy/releases/tag/v0.1.0
