# phone-stories-meta — versión remota del juego

> Repo público que alimenta el **update checker in-game** de Phone Stories.
> Clon local: `~/Proyectos/PhoneStories/Herramientas/phone-stories-meta` (SSH alias github-work).
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

---

# overrides.json — parches remotos sin build

> El juego lo baja al arrancar, del mismo host que `version`. Sirve para arreglar
> cosas que ya están en la calle sin sacar una versión nueva.
> **El cliente vive en el repo del juego** (`override_system.gd`); acá vive sólo el archivo.

## Contrato

```json
{
  "schema": 1,
  "revision": 2,
  "game_version": "0.6.0",
  "disabled": false,
  "flags": [ { "pov": "alice", "action": "unlock_forum_board", "target": "nsfw" } ],
  "raw_flags": [ { "pov": "alice", "flag": "forum_board_unlocked:nsfw", "value": true } ],
  "inserts": [ { "id": "ov_001", "pov": "alice", "chat": "alice", "capsule": "cap6",
                 "at": "entry", "action": "unlock_forum_board", "target": "nsfw" } ]
}
```

| campo | qué hace |
|---|---|
| `schema` | siempre `1`. Si el cliente no lo entiende, descarta el archivo entero. |
| `revision` | subilo en cada cambio. Sirve para cachear y para auditar qué se aplicó. |
| `game_version` | versión EXACTA para la que se escribió. Si no coincide, no se aplica nada. |
| `disabled` | `true` apaga todo sin borrar el archivo. Es el kill switch. |
| `flags` | efectos a aplicar. Cada entrada lleva `pov` obligatorio: las variables se guardan por protagonista y los ids de board se repiten entre POVs (`nsfw` existe en alice, rae y cherry). |
| `raw_flags` | escape hatch para variables sin efecto asociado. Lista de `{pov, flag, value}` — un dict no puede llevar `pov`. Prefijo validado contra `PROGRESSION_PREFIXES`. |
| `inserts` | mete UN nodo efecto. Anclaje: `"at": "entry"` (queda primero) o `"after": "<id>"` (sólo si ese nodo tiene un `sigue` simple). Nada de `before`: recablear varios predecesores cambia el flujo en lugares que nadie miró. |

## Acciones permitidas

`unlock_forum_board`, `unlock_forum`, `unlock_social`, `unlock_social_story`,
`unlock_social_post`, `unlock_app`.

Todas las resuelve `DialogueManager._apply_effects` vía `trigger_event`. **`unlock_gallery`
queda afuera a propósito**: la ejecuta `code_manager.gd` (camino de los códigos), no el
dispatcher de diálogo, y sumarla obligaría a un segundo camino de aplicación en el cliente.
Se puede agregar más adelante sin romper nada, porque el archivo está pineado a `game_version`.

## Cuándo se aplican

`set_variable` no hace nada si no hay protagonista activo (`game_state.gd:427`), así que
**no se puede aplicar "al arrancar"**. Cada entrada se aplica cuando su `pov` es el
protagonista activo, y se re-aplica cada vez que se vuelve a ese POV. Nunca toca otro POV.

Los `flags` pasan por el handler real (el mismo que los efectos del juego), así que quedan
escritos en el save y `disabled: true` sólo frena las aplicaciones siguientes — no deshace
lo ya escrito. Sólo `raw_flags` es overlay de lectura y se apaga de verdad.

## Invariantes del cliente (no negociables)

1. **Version pin**: `game_version` distinto → no se aplica nada. Es también lo que permite
   agregar acciones nuevas más adelante sin romper builds viejos.
2. **Todo o nada**: se valida el archivo completo antes de tocar el juego. Nunca aplicación parcial.
3. **Idempotente**: un insert cuyo `id` ya existe se saltea.
4. **Silencioso**: 404, timeout o JSON roto → el juego arranca normal, sin cartel.
5. **Log**: se registra en consola y en `user://` qué se aplicó, con ids.

## Antes de pushear

```bash
cd ~/Proyectos/PhoneStories/Herramientas/phone-stories-meta
python3 tools/validate_overrides.py --game ~/Proyectos/PhoneStories/Juegos/MyPhoneStories
```

Verifica que cada `action` exista, que cada `target` esté en la data, que la cápsula y
el nodo `before` existan, y que el id insertado no choque. Sale con 1 si hay errores.
Además **avisa si el override no hace nada** (ej: destrabar un board que ya viene
abierto) — así no se repite el caso del board de Rae, donde el "fix" era decorativo.
