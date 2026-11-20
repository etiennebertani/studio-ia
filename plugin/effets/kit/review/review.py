#!/usr/bin/env python3
"""Review détaillée: the creator watches the full rendered video and leaves a note on every animation.

    PY KIT/review/review.py <project> [--video <mp4>] [--port 8766] [--keep]

Builds <project>/review/v<N>/ (N = the next version: v1 after the first render, v2 after the next...) with the video,
items.json (every element of edit.py with its time: each effect, each overlay or file of theirs, each card, text box,
thing behind the head, black-and-white beat, colour, the music, the sound effects, the captions, the cuts, the
framing) and retours.json, then serves it at http://127.0.0.1:<port>/ (standard library only).

On the page, per element: J'aime / À changer / À enlever, a note, and files (videos, images, sounds: what they want
instead or as an example). Notes can also be pinned to any second of the video, plus one note on the whole video.
Everything saves by itself as they type (retours.json, files in review/v<N>/pieces/). When they press
"Envoyer à Claude", retours.json gets "sent": true, the server prints RETOURS ENVOYÉS and stops (so an agent that
started it in the background is woken up), unless --keep.

retours.json: {"version": N, "video": "video.mp4", "sent": bool, "sent_at": ISO,
               "items": {"<id>": {"status": "ok"|"change"|"remove"|"", "text": str, "pieces": [file names],
                                  "reply": str}},          # reply: written by the agent once it is applied
               "free": [{"t": seconds, "text": str, "pieces": [...], "reply": str}],
               "global": {"text": str, "pieces": [...], "reply": str}}
The previous version's retours.json (with the agent's replies) is shown on the page under each element.
"""
import datetime
import glob
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import threading

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KIT, "pipeline"))
import common  # noqa: E402

MAX_UPLOAD = 2 * 1024 ** 3


def dur(path):
    try:
        return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                              "csv=p=0", path], text=True).strip())
    except Exception:
        return 0.0


def tm(t, end):
    return end if t == "end" else float(t)


def pretty(s):
    return re.sub(r"[-_]+", " ", str(s)).strip().capitalize()


def items_from(E, end):
    """every element of the edit the creator can comment on, in time order"""
    out = []

    def add(id_, kind, label, a, b, note=""):
        out.append(dict(id=id_, kind=kind, label=label, at=round(tm(a, end), 3), end=round(tm(b, end), 3),
                        note=str(note or "")))

    for f in getattr(E, "FX", []) or []:
        add("fx-" + f["id"], "Effet", pretty(f["id"]), f.get("at", 0), f.get("end", "end"), f.get("note"))
    for k, o in enumerate(getattr(E, "OVERLAYS", []) or []):
        src = str(o.get("src", ""))
        mine = "mes-fichiers" in src
        add("ov-" + re.sub(r"[^a-z0-9]+", "-", os.path.basename(src).lower()).strip("-"),
            "Ton fichier" if mine else ("Vidéo posée" if src.endswith((".mp4", ".mov")) else "Image posée"),
            os.path.basename(src), o.get("at", 0), o.get("end", "end"), o.get("note"))
    for k, c in enumerate(getattr(E, "CARDS", []) or []):
        cid, _, a, b = c[0], c[1], c[2], c[3]
        add(f"card-{cid}", "Carte plein écran", pretty(cid), a, b, c[5] if len(c) > 5 else "")
    for k, x in enumerate(getattr(E, "BOXES", []) or []):
        add(f"box{k}", "Texte à l'écran", str(x.get("text", "")).replace("\n", " "), x.get("at", 0),
            x.get("end", "end"), x.get("note"))
    for k, x in enumerate(getattr(E, "BEHIND", []) or []):
        a = x.get("at", (x.get("items") or [(0,)])[0][0])
        label = x.get("text") or x.get("src") or ", ".join(str(i[1]) for i in x.get("items", [])[:3]) or x.get("kind")
        add(f"behind{k}", "Derrière ta tête", str(label), a, x.get("end", "end"), x.get("note"))
    hook = getattr(E, "HOOK", None)
    if hook:
        add("hook", "Texte du début", " ".join(str(hook.get(k, "")) for k in ("eyebrow", "h1", "h2")).strip(), 0,
            hook.get("shot_end", 3.0))
    for k, (a, b) in enumerate(getattr(E, "BW", []) or []):
        add(f"bw{k}", "Noir et blanc", "Passage en noir et blanc", a, b)
    for k, g in enumerate(getattr(E, "GRADES", []) or []):
        add(f"grade{k}", "Couleur", str(g[2]), g[0], min(tm(g[1], end), end))
    S = getattr(E, "SOUND", {}) or {}
    if S.get("music"):
        secs = S.get("sections") or [dict(at=0.0)]
        add("musique", "Musique", os.path.basename(S["music"]), secs[0].get("at", 0.0), end,
            f"Volume sous la voix : {S.get('bed_db', '?')} dB")
    if S.get("sfx"):
        add("bruitages", "Bruitages", f"{len(S['sfx'])} bruitages", 0, end)
    add("sous-titres", "Sous-titres", "Les sous-titres (police, taille, place, rythme)", 0, end)
    add("coupes", "Coupes", "Les coupes et les blancs (rythme, mots coupés)", 0, end)
    if len(getattr(E, "SHOTS", []) or []) > 1 or (getattr(E, "CAMERA", {}) or {}).get("punch"):
        add("cadrage", "Cadrage", "Les zooms et changements de cadrage", 0, end)
    out.sort(key=lambda i: (i["at"] if i["kind"] not in ("Musique", "Bruitages", "Sous-titres", "Coupes", "Cadrage")
                            else 1e9, i["at"]))
    return out


