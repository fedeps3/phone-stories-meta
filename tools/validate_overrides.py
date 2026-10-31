#!/usr/bin/env python3
"""validate_overrides.py — valida overrides.json ANTES de que salga a producción.

El juego baja `overrides.json` del repo meta al arrancar y aplica flags y nodos
temporales. Un error acá se propaga a todas las instalaciones sin build de por
medio, así que se valida localmente primero.

    python3 tools/validate_overrides.py [--file overrides.json] [--game /ruta/al/juego]

Qué verifica:
  - estructura y tipos (schema, revision, game_version, disabled)
  - que cada action exista en el vocabulario real del juego
  - que cada target EXISTA en la data (board, thread, app, asset, post...)
  - que cada insert apunte a una cápsula y a un nodo que existen
  - que el id del nodo insertado no choque con uno ya existente
  - AVISA si el override no hace nada (ej: desbloquear un board que ya está abierto)

Sale con 1 si hay errores. Los avisos no rompen el build pero se leen.
"""
import argparse
import glob
import json
import os
import sys

# Vocabulario permitido en overrides: los eventos que DialogueManager._apply_effects
# resuelve vía trigger_event. unlock_gallery queda AFUERA a propósito: lo ejecuta
# code_manager.gd (camino de los códigos), no el dispatcher de diálogo, y sumarlo
# obligaría a un segundo camino de aplicación en el cliente.
ACTIONS = {
    "unlock_forum_board", "unlock_forum", "unlock_social",
    "unlock_social_story", "unlock_social_post", "unlock_app",
}
# Prefijos válidos para raw_flags: exactamente PROGRESSION_PREFIXES de
# game_state.gd:54 (sin el ':' final). Quedan afuera a propósito:
#   - forum_following (no usa la forma "prefijo:valor")
#   - gallery_* (van por la ruta persistente de galería, no por variables)
#   - expired, phone_was_unlocked, portal_start_node (no son progresión)
FLAG_PREFIXES = {
    "email_unlocked", "email_replied", "email_read", "email_saved",
    "app_unlocked", "dialogue_unlocked",
    "social_unlocked", "social_post_unlocked", "social_story_unlocked",
    "social_replied", "social_override",
    "forum_unlocked", "forum_board_unlocked", "forum_post_notified",
    "forum_link_clicked", "forum_replied",
    "spy_unlocked", "spy_archived", "relation_unlocked", "relation_bar_defs",
    "vn_watched", "timeline", "echado", "bloqueado",
}

errores, avisos = [], []


def err(m):
    errores.append(m)


def warn(m):
    avisos.append(m)


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


class Game:
    def __init__(self, root, tier="free"):
        self.root, self.tier = root, tier
        cfg = os.path.join(root, "data", tier, "config", "home_apps.json")
        self.apps = set()
        if os.path.isfile(cfg):
            d = load(cfg)
            lst = d if isinstance(d, list) else d.get("apps", [])
            self.apps = {a.get("id") for a in lst if isinstance(a, dict)}
        self.assets = set()
        mf = os.path.join(root, "data", tier, "config", "asset_manifest.json")
        if os.path.isfile(mf):
            d = load(mf)
            items = d.get("assets", d)
            if isinstance(items, dict):
                self.assets = set(items.keys())
            else:
                self.assets = {a.get("id") for a in items if isinstance(a, dict)}

    def has_pov(self, pov):
        return bool(pov) and os.path.isdir(self.pov_dir(pov))

    def pov_dir(self, pov):
        return os.path.join(self.root, "data", self.tier, "stories", pov)

    def boards(self, pov):
        """{board_id: locked}"""
        out = {}
        pat = os.path.join(self.root, "data", self.tier, "povs", pov, "forums", "boards", "*", "board.json")
        for f in glob.glob(pat):
            try:
                d = load(f)
            except Exception:
                continue
            out[d.get("id")] = bool(d.get("locked"))
        return out

    def threads(self, pov):
        out = set()
        pat = os.path.join(self.root, "data", self.tier, "povs", pov, "forums", "boards", "*", "board.json")
        for f in glob.glob(pat):
            try:
                d = load(f)
            except Exception:
                continue
            for t in d.get("threads", []) or []:
                out.add(t)
        return out

    def id_index(self, pov):
        """Todos los ids de la data del POV: red de seguridad para targets que no
        modelamos con precisión (social/stories/posts)."""
        ids = set()
        for f in glob.glob(os.path.join(self.root, "data", self.tier, "povs", pov, "**", "*.json"),
                           recursive=True):
            try:
                d = load(f)
            except Exception:
                continue
            stack = [d]
            while stack:
                o = stack.pop()
                if isinstance(o, dict):
                    if isinstance(o.get("id"), str):
                        ids.add(o["id"])
                    stack.extend(o.values())
                elif isinstance(o, list):
                    stack.extend(o)
        return ids

    def capsule(self, pov, chat, capsule):
        return os.path.join(self.pov_dir(pov), chat, "capsules", capsule + ".json")


