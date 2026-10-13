# itch.io — página de My Phone Stories

Página: <https://mittian.itch.io/my-phone-stories>

| Archivo | Qué es |
|---|---|
| `custom.css` | El CSS entero. Se pega tal cual en el editor de CSS de itch. |
| `README.md` | Este doc: cómo activarlo, qué cambia y qué conviene arreglar del contenido. |

Verificado contra un banco local (réplica de tu página con el CSS real de itch
`game.css`), renderizado con Chromium headless:

- sin scroll horizontal en 1280 / 768 / 500 px de ancho;
- 0 elementos que el CSS esconda o saque de la columna;
- contrastes medidos: texto 14.6:1, botones 8.4:1 (texto oscuro sobre naranja),
  chips 12.2:1, metadatos chicos ≥5.3:1 (AA para texto chico);
- gate de edad: caja 550×359, texto 14.6:1, botón 8.4:1.

---

## 1. itch NO tiene el CSS abierto: hay que pedir acceso

El CSS custom en itch se habilita **por cuenta** y lo aprueba el staff. Sin eso,
el editor de CSS no aparece. Los requisitos que piden (de la guía oficial):
decir qué cambios querés, que no se pueda hacer con el editor de temas, que la
página siga siendo accesible, y **no tocar la UI propia de itch** (todo lo mío
cuelga de `#wrapper`, así que cumple).

Mensaje listo para mandar a <https://itch.io/support> (en inglés, que es como
lo lee el staff):

> **Subject:** Custom CSS access for my project page (My Phone Stories)
>
> Hi! I'd like to request CSS editor access for my account `mittian`, to style my
> project page <https://mittian.itch.io/my-phone-stories>.
>
> The theme editor covers my colors and banner, but not what I need:
>
> 1. My build screenshots are dark phone-UI captures. I'd like the page column to
>    read as one dark rounded card (border + soft shadow) so they sit on a
>    background that matches the game instead of a flat, lighter panel.
> 2. A short gradient at the bottom of the banner so it fades into the column
>    instead of ending on a hard cut.
> 3. The download rows and the "More information" metadata panel presented as
>    cards, with the tags shown as chips, and a consistent type scale for the
>    section headers in the description.
> 4. Accessibility fix: itch's default paints my orange buttons with white text
>    (~2.5:1). I'm setting dark text on the orange (~8.4:1) and keeping focus
>    outlines visible at all times.
>
> All my rules are scoped inside `#wrapper`; I don't alter itch.io's own UI, and I
> use no JavaScript and no third-party fonts (the theme font stays). I've read the
> CSS guide, kept a `prefers-reduced-motion` block, and checked the page logged
> out and at mobile widths.
>
> Thanks!

## 2. Cómo se pega

1. Con el acceso ya habilitado: abrí tu página → **Edit theme**.
2. Buscá la sección **CSS** (aparece sólo cuando el acceso está activo).
3. Pegá **todo** `custom.css` y guardá.
4. Hard refresh (Ctrl+Shift+R). El CSS custom va **después** del tema, así que
   pisa al editor de temas sin `!important`.

Opcional pero recomendado, para que el chrome de itch (la barra de arriba)
acompañe: en el **editor de temas**, poné el color **BG** en `#0d0d0f`. Eso es
lo único que el CSS no puede tocar sin romper la UI del sitio.

---

## 3. Qué cambia

- **Fondo y columna**: página casi negra con un patrón de puntos apenas visible,
  columna como tarjeta oscura redondeada con sombra. Antes: naranja plano + panel
  violeta grisáceo, que peleaba con los screenshots (que son negros).
- **Banner**: fundido en degradé hacia la columna, esquinas redondeadas arriba.
- **Botones**: píldoras; el CTA del encabezado grande con halo naranja. **Texto
  oscuro sobre naranja** (`#140f06` sobre `#fb922b` = 8.4:1 contra los ~2.5:1 del
  blanco que pone itch).
- **Descarga**: cada archivo es una tarjeta con borde, hover y botón naranja.
- **Ficha técnica**: etiquetas en mayúsculas + **todos los links como chips**
  (Plataformas, Género, Tags, Idiomas… son todos tags de itch, así que quedan
  parejos).
- **Títulos de sección** (DOWNLOAD, DEVELOPMENT LOG, COMMENTS): mayúsculas con
  espaciado y una barrita amarilla→naranja a la izquierda.
- **Devlog**: lista con separadores finos y fecha a la derecha, hover por fila.
- **Comentarios**: burbujas redondeadas (pegan con el chat del juego).
- **Gate de edad**: caja oscura centrada, selects y botón integrados.
- **Mobile**: paddings y tipografías reducidos; la tira de capturas (que en itch
  es un carrusel horizontal) suma aire entre imágenes y anclaje al deslizar.
- **Accesibilidad**: foco visible siempre, contraste mínimo AA en todo el texto
  (incluidos los metadatos chicos), y `prefers-reduced-motion`.

## 4. Perillas

Todo sale del bloque **1. Tokens** en `custom.css`. Cambiar el accent de toda la
página es una línea:

```css
--ps-orange: #fb922b;   /* accent: botones, links, chips activos */
--ps-yellow: #e8c547;   /* placa "My Phone" del logo: detalles chicos */
--ps-bg:     #0d0d0f;   /* fondo de página */
--ps-surface:#16161c;   /* la columna */
--ps-card:   #1e1e26;   /* tarjetas (descargas, chips, comentarios) */
```

Si querés la paleta más "cálida bar" (marrón del banner) en vez de fría:
`--ps-bg: #14100d`, `--ps-surface: #1c1714`, `--ps-card: #241d18`. La tipografía
sale del tema (hoy Lato); si la cambiás en el editor de temas, el CSS la sigue
sola.

---

## 5. Opcional: 3 bloques de HTML en la descripción (lo que más cambia el look)

El CSS no puede tocar el **texto** de la descripción (no hay selector por
contenido), y hoy:

- **"Features"** es un párrafo más → no se lee como subtítulo;
- las features son párrafos que empiezan con `- ` → no son una lista;
- el final son **4 PNG promocionales** con texto horneado y anchos distintos
  (399 / 558 / 578 / 632 px) → el conjunto se lee como 4 banners sueltos y
  compite con el botón de descarga.

Si querés arreglarlo, se pega en **Edit game → Description → botón `<>` (HTML)**.
Ojo: una vez que editás en HTML, seguí editando en HTML (el editor visual
reescribe el markup). Las clases **tienen** que empezar con `custom-`; itch borra
las demás.

```html
<div class="custom-platforms">
  <b>Available on</b><span>Windows</span><span>Linux</span><span>Android</span>
</div>

<div class="custom-features">
  <div class="custom-feature"><b>Choices that matter</b>Branching dialogue that leads to different outcomes and scenes.</div>
  <div class="custom-feature"><b>Gallery</b>Unlock illustrations as the story advances.</div>
  <div class="custom-feature"><b>Vainly</b>A social media app with stories, profiles and posts, all part of Alice's world.</div>
  <div class="custom-feature"><b>Languages</b>English &middot; Espa&ntilde;ol &middot; Portugu&ecirc;s.</div>
</div>

<div class="custom-note">
  The game is growing fast. <b>v0.3.1</b> is the free build — <b>v0.4.0</b> is out now for supporters on Patreon.
</div>

<div class="custom-cta">
  <a href="https://x.com/Mittian_dev">Follow on X</a>
  <a class="custom-cta-primary" href="https://www.patreon.com/c/Mittian">Subscribe on Patreon</a>
</div>
```

Y se borran del cuerpo las 4 imágenes (`AVAILABLE IN` / `FOLLOW DEVELOPMENT` /
`FOLLOW ON X` / `SUBSCRIBE TO PATREON`). Probado con el banco local: los chips
quedan parejos, las features van en grilla 2×2 en escritorio y 1 columna en
mobile, y el CTA de Patreon queda **secundario** (borde naranja, sin bloque
naranja lleno) para no competir con *Download*. Ventaja de fondo: el texto pasa a
ser texto — se traduce, se edita sin re-exportar y no se pixela.

---

## 6. Lo que vi en la página y NO es CSS (contenido)

Por orden de impacto:

1. **La versión del banner está vieja.** El banner dice **V0.3.0**, la descarga
   pública es **v0.3.1** y el devlog anuncia **v0.4.0** para Patreon. El
   visitante tiene que reconstruir qué es gratis y qué es early access. Dos
   movimientos: re-exportar el banner con la versión de la build pública, y/o
   dejar la línea de versiones en la descripción (el bloque `custom-note` de
   arriba). Si el banner lleva versión, se re-exporta en cada release — el logo
   solo no debería llevarla.
2. **Los 4 PNG promocionales del final**: anchos distintos (399/558/578/632) y
   texto horneado. O se re-exportan todos al mismo ancho, o se reemplazan por el
   bloque de la sección 5 (mejor).
3. **Idiomas**: la descripción promete *Portugues*, pero el campo **Languages**
   de itch lista sólo English + Spanish (C). Falta **Portuguese** (`lang-pt`).
   El que filtra por portugués no encuentra el juego.
4. **Nombres de los archivos**: las filas muestran
   `PhoneStories_v0.3.1_Android.apk`, etc. Renombrá cada upload a algo como
   `Android (APK)` / `Windows (EXE)` / `Linux (x86_64)` desde
   **Edit game → Uploads**: la plataforma es lo que el visitante busca, el
   nombre técnico no. (El tamaño y la versión ya se ven aparte.)
5. **Tags**: tenés 7 (adult, anime, dating-sim, meaningful-choices,
   multiple-endings, nsfw, romance) y hay 10 slots. `phone-simulation` existe
   como tag de itch (200 OK) y es exactamente lo que es tu juego — no está
   puesto. (El tema NTR no va en tags de itch: no es tag canónico, va en la
   descripción.)
6. **"Vainly"** está bien escrito: es el nombre de la app in-game (aparece así
   en `data/`). No lo toques.