def latest_render(project):
    vids = [v for v in glob.glob(os.path.join(project, "renders", "*.mp4"))]
    phone = [v for v in vids if v.endswith("-phone.mp4")]
    pool = phone or vids
    if not pool:
        sys.exit(f"no render yet in {project}/renders: render first (SKILL.md step 8)")
    return max(pool, key=os.path.getmtime)


def build(project, video):
    root = os.path.join(project, "review")
    os.makedirs(root, exist_ok=True)
    done = sorted(int(m.group(1)) for d in os.listdir(root) if (m := re.fullmatch(r"v(\d+)", d)))
    # reuse the last version while it hasn't been sent; otherwise start the next one
    if done and not json.load(open(os.path.join(root, f"v{done[-1]}", "retours.json"))).get("sent"):
        n = done[-1]
    else:
        n = (done[-1] + 1) if done else 1
    vdir = os.path.join(root, f"v{n}")
    os.makedirs(os.path.join(vdir, "pieces"), exist_ok=True)
    shutil.copy(video, os.path.join(vdir, "video.mp4"))
    E = common.load_edit(project)
    end = dur(video)
    items = items_from(E, end)
    json.dump(dict(version=n, title=getattr(E, "TITLE", os.path.basename(project)), duration=end,
                   source=os.path.basename(video), items=items), open(os.path.join(vdir, "items.json"), "w"),
              indent=1, ensure_ascii=False)
    rp = os.path.join(vdir, "retours.json")
    if not os.path.exists(rp):
        json.dump(dict(version=n, video="video.mp4", sent=False, items={}, free=[], **{"global": {}}),
                  open(rp, "w"), indent=1, ensure_ascii=False)
    shutil.copy(os.path.join(KIT, "review", "page.html"), os.path.join(root, "index.html"))
    return root, n


