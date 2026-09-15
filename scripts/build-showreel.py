"""Build Salon Format's 25-second vertical reel from original project material.

The Elio and Emilie chapters use existing project reels. The remaining chapters
animate artwork/screens already used by their published experiences. No stock,
generated imagery, or external music is used.
"""

from pathlib import Path
from tempfile import TemporaryDirectory
import math
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DESKTOP = ROOT.parent
OUTPUT = ROOT / "public" / "showreel" / "salon-format-showreel.mp4"
FFMPEG = DESKTOP / "Museum Experience" / "Emilie Floege Reel" / "node_modules" / "ffmpeg-static" / "ffmpeg"
ELIO_REEL = DESKTOP / "SALON FORMAT" / "Museum Emilie Floege" / "experience" / "ELIOS-OCEAN-INSTAGRAM-REEL-FINAL.mp4"
EMILIE_REEL = DESKTOP / "Museum Experience" / "Emilie Floege Reel" / "EMILIE-FLOEGE-INSTAGRAM-REEL-V6.mp4"
FONT_DISPLAY = ROOT / "node_modules" / "@fontsource" / "della-respira" / "files" / "della-respira-latin-400-normal.woff2"
FONT_SANS = ROOT / "node_modules" / "@fontsource" / "josefin-sans" / "files" / "josefin-sans-latin-400-normal.woff2"
SIZE = (720, 1280)
FPS = 24


def run(*args):
    command = [str(FFMPEG), "-hide_banner", "-loglevel", "error", "-y", *map(str, args)]
    subprocess.run(command, check=True)


def font(size, display=False):
    return ImageFont.truetype(str(FONT_DISPLAY if display else FONT_SANS), size)


def text_png(path, key, label, word):
    im = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ink = (23, 23, 23, 255)
    cream = (247, 241, 229, 255)
    yellow = (255, 227, 59, 255)
    blue = (40, 35, 232, 255)
    coral = (255, 95, 87, 255)

    def plate(x, y, width, height, fill):
        # A single slightly imperfect color strip, drawn in the project's palette.
        d.polygon(((x, y + 5), (x + width - 4, y), (x + width, y + height - 5),
                   (x + 4, y + height)), fill=fill)

    if key == "elio":
        # The source reel already has interface labels. Keep the ocean and Elio's
        # creature clear, and give the one added verb its own space.
        plate(380, 520, 284, 110, yellow)
        d.text((400, 534), word, font=font(63, True), fill=ink)
    elif key == "kusama":
        plate(42, 235, 364, 76, cream)
        d.text((62, 257), label, font=font(27), fill=ink)
        plate(222, 830, 435, 137, cream)
        d.text((244, 842), word, font=font(75, True), fill=ink)
    elif key == "emilie":
        # Emilie's own footage already names the experience at the top.
        plate(42, 555, 250, 107, coral)
        d.text((62, 565), word, font=font(72, True), fill=ink)
    elif key == "firstaid":
        plate(40, 240, 595, 76, coral)
        d.text((58, 261), label, font=font(25), fill=cream)
    elif key == "learning":
        plate(40, 185, 455, 71, blue)
        d.text((58, 205), label, font=font(26), fill=cream)
        plate(40, 270, 240, 88, coral)
        d.text((58, 275), word, font=font(61, True), fill=ink)
    im.save(path)


def still_png(path, source, background, title=None):
    im = Image.new("RGBA", SIZE, background)
    art = Image.open(source).convert("RGBA")
    ratio = min(650 / art.width, 640 / art.height)
    art = art.resize((round(art.width * ratio), round(art.height * ratio)), Image.Resampling.LANCZOS)
    x = (SIZE[0] - art.width) // 2
    y = (SIZE[1] - art.height) // 2 + 45
    im.alpha_composite(art, (x, y))
    if title:
        d = ImageDraw.Draw(im)
        ink = (23, 23, 23, 255)
        d.text((66, 320), title, font=font(54, True), fill=ink)
    im.convert("RGB").save(path, quality=95)


def cover_png(path, source):
    art = Image.open(source).convert("RGB")
    ratio = max(SIZE[0] / art.width, SIZE[1] / art.height)
    art = art.resize((round(art.width * ratio), round(art.height * ratio)), Image.Resampling.LANCZOS)
    left = (art.width - SIZE[0]) // 2
    top = (art.height - SIZE[1]) // 2
    art.crop((left, top, left + SIZE[0], top + SIZE[1])).save(path, quality=95)


def detail_png(path, source, background, regions):
    """Reframe actual experience screens for a readable vertical composition."""
    im = Image.new("RGBA", SIZE, background)
    screenshot = Image.open(source).convert("RGBA")
    for bounds, target in regions:
        crop = screenshot.crop(bounds)
        x, y, width, height = target
        crop = crop.resize((width, height), Image.Resampling.LANCZOS)
        im.alpha_composite(crop, (x, y))
    im.convert("RGB").save(path, quality=95)


