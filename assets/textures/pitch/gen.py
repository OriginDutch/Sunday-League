"""Procedural seamless stylised grass: albedo + 16-bit height + normal (OpenGL / Godot)."""
import sys, numpy as np
from PIL import Image, ImageDraw

OUT = 1024
SS = 2                      # supersample factor
W = OUT * SS
C_LO = np.array([0x4F, 0x8A, 0x3A], float)
C_HI = np.array([0x5E, 0x9A, 0x45], float)


def tile_noise(rng, n, beta, fmin=1, fmax=None):
    """Periodic noise via spectral synthesis -> tiles perfectly. Returns [0,1]."""
    fx = np.fft.fftfreq(n) * n
    fy = np.fft.rfftfreq(n) * n
    f = np.sqrt(fx[:, None] ** 2 + fy[None, :] ** 2)
    amp = np.zeros_like(f)
    m = f >= fmin
    if fmax: m &= f <= fmax
    amp[m] = f[m] ** (-beta)
    ph = rng.uniform(0, 2 * np.pi, f.shape)
    img = np.fft.irfft2(amp * np.exp(1j * ph), s=(n, n))
    img -= img.min(); img /= img.max()
    return img


def generate(edge, seed, blades, length, width, dir_coherence, clump, tint_var, gap_dark):
    rng = np.random.default_rng(seed)
    hgt = Image.new("I", (W, W), 0)      # blade height (0 = gap)
    tnt = Image.new("I", (W, W), 0)      # blade tint 1..1000
    ids = Image.new("I", (W, W), 0)      # blade id, for outlines
    dh, dt, di = ImageDraw.Draw(hgt), ImageDraw.Draw(tnt), ImageDraw.Draw(ids)

    clumps = tile_noise(rng, 256, 1.6, 2, 24)          # density/height clumping
    dirf = tile_noise(rng, 256, 2.2, 1, 6) * 4 * np.pi  # smooth direction field

    xs = rng.uniform(0, W, blades)
    ys = rng.uniform(0, W, blades)
    ci = ((ys / W * 256).astype(int) % 256, (xs / W * 256).astype(int) % 256)
    cl = clumps[ci]
    ang = dir_coherence * dirf[ci] + (1 - dir_coherence) * rng.uniform(0, 2 * np.pi, blades)
    ang += rng.normal(0, 0.35, blades)
    L = length * SS * rng.uniform(0.6, 1.3, blades) * (1 + clump * (cl - 0.5))
    Wd = width * SS * rng.uniform(0.75, 1.25, blades)
    top = np.clip(0.55 + 0.35 * rng.random(blades) + clump * 0.4 * (cl - 0.5), 0.2, 1.0)
    tint = np.clip(0.5 + tint_var * rng.normal(0, 1, blades) + 0.35 * (cl - 0.5), 0.02, 0.98)

    order = np.argsort(top)               # painter's order: tallest on top
    SEG = 4
    for i in order:
        x, y, a, l, w = xs[i], ys[i], ang[i], L[i], Wd[i]
        dx, dy = np.cos(a), np.sin(a)
        px, py = -dy, dx
        # tapered blade as SEG quads, height rising toward tip
        pts = []
        for s in range(SEG + 1):
            t = s / SEG
            cx, cy = x + dx * l * t, y + dy * l * t
            hw = w * 0.5 * (1 - t) ** 0.8 + 0.25
            pts.append(((cx + px * hw, cy + py * hw), (cx - px * hw, cy - py * hw)))
        r = l + w
        shifts = [(ox, oy) for ox in ((-W, 0, W) if (x - r < 0 or x + r > W) else (0,))
                  for oy in ((-W, 0, W) if (y - r < 0 or y + r > W) else (0,))]
        hv_base = top[i] * 60000
        tv = int(tint[i] * 1000) + 1
        for s in range(SEG):
            (a1, b1), (a2, b2) = pts[s], pts[s + 1]
            hv = int(hv_base * (0.25 + 0.75 * (s + 1) / SEG))
            for ox, oy in shifts:
                poly = [(p[0] + ox, p[1] + oy) for p in (a1, a2, b2, b1)]
                dh.polygon(poly, fill=hv)
                dt.polygon(poly, fill=tv)
                di.polygon(poly, fill=int(i) + 1)

    H = np.asarray(hgt, float) / 60000.0
    T = np.asarray(tnt, float)
    gap = T == 0
    I = np.asarray(ids)
    E = ((I != np.roll(I, 1, 0)) | (I != np.roll(I, 1, 1))).astype(float)
    T = np.where(gap, 0, (T - 1) / 1000.0)

    # downsample 2x (box) -> stays periodic
    def down(a): return a.reshape(OUT, SS, OUT, SS).mean((1, 3))
    H, T, G, E = down(H), down(T), down(gap.astype(float)), down(E)

    base = tile_noise(rng, OUT, 1.8, 2, 40)      # soft large colour variation
    fine = tile_noise(rng, OUT, 0.6, 60)          # micro grain
    k = np.clip(0.30 * base + 0.25 * T + 0.40 * H + 0.05 * fine, 0, 1)
    k = (k - k.min()) / (k.max() - k.min())
    col = C_LO[None, None] + (C_HI - C_LO)[None, None] * k[..., None]
    col *= (1 - gap_dark * G - edge * E)[..., None]   # gaps + blade outlines a touch deeper
    albedo = np.clip(col, 0, 255).astype(np.uint8)

    # height: blades + soft clump undulation, light wrap blur
    hh = 0.8 * H + 0.2 * tile_noise(rng, OUT, 1.6, 2, 30)
    hh = (hh + np.roll(hh, 1, 0) + np.roll(hh, -1, 0) + np.roll(hh, 1, 1) + np.roll(hh, -1, 1) + hh * 3) / 8
    hh = (hh - hh.min()) / (hh.max() - hh.min())
    h16 = (hh * 65535).astype(np.uint16)

    # normal map (OpenGL / Godot: +Y up), wrap-aware gradients
    s = 4.0
    gx = (np.roll(hh, -1, 1) - np.roll(hh, 1, 1)) * 0.5 * s
    gy = (np.roll(hh, -1, 0) - np.roll(hh, 1, 0)) * 0.5 * s
    n = np.dstack([-gx, gy, np.ones_like(hh)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    normal = ((n * 0.5 + 0.5) * 255).round().astype(np.uint8)
    return albedo, h16, normal


VARIANTS = {
    "A_fine":   dict(edge=0.07, seed=11, blades=140000, length=7,  width=2.2, dir_coherence=0.0, clump=0.4, tint_var=0.12, gap_dark=0.06),
    "B_clumpy": dict(edge=0.045, seed=22, blades=95000,  length=10, width=3.0, dir_coherence=0.25, clump=1.0, tint_var=0.16, gap_dark=0.045),
    "C_soft":   dict(edge=0.05, seed=33, blades=110000, length=9,  width=2.8, dir_coherence=0.6, clump=0.6, tint_var=0.08, gap_dark=0.04),
}

if __name__ == "__main__":
    name = sys.argv[1]
    alb, h16, nrm = generate(**VARIANTS[name])
    pre = f"/home/claude/grass/out/grass_{name}"
    Image.fromarray(alb, "RGB").save(pre + "_albedo.png")
    Image.fromarray(h16).save(pre + "_height16.png")
    Image.fromarray((h16 >> 8).astype(np.uint8), "L").save(pre + "_height8.png")
    Image.fromarray(nrm, "RGB").save(pre + "_normal.png")
    print(name, "done")