def serve(root, n, port, keep):
    vdir = os.path.join(root, f"v{n}")
    rp = os.path.join(vdir, "retours.json")
    lock = threading.Lock()

    class H(http.server.SimpleHTTPRequestHandler):
        extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                          ".html": "text/html; charset=utf-8", ".json": "application/json; charset=utf-8",
                          ".mp4": "video/mp4", ".mov": "video/quicktime"}

        def __init__(self, *a, **kw):
            super().__init__(*a, directory=root, **kw)

        def log_message(self, *a):
            pass

        def end_headers(self):
            self.send_header("Cache-Control", "no-store")
            self.send_header("Accept-Ranges", "bytes")
            super().end_headers()

        def _json(self, code, obj):
            body = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?")[0]
            if path == "/api/state":
                prev = os.path.join(root, f"v{n - 1}", "retours.json")
                prev_items = os.path.join(root, f"v{n - 1}", "items.json")
                return self._json(200, dict(
                    version=n, items=json.load(open(os.path.join(vdir, "items.json"))),
                    retours=json.load(open(rp)),
                    previous=json.load(open(prev)) if os.path.exists(prev) else None,
                    previous_items=json.load(open(prev_items)) if os.path.exists(prev_items) else None))
            rng = self.headers.get("Range")
            full = os.path.join(root, path.lstrip("/"))
            if rng and os.path.isfile(full) and full.startswith(root):     # video seeking needs byte ranges
                size = os.path.getsize(full)
                m = re.match(r"bytes=(\d*)-(\d*)", rng)
                a = int(m.group(1)) if m.group(1) else max(0, size - int(m.group(2)))
                b = int(m.group(2)) if m.group(1) and m.group(2) else size - 1
                b = min(b, size - 1)
                self.send_response(206)
                self.send_header("Content-Type", self.guess_type(full))
                self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
                self.send_header("Content-Length", str(b - a + 1))
                self.end_headers()
                with open(full, "rb") as fh:
                    fh.seek(a)
                    left = b - a + 1
                    while left > 0:
                        chunk = fh.read(min(1 << 20, left))
                        if not chunk:
                            break
                        try:
                            self.wfile.write(chunk)
                        except (BrokenPipeError, ConnectionResetError):
                            return
                        left -= len(chunk)
                return
            return super().do_GET()

        def do_POST(self):
            path = self.path.split("?")[0]
            n_bytes = int(self.headers.get("Content-Length", 0))
            if path == "/api/upload":
                from urllib.parse import parse_qs, urlparse
                qs = parse_qs(urlparse(self.path).query)
                name = os.path.basename(qs.get("name", ["fichier"])[0]) or "fichier"
                name = re.sub(r"[^\w.\- ]+", "_", name)[-80:]
                if n_bytes > MAX_UPLOAD:
                    return self._json(413, {"error": "fichier trop lourd (2 Go max)"})
                stamp = datetime.datetime.now().strftime("%H%M%S")
                dest = os.path.join(vdir, "pieces", f"{stamp}-{name}")
                left = n_bytes
                with open(dest, "wb") as fh:
                    while left > 0:
                        chunk = self.rfile.read(min(1 << 20, left))
                        if not chunk:
                            break
                        fh.write(chunk)
                        left -= len(chunk)
                return self._json(200, {"ok": True, "file": os.path.basename(dest)})
            try:
                body = json.loads(self.rfile.read(min(n_bytes, 4 << 20)) or b"{}")
            except ValueError:
                return self._json(400, {"error": "json"})
            if path == "/api/save":
                with lock:
                    cur = json.load(open(rp))
                    if cur.get("sent"):
                        return self._json(409, {"error": "déjà envoyé"})
                    for k in ("items", "free", "global"):
                        if k in body:
                            cur[k] = body[k]
                    json.dump(cur, open(rp, "w"), indent=1, ensure_ascii=False)
                return self._json(200, {"ok": True})
            if path == "/api/send":
                with lock:
                    cur = json.load(open(rp))
                    cur["sent"] = True
                    cur["sent_at"] = datetime.datetime.now().isoformat(timespec="seconds")
                    json.dump(cur, open(rp, "w"), indent=1, ensure_ascii=False)
                print(f"RETOURS ENVOYÉS {rp}", flush=True)
                self._json(200, {"ok": True})
                if not keep:
                    threading.Timer(1.5, srv.shutdown).start()
                return
            return self._json(404, {"error": "not found"})

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), H)
    print(f"REVIEW v{n}: http://127.0.0.1:{port}/   (retours -> {rp})", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith("-"):
        sys.exit(__doc__)
    project = os.path.abspath(os.path.expanduser(a[0]))
    video = os.path.abspath(os.path.expanduser(a[a.index("--video") + 1])) if "--video" in a else latest_render(project)
    port = int(a[a.index("--port") + 1]) if "--port" in a else 8766
    root, n = build(project, video)
    if "--build-only" in a:
        print(f"REVIEW v{n} built in {root}")
        return
    serve(root, n, port, "--keep" in a)


if __name__ == "__main__":
    main()
