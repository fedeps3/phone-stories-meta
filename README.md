# phone-stories-meta — versión remota del juego

> Repo público que alimenta el **update checker in-game** de Phone Stories.
> Clon local: `~/Documentos/Godot/phone-stories-meta` (SSH alias github-work).
> El juego lee: `https://raw.githubusercontent.com/fedeps3/phone-stories-meta/main/version`

## Flujo estándar (el agente maneja esto, no Alex)

Alex pasa el changelog en criollo → el agente edita `version`, commitea y pushea.
Commit format: `release: X.Y.Z (public)` o `release: X.Y.Z (early access)`.

### 1. Early access en Patreon (pública no cambia)
```json
"latest_patreon": "<nueva>",   // latest_public NO tocar
"patreon_notes": "<changelog EN>"
```
Efecto: los free reciben notificación EARLY ("available NOW on Patreon").

### 2. Versión pública
```json
"latest_public": "<nueva>",
"public_notes": "<changelog EN>"
```
Si `latest_patreon == latest_public` → la notificación rica sale sin bloque early.
Y aparte: Alex actualiza `application/config/version` en el juego antes de compilar.

### 3. En ambos casos
- Notas SIEMPRE en inglés (público F95). Una línea por bullet, `\n` como separador.
- Invariante: `latest_patreon >= latest_public` JAMÁS al revés.
- No renombrar campos existentes (los viejos builds dependen de ellos).
- Semver "X.Y.Z" — comparación numérica por componente.

## Campos

| Campo | Qué es |
|---|---|
| latest_public | Última versión pública (itch.io) |
| latest_patreon | Última versión early access (Patreon) |
| url_public | https://mittian.itch.io/my-phone-stories |
| url_patreon | https://www.patreon.com/c/Mittian |
| public_notes | Changelog público (EN, \n = bullet) |
| patreon_notes | Changelog/motivación early access (EN) |

Spec completa del checker: `mobile/docs/SPEC_update_checker.md` (repo del juego).