def check_action(a, t, where, game, pov):
    """Valida un par (action, target) contra la data real."""
    if a not in ACTIONS:
        err(f"{where}: action '{a}' no existe. Válidas: {', '.join(sorted(ACTIONS))}")
        return
    if not isinstance(t, str) or not t.strip():
        err(f"{where}: target vacío")
        return
    t = t.split(":", 1)[1] if t.startswith("asset:") else t

    if a == "unlock_forum_board":
        b = game.boards(pov)
        if t not in b:
            err(f"{where}: el board '{t}' no existe en el POV '{pov}'")
        elif not b[t]:
            warn(f"{where}: el board '{t}' YA está desbloqueado por defecto — este override no hace nada")
    elif a == "unlock_forum":
        if t not in game.threads(pov):
            err(f"{where}: el thread '{t}' no existe en el POV '{pov}'")
    elif a == "unlock_app":
        if t not in game.apps:
            err(f"{where}: la app '{t}' no existe en home_apps.json")
    else:
        if t not in game.id_index(pov):
            warn(f"{where}: no encontré '{t}' en la data del POV '{pov}' (no pude verificar: {a})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "overrides.json"))
    ap.add_argument("--game", default=os.path.expanduser(
        "~/Proyectos/PhoneStories/Juegos/MyPhoneStories"))
    ap.add_argument("--tier", default="free")
    a = ap.parse_args()

    if not os.path.isfile(a.file):
        sys.exit(f"no existe {a.file}")
    if not os.path.isdir(a.game):
        sys.exit(f"no existe el repo del juego: {a.game} (usá --game)")
    try:
        d = load(a.file)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: JSON inválido en {a.file}: {e}")

    game = Game(a.game, a.tier)
    for k in ("schema", "revision", "game_version", "disabled"):
        if k not in d:
            err(f"falta la clave obligatoria '{k}'")
    if d.get("schema") != 1:
        err(f"schema debe ser 1 (es {d.get('schema')!r})")
    if not isinstance(d.get("revision"), int):
        err("revision debe ser entero")
    if not isinstance(d.get("game_version"), str) or not d.get("game_version"):
        err("game_version debe ser un string tipo '0.6.0'")
    if not isinstance(d.get("disabled"), bool):
        err("disabled debe ser true/false")

    flags = d.get("flags", [])
    if not isinstance(flags, list):
        err("flags debe ser una lista de {pov, action, target}")
        flags = []
    for i, f in enumerate(flags):
        if not isinstance(f, dict) or "action" not in f or "target" not in f:
            err(f"flags[{i}]: se espera {{pov, action, target}}")
            continue
        pov = f.get("pov")
        if not pov:
            err(f"flags[{i}]: falta 'pov' (las variables se guardan por protagonista)")
            continue
        if not game.has_pov(pov):
            err(f"flags[{i}]: el POV '{pov}' no existe en la data")
            continue
        check_action(f["action"], f["target"], f"flags[{i}]", game, pov)

    raw = d.get("raw_flags", [])
    if raw and not isinstance(raw, list):
        err("raw_flags debe ser una lista de {pov, flag, value} (un dict no puede llevar pov)")
        raw = []
    for i, r in enumerate(raw):
        if not isinstance(r, dict) or "flag" not in r or "pov" not in r:
            err(f"raw_flags[{i}]: se espera {{pov, flag, value}}")
            continue
        if not game.has_pov(r["pov"]):
            err(f"raw_flags[{i}]: el POV '{r['pov']}' no existe en la data")
        pre = str(r["flag"]).split(":", 1)[0]
        if pre not in FLAG_PREFIXES:
            err(f"raw_flags[{i}]: prefijo '{pre}' desconocido. Válidos: {', '.join(sorted(FLAG_PREFIXES))}")
        if not isinstance(r.get("value"), bool):
            err(f"raw_flags[{i}]: 'value' debe ser true/false")

    inserts = d.get("inserts", [])
    if not isinstance(inserts, list):
        err("inserts debe ser una lista")
        inserts = []
    ids = set()
    for i, ins in enumerate(inserts):
        where = f"inserts[{i}]"
        if "before" in ins:
            err(f"{where}: 'before' está obsoleto; usá \"at\": \"entry\" o \"after\": \"<id>\"")
        for k in ("id", "pov", "chat", "capsule"):
            if k not in ins:
                err(f"{where}: falta '{k}'")
        anchor = "at" if "at" in ins else ("after" if "after" in ins else None)
        if anchor is None:
            err(f"{where}: falta \"at\": \"entry\" o \"after\": \"<id>\"")
        elif "at" in ins and "after" in ins:
            err(f"{where}: 'at' y 'after' son excluyentes")
        elif anchor == "at" and ins.get("at") != "entry":
            err(f"{where}: 'at' sólo acepta \"entry\"")
        if not all(k in ins for k in ("id", "pov", "chat", "capsule")) or anchor is None:
            continue
        if ins["id"] in ids:
            err(f"{where}: id '{ins['id']}' repetido")
        ids.add(ins["id"])
        path = game.capsule(ins["pov"], ins["chat"], ins["capsule"])
        if not os.path.isfile(path):
            err(f"{where}: no existe la cápsula {ins['pov']}/{ins['chat']}/{ins['capsule']}")
            continue
        cap = load(path)
        lista = cap.get("nodos", [])
        nodos = {n.get("id") for n in lista}
        if anchor == "after":
            ref = ins.get("after")
            if ref not in nodos:
                err(f"{where}: el nodo '{ref}' no existe en {ins['capsule']}")
            else:
                n = next(x for x in lista if x.get("id") == ref)
                if not n.get("sigue"):
                    err(f"{where}: '{ref}' no tiene 'sigue' simple (es end o usa opciones/casos/sino)")
                for k in ("opciones", "casos", "sino"):
                    if n.get(k):
                        err(f"{where}: '{ref}' tiene '{k}'; insertar después cambiaría más de una arista")
        if ins["id"] in nodos:
            err(f"{where}: el id '{ins['id']}' ya existe en {ins['capsule']}")
        if "action" in ins:
            check_action(ins["action"], ins["target"], where, game, ins["pov"])

    print(f"{os.path.basename(a.file)} — schema {d.get('schema')}, rev {d.get('revision')}, "
          f"game_version {d.get('game_version')}, disabled={d.get('disabled')}")
    print(f"  flags: {len(flags)} · raw_flags: {len(raw or {})} · inserts: {len(inserts)}")
    for e in errores:
        print(f"  ERROR {e}")
    for w in avisos:
        print(f"  aviso {w}")
    print(f"\n{len(errores)} error(es), {len(avisos)} aviso(s).")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
