#!/usr/bin/env python3
"""Carminite Cadence — crimson rhythm-tap arcade for ElbowOS. Python 3 + pygame."""
import math, os, random, subprocess, sys

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
RECORD = "--play" not in sys.argv
if RECORD:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

W, H, FPS, SECS = 1080, 1920, 30, 15
OUT = os.environ.get("ELBOWOS_MP4", "/workspace/artifacts/CARMINITE_CADENCE_ElbowOS.mp4")
TITLE, HANDLE = "CARMINITE CADENCE", "x.com/ElbowOS"
WINE, GOLD, CREAM = (32, 8, 18), (255, 198, 96), (255, 236, 214)
CRIMSON, AMBER, ROSE = (214, 42, 68), (255, 148, 42), (255, 112, 146)
LANES, HIT_Y, SPEED = 4, 1500, 16.0
LX = [190, 430, 670, 910]


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        try:
            self.screen = pygame.display.set_mode((W, H), 0 if not RECORD else pygame.HIDDEN)
        except pygame.error:
            os.environ["SDL_VIDEODRIVER"] = "dummy"
            pygame.display.quit()
            pygame.display.init()
            self.screen = pygame.display.set_mode((W, H), pygame.HIDDEN)
        self.font = pygame.font.Font(None, 72)
        self.mid = pygame.font.Font(None, 48)
        self.small = pygame.font.Font(None, 36)
        self.reset()

    def reset(self):
        self.t = 0
        self.score = 0
        self.combo = 0
        self.judge, self.judge_t = "", 0
        self.flash = [0] * LANES
        self.sparks, self.notes = [], []
        self.rng = random.Random(11)
        self.chart, frame, i = [], 6, 0
        pat = [0, 1, 2, 3, 2, 1, 3, 0, 1, 3, 2, 0, 2, 3, 1, 0]
        while frame < FPS * SECS - 18:
            self.chart.append((frame, pat[i % len(pat)], i % 3))
            if i % 6 == 5:
                self.chart.append((frame, (pat[i % len(pat)] + 2) % 4, (i + 1) % 3))
            frame += 14 if i % 4 else 18
            i += 1
        self.ci = 0
        for k, lane in enumerate([1, 3, 0, 2, 1]):
            self.notes.append({"lane": lane, "y": 360 + k * 200, "hit": False, "hue": k % 3})

    def update(self, presses):
        self.t += 1
        while self.ci < len(self.chart) and self.chart[self.ci][0] <= self.t:
            _, lane, hue = self.chart[self.ci]
            self.notes.append({"lane": lane, "y": 250, "hit": False, "hue": hue})
            self.ci += 1
        for i in range(LANES):
            self.flash[i] = max(0, self.flash[i] - 1)
        self.judge_t = max(0, self.judge_t - 1)
        for lane in presses:
            self._tap(lane)
        for n in self.notes:
            n["y"] += SPEED
            if not n["hit"] and n["y"] > HIT_Y + 100:
                n["hit"] = True
                self.combo = 0
                self.judge, self.judge_t = "MISS", 10
        self.sparks = [s for s in self.sparks if s["life"] > 0]
        for s in self.sparks:
            s["x"] += s["vx"]
            s["y"] += s["vy"]
            s["vy"] += 0.25
            s["life"] -= 1

    def _tap(self, lane):
        self.flash[lane] = 8
        best, best_d = None, 999
        for n in self.notes:
            if n["hit"] or n["lane"] != lane:
                continue
            d = abs(n["y"] - HIT_Y)
            if d < best_d:
                best, best_d = n, d
        if best and best_d < 120:
            best["hit"] = True
            perfect = best_d < 40
            self.score += (140 if perfect else 70) + self.combo * 5
            self.combo += 1
            self.judge = "PERFECT" if perfect else "GOOD"
            self.judge_t = 12
            self._burst(LX[lane], HIT_Y, GOLD if perfect else CREAM)
        else:
            self.combo = 0
            self.judge, self.judge_t = "WHIFF", 8

    def _burst(self, x, y, col):
        for i in range(16):
            a = i / 16 * math.tau
            self.sparks.append({
                "x": x, "y": y, "vx": math.cos(a) * (3 + i % 4),
                "vy": math.sin(a) * (3 + i % 4) - 3, "life": 16, "col": col,
            })

    def auto_presses(self):
        presses = []
        for lane in range(LANES):
            for n in self.notes:
                if n["hit"] or n["lane"] != lane:
                    continue
                if abs(n["y"] - HIT_Y) <= SPEED * 0.55:
                    presses.append(lane)
                    break
        return presses

    def draw(self, surf):
        surf.fill(WINE)
        drift = (self.t * 6) % 80
        for y in range(-80, H, 80):
            pygame.draw.line(surf, (58, 16, 28), (0, y + drift), (W, y + drift), 2)
        pulse = 0.5 + 0.5 * math.sin(self.t * 0.12)
        glow = pygame.Surface((W, 520), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (160, 36, 54, int(80 + 50 * pulse)), glow.get_rect())
        surf.blit(glow, (0, 1120))
        for i, x in enumerate(LX):
            pygame.draw.line(surf, (110, 36, 48), (x, 300), (x, 1700), 8)
            if self.flash[i]:
                pad = pygame.Surface((170, 80), pygame.SRCALPHA)
                pygame.draw.ellipse(pad, (255, 190, 90, 170), pad.get_rect())
                surf.blit(pad, (x - 85, HIT_Y - 34))
            pygame.draw.circle(surf, GOLD, (x, HIT_Y), 42, 5)
            pygame.draw.circle(surf, CREAM, (x, HIT_Y), 9)
        pygame.draw.line(surf, GOLD, (70, HIT_Y), (W - 70, HIT_Y), 4)
        colors = [CRIMSON, AMBER, ROSE]
        for n in self.notes:
            if n["hit"] or n["y"] < 220 or n["y"] > 1780:
                continue
            x, y = LX[n["lane"]], int(n["y"])
            col = colors[n["hue"]]
            pygame.draw.polygon(surf, col, [(x, y - 52), (x + 40, y), (x, y + 52), (x - 40, y)])
            pygame.draw.polygon(surf, CREAM, [(x, y - 26), (x + 18, y), (x, y + 26), (x - 18, y)])
            pygame.draw.circle(surf, col, (x, y), 8)
            pygame.draw.line(surf, GOLD, (x, y - 52), (x, y - 74), 4)
        for s in self.sparks:
            pygame.draw.circle(surf, s["col"], (int(s["x"]), int(s["y"])), max(2, s["life"] // 3))
        title = self.font.render(TITLE, True, GOLD)
        surf.blit(title, title.get_rect(center=(W // 2, 100)))
        surf.blit(self.small.render(HANDLE, True, CREAM), self.small.render(HANDLE, True, CREAM).get_rect(center=(W // 2, 168)))
        surf.blit(self.mid.render(f"SCORE  {self.score}", True, CREAM), self.mid.render(f"SCORE  {self.score}", True, CREAM).get_rect(center=(W // 2, 230)))
        if self.combo > 1:
            tag = self.mid.render(f"{self.combo} CHAIN", True, ROSE)
            surf.blit(tag, tag.get_rect(center=(W // 2, 290)))
        if self.judge_t:
            jc = GOLD if self.judge == "PERFECT" else CREAM
            j = self.font.render(self.judge, True, jc)
            surf.blit(j, j.get_rect(center=(W // 2, 1660)))
        hint = self.small.render("A  S  D  F    TAP THE LANTERNS", True, (210, 150, 140))
        surf.blit(hint, hint.get_rect(center=(W // 2, 1824)))

    def play_interactive(self):
        clock = pygame.time.Clock()
        keys = {pygame.K_a: 0, pygame.K_s: 1, pygame.K_d: 2, pygame.K_f: 3,
                pygame.K_LEFT: 0, pygame.K_DOWN: 1, pygame.K_UP: 2, pygame.K_RIGHT: 3}
        running = True
        while running:
            presses = []
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
                    running = False
                elif ev.type == pygame.KEYDOWN and ev.key in keys:
                    presses.append(keys[ev.key])
                elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                    self.reset()
            self.update(presses)
            self.draw(self.screen)
            pygame.display.flip()
            clock.tick(FPS)
        pygame.quit()

    def record(self):
        os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
        cmd = ["ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-an", "-c:v", "libx264",
               "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", OUT]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for _ in range(FPS * SECS):
                self.update(self.auto_presses())
                self.draw(self.screen)
                proc.stdin.write(pygame.image.tobytes(self.screen, "RGB"))
        finally:
            proc.stdin.close()
            err = proc.stderr.read().decode("utf-8", "ignore")
            rc = proc.wait()
        if rc != 0:
            raise SystemExit(f"ffmpeg failed ({rc}):\n{err[-1200:]}")
        print("wrote", OUT)
        pygame.quit()


def main():
    g = Game()
    g.play_interactive() if not RECORD else g.record()


if __name__ == "__main__":
    main()