def end_png(path):
    blue = (40, 35, 232, 255)
    cream = (247, 241, 229, 255)
    im = Image.new("RGBA", SIZE, blue)
    logo = Image.open(ROOT / "public" / "brand" / "salon-format-wordmark-only.png").convert("RGBA")
    logo.thumbnail((610, 390), Image.Resampling.LANCZOS)
    im.alpha_composite(logo, ((SIZE[0] - logo.width) // 2, 370))
    d = ImageDraw.Draw(im)
    d.text((SIZE[0] / 2, 825), "Learning through design,", font=font(35), fill=cream, anchor="ma")
    d.text((SIZE[0] / 2, 875), "story and play.", font=font(35), fill=cream, anchor="ma")
    d.line((175, 963, 545, 963), fill=(255, 227, 59, 255), width=3)
    d.text((SIZE[0] / 2, 1027), "salonformat.com", font=font(34), fill=cream, anchor="ma")
    im.convert("RGB").save(path, quality=95)


def video_segment(source, start, duration, overlay, output, show_after=0):
    # Existing project video is kept intact apart from framing and small captions.
    run("-ss", start, "-i", source, "-loop", "1", "-i", overlay,
        "-filter_complex",
        f"[0:v]scale=720:1280:flags=lanczos,setsar=1[scene];"
        f"[scene][1:v]overlay=0:0:enable='gte(t,{show_after})',format=yuv420p[v]",
        "-map", "[v]", "-an", "-t", duration, "-r", FPS,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", output)


def still_segment(source, duration, overlay, output, motion=True):
    if motion:
        # One restrained camera move on a genuine project visual, not a fake UI action.
        vf = "[0:v]scale=780:1387,zoompan=z='min(zoom+0.0006,1.065)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=720x1280:fps=24[scene];"
    else:
        vf = "[0:v]scale=720:1280[scene];"
    run("-loop", "1", "-framerate", FPS, "-i", source,
        "-loop", "1", "-i", overlay,
        "-filter_complex", vf + "[scene][1:v]overlay=0:0,format=yuv420p[v]",
        "-map", "[v]", "-an", "-t", duration, "-r", FPS,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", output)


def sound(path):
    """Original low-key pluck rhythm and short interaction clicks, 25 seconds."""
    rate = 48000
    duration = 25
    audio = np.zeros(rate * duration, dtype=np.float64)
    pulse = 60 / 104
    notes = [196.0, 293.66, 246.94, 329.63, 220.0, 392.0]
    for beat in range(math.ceil(duration / pulse)):
        at = beat * pulse
        start = round(at * rate)
        length = min(round(.42 * rate), len(audio) - start)
        if length <= 0:
            continue
        t = np.arange(length) / rate
        freq = notes[(beat // 4) % len(notes)]
        env = np.exp(-10 * t)
        pluck = (np.sin(2 * np.pi * freq * t) + .25 * np.sin(2 * np.pi * 2 * freq * t)) * env
        audio[start:start + length] += (.042 if beat % 4 else .07) * pluck
    rng = np.random.default_rng(26)
    for at in [0.15, 2.0, 5.0, 9.0, 13.0, 17.0, 21.0, 24.0]:
        start = round(at * rate)
        length = min(round(.08 * rate), len(audio) - start)
        t = np.arange(length) / rate
        click = rng.normal(0, 1, length) * np.exp(-60 * t)
        audio[start:start + length] += .045 * click
    # A subtle continuous, warm bed lets the visuals breathe between pulses.
    t = np.arange(len(audio)) / rate
    audio += .012 * np.sin(2 * np.pi * 98 * t) * np.sin(np.pi * t / duration) ** 2
    audio *= min(1, .72 / max(np.max(np.abs(audio)), 1e-6))
    pcm = np.int16(np.clip(audio, -1, 1) * 32767)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm.tobytes())


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="salonformat-reel-") as temp:
        temp = Path(temp)
        overlays = {}
        specs = [
            ("elio", "ELIO’S OCEAN INVESTIGATION", "Explore."),
            ("kusama", "INTO THE INFINITE", "Discover."),
            ("emilie", "EMILIE FLÖGE", "Move."),
            ("firstaid", "WHAT IF I GET IT WRONG?", ""),
            ("learning", "LEARNING, DIFFERENTLY", "Learn."),
        ]
        for key, label, word in specs:
            overlays[key] = temp / f"{key}-text.png"
            text_png(overlays[key], key, label, word)

        kusama = temp / "kusama-frame.jpg"
        firstaid = temp / "firstaid-frame.jpg"
        learning = temp / "learning-frame.jpg"
        end = temp / "end-frame.jpg"
        cover_png(kusama, ROOT / "public" / "images" / "kusama" / "figure.png")
        detail_png(
            firstaid,
            ROOT / "public" / "images" / "first-aid" / "experience-preview.png",
            (184, 202, 197, 255),
            [((80, 175, 790, 545), (40, 410, 640, 330)),
             ((820, 142, 1275, 640), (180, 760, 360, 395))],
        )
        detail_png(
            learning,
            ROOT / "public" / "images" / "learning-differently-preview.png",
            (255, 242, 142, 255),
            [((970, 90, 1615, 530), (60, 365, 600, 410)),
             ((970, 565, 1615, 1000), (60, 790, 600, 410))],
        )
        end_png(end)
        transparent = temp / "transparent.png"
        Image.new("RGBA", SIZE, (0, 0, 0, 0)).save(transparent)

        segments = [temp / f"chapter-{i}.mp4" for i in range(6)]
        video_segment(ELIO_REEL, 0, 5, overlays["elio"], segments[0], show_after=2)
        still_segment(kusama, 4, overlays["kusama"], segments[1])
        video_segment(EMILIE_REEL, 1.55, 4, overlays["emilie"], segments[2])
        still_segment(firstaid, 4, overlays["firstaid"], segments[3])
        still_segment(learning, 4, overlays["learning"], segments[4])
        still_segment(end, 4, transparent, segments[5], motion=False)

        concat = temp / "chapters.txt"
        concat.write_text("".join(f"file '{part}'\n" for part in segments))
        wav = temp / "sound.wav"
        sound(wav)
        run("-f", "concat", "-safe", "0", "-i", concat, "-i", wav,
            "-map", "0:v", "-map", "1:a", "-c:v", "copy",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
            "-shortest", OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
