"""Contrôle d'origine : un contenu fait sans IA générative ne doit porter aucune marque « fait par IA ».

    python3 controle_origine.py <fichier ou dossier> [...]

Cherche, dans chaque fichier (vidéo, image, son), les marques que lisent les plateformes pour afficher « Infos IA » :
manifeste C2PA (Content Credentials), type de source IPTC « trainedAlgorithmicMedia », et la signature des
générateurs connus. Le Studio n'ajoute jamais ces marques ; s'il en trouve une, c'est qu'un élément généré par IA est
entré dans le montage (image, b-roll, musique, voix de synthèse). On ne l'efface jamais : on dit à la personne quel
fichier la porte, pour qu'elle le remplace par un élément authentique ou qu'elle assume l'étiquette.

Affiche {"ok": bool, "marques": [{"fichier", "marque"}]}. Code de sortie 1 si une marque est trouvée.
"""
import json
import sys
from pathlib import Path

EXTENSIONS = {".mp4", ".mov", ".m4v", ".jpg", ".jpeg", ".png", ".webp", ".heic", ".gif", ".mp3", ".wav", ".m4a", ".aac", ".ogg"}
MARQUES = {
    b"c2pa": "manifeste C2PA (Content Credentials)",
    b"jumb": "boîte JUMBF (porte en général un manifeste C2PA)",
    b"trainedAlgorithmicMedia": "IPTC : contenu généré par IA",
    b"compositeWithTrainedAlgorithmicMedia": "IPTC : contenu composé avec de l'IA",
    b"algorithmicMedia": "IPTC : contenu algorithmique",
    b"Made with AI": "mention « Made with AI »",
    b"AI generated": "mention « AI generated »",
}
GENERATEURS = [b"Midjourney", b"DALL-E", b"DALL\xc2\xb7E", b"Stable Diffusion", b"Adobe Firefly", b"Imagen", b"SynthID",
               b"Runway", b"Sora", b"Kling", b"Pika", b"Suno", b"Udio", b"ElevenLabs", b"OpenAI", b"Ideogram", b"Leonardo.Ai"]
def _boites_mp4(data, debut, fin, sortie):
    """MP4/MOV : garde toutes les boîtes sauf les données d'image et de son (mdat), qui ne contiennent pas de métadonnées."""
    i = debut
    while i + 8 <= fin:
        taille = int.from_bytes(data[i:i + 4], "big"); genre = data[i + 4:i + 8]; tete = 8
        if taille == 1 and i + 16 <= fin:
            taille = int.from_bytes(data[i + 8:i + 16], "big"); tete = 16
        elif taille == 0:
            taille = fin - i
        if taille < tete or i + taille > fin:
            break
        if genre in (b"moov", b"trak", b"mdia", b"minf", b"stbl", b"udta", b"meta", b"ilst"):
            sortie.append(data[i:i + tete]); _boites_mp4(data, i + tete + (4 if genre == b"meta" else 0), i + taille, sortie)
        elif genre not in (b"mdat", b"free", b"skip", b"stco", b"co64", b"stsz", b"stts", b"stss", b"ctts", b"stsc", b"sdtp", b"sgpd", b"sbgp"):
            sortie.append(data[i:i + taille])
        i += taille


def _jpeg(data):
    """JPEG : seulement les segments d'en-tête (EXIF, XMP, JUMBF), jusqu'au début de l'image compressée."""
    out, i = [], 2
    while i + 4 <= len(data) and data[i] == 0xFF:
        m = data[i + 1]; n = int.from_bytes(data[i + 2:i + 4], "big")
        if m == 0xDA:
            break
        out.append(data[i:i + 2 + n]); i += 2 + n
    return out


def _png(data):
    """PNG : tous les morceaux sauf l'image compressée (IDAT)."""
    out, i = [], 8
    while i + 8 <= len(data):
        n = int.from_bytes(data[i:i + 4], "big"); genre = data[i + 4:i + 8]
        if genre != b"IDAT":
            out.append(data[i:i + 12 + n])
        i += 12 + n
    return out


def _riff(data):
    """WAV : tous les morceaux sauf le son lui-même (data)."""
    out, i = [], 12
    while i + 8 <= len(data):
        genre = data[i:i + 4]; n = int.from_bytes(data[i + 4:i + 8], "little")
        if genre != b"data":
            out.append(data[i:i + 8 + n])
        i += 8 + n + (n & 1)
    return out


def _id3(data):
    """MP3 : l'étiquette ID3 du début et l'étiquette de fin."""
    out = [data[-128:]]
    if data[:3] == b"ID3":
        n = (data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9]
        out.append(data[:10 + n])
    return out


def metadonnees(chemin):
    data = chemin.read_bytes(); ext = chemin.suffix.lower()
    if ext in (".mp4", ".mov", ".m4v", ".m4a", ".heic"):
        out = []; _boites_mp4(data, 0, len(data), out); return b"".join(out)
    if ext in (".jpg", ".jpeg"):
        return b"".join(_jpeg(data))
    if ext == ".png":
        return b"".join(_png(data))
    if ext == ".wav":
        return b"".join(_riff(data))
    if ext == ".mp3":
        return b"".join(_id3(data))
    return data[:65536]


def marques(chemin):
    data = metadonnees(chemin)
    trouve = [nom for cle, nom in MARQUES.items() if cle in data]
    trouve += [f"signature du générateur {g.decode('utf-8', 'ignore')}" for g in GENERATEURS if g in data]
    return trouve


def fichiers(cibles):
    for cible in cibles:
        p = Path(cible)
        if p.is_dir():
            yield from (f for f in sorted(p.rglob("*")) if f.is_file() and f.suffix.lower() in EXTENSIONS)
        elif p.is_file():
            yield p


def main():
    resultats = [{"fichier": str(f), "marque": m} for f in fichiers(sys.argv[1:]) for m in marques(f)]
    print(json.dumps({"ok": not resultats, "marques": resultats}, ensure_ascii=False, indent=1))
    sys.exit(1 if resultats else 0)


if __name__ == "__main__":
    main()
