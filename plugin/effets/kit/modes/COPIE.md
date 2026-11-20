# Copie: the same edit as one of their reels, on a new take

The creator sends one of their own reels they loved ("je veux exactement ce montage") and a new take. You take the
reel apart, write down its recipe, and rebuild that recipe on the new take as closely as the kit allows. The reel is
the brief: where it disagrees with the mode file or their style pack, the reel wins.

What they do: send the reel, send the take, look at the side-by-side, say go. Everything else is yours, quietly.
Never show them frame sheets, measurements or the recipe file unless they ask.

## 1. Take the request
- They need two things: the reel (an Instagram, TikTok or YouTube link, or the file) and the new take. Missing one:
  ask for it in one line, nothing else.
- Their own reel only. A reel from someone else: say in one line that Copie is for their own reels, and offer
  `/editeur:nouvel-effet` for one effect from it, or `/editeur:studio-style` to take its look.
- Download it: `python3 $EDITEUR/outils/instagram.py <link> --dossier ~/Editeur/references --audio` (it falls back to
  the browser session when Instagram asks for a login). Keep `video.mp4`, the `.m4a` and the `.info.json`.
- Say how long this takes, once: "Je décortique ton reel (5 min), puis je monte la nouvelle vidéo pareil."

## 2. Take the reel apart (write `<project>/work/copie/recette.json`)
Look before you measure: the whole reel at 2 fps, then 6 fps on the first 3 seconds and around every cut.
- **Cut rhythm**: picture cuts (`ffmpeg -i video.mp4 -vf "select='gt(scene,0.3)',showinfo" -f null -`), the average
  and shortest shot, jump cuts inside a sentence or only between sentences, how tight the silences are (transcribe
  it with `PY KIT/pipeline/words.py` on a scratch project and measure the gaps between words).
- **Framing**: one framing or two (wide/close), punch-ins on which kind of words, slow pushes, b-roll or not.
- **Hook**: the on-screen text of the first seconds (exact words, size, place, box or not, how long it stays), and
  what happens on frame 0.
- **Captions**: word by word, phrase by phrase or none; font, size, case, colour, box, position, the highlighted
  word or not. `python3 $EDITEUR/outils/da.py images <video.mp4>` pulls 5 full-size frames and a sheet: read font, colours and
  position from them (the `ma-da` skill shows how).
- **Graphics and effects**: every overlay, card, screenshot, sticker, cutout trick, transition, with its second and
  the word it lands on. Match each one to an effect in `KIT/fx/LIBRARY.md` or `HOME/fx/LIBRARY.md`; one with no match
  is listed as "à recréer" (build it like `KIT/effect/EFFECT.md` step 2 onwards, on this take, after the storyboard
  is approved; never more than two new ones per video).
- **Music**: the track (the `.info.json` often names it: `track`, `artist`), where in the track the reel starts, the
  second of the reel where it drops, how loud it sits under the voice, whether it ducks. Find the same track in their
  bank (`~/Editeur/musiques`, `HOME/music`) first; not there: say which track it is and use the closest one they have
  until they add it. Copy the drop: the drop lands on the same kind of moment in the new take (the hook's last word, the
  turn, the punchline), not on the same second.
- **Sound effects**: whooshes on cuts, pops on overlays, risers, hits; density per 10 seconds.
- **Colour**: warmer or cooler, contrast, black-and-white beats. Note it, never apply it on your own: the new take
  keeps its picture as shot (SKILL.md step 3, Colour). If the reel's look matters, offer it in the storyboard.
- **End**: the last frame, a CTA, how long after the last word.

## 3. Pick the mode and write edit.py
- Pick the internal key the reel is closest to: mostly selfie with things on top of them = `lofi` (Brut); two
  framings and full-screen cards = `hifi` (Normal); a different effect on every line = `showcase` (Show-off).
  Scaffold with that `--mode` (SKILL.md step 1) and put `COPIE = "<reel link>"` at the top of `edit.py`.
- Cut the new take (SKILL.md step 2) with the reel's silence tightness and jump-cut habit.
- Map the recipe onto the new words: same hook shape and length, same caption system (override the pack's caption
  settings in edit.py when the reel differs), the same effect families at the same density, landing on the same kind of
  word; the same music start point relative to the hook and the drop on the matching beat; the same SFX density;
  no colour treatment unless they pick one from the storyboard (`GRADES = []` by default).
- The new take is not the reel: where the words don't offer the same moment (no list, no number, no turn), skip that
  effect rather than force it, and say so in the storyboard.

## 4. Storyboard: the reel next to the new video
Build the storyboard as usual (SKILL.md step 6), and add the reference: for each beat, the reel's matching frame
beside the new one (`work/copie/ref_<beat>.jpg`, taken at the reel's matching second). The message to the creator,
in French, says in three lines what was copied, what couldn't be (and why), and ends with « 👉 À toi : commente le
storyboard, ou écris go. »

## 5. Render
As usual (SKILL.md step 8). After the render, one line of comparison: length of both, number of cuts, of effects,
same music or not.
