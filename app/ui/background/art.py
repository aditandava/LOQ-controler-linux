def hex_rgb(value):
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def mix(first, second, amount):
    return tuple(round(a + (b - a) * amount) for a, b in zip(first, second))


def write_png(path, width, height, pixels):
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))

    stride = width * 3
    rows = b"".join(b"\0" + bytes(pixels[y * stride:(y + 1) * stride]) for y in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
                     + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b""))


def draw_art(path, colors, width=1200, height=800):
    """Draws a night landscape (sky, moon, stars, mountains) in the theme colours."""
    bg, surface, accent, accent2 = (hex_rgb(colors[f"loq_{name}"])
                                    for name in ("bg", "surface", "accent", "accent2"))
    stride = width * 3
    pixels = bytearray(stride * height)

    def blend(x, y, color, amount):
        at = y * stride + x * 3
        pixels[at:at + 3] = bytes(mix(pixels[at:at + 3], color, amount))

    horizon = mix(surface, accent, 0.45)
    for y in range(height):
        pixels[y * stride:(y + 1) * stride] = bytes(mix(bg, horizon, (y / height) ** 1.3)) * width

    cx, cy, radius, reach = int(width * 0.76), int(height * 0.22), 52, 240
    for y in range(max(0, cy - reach), min(height, cy + reach)):
        for x in range(cx - reach, min(width, cx + reach)):
            distance = math.hypot(x - cx, y - cy)
            if distance < reach:
                moon = max(0.0, min(1.0, radius + 0.5 - distance))
                blend(x, y, accent2, max(moon, 0.45 * (1 - distance / reach) ** 2))

    stars = random.Random(7)  # the same sky every time
    for _ in range(190):
        x, y = stars.randrange(width - 1), stars.randrange(int(height * 0.55))
        light = stars.uniform(0.25, 0.9)
        for dx in range(stars.choice((1, 1, 2))):
            blend(x + dx, y, (255, 255, 255), light)

    def peaks(value):
        return abs((value % 1.0) * 2 - 1)

    layers = ((0.66, 0.20, mix(surface, accent, 0.30), 0.15),
              (0.76, 0.17, mix(surface, bg, 0.40), 0.62),
              (0.90, 0.15, mix(bg, (0, 0, 0), 0.20), 0.37))
    for base, rise, color, shift in layers:
        for x in range(width):
            u = x / width
            ridge = (0.62 * peaks(u * 1.7 + shift) + 0.28 * peaks(u * 4.3 + shift * 3)
                     + 0.10 * peaks(u * 13 + shift * 7))
            top = (base - rise * ridge) * height
            first = int(top)
            blend(x, first, color, 1 - (top - first))  # smooth edge
            below = height - first - 1
            for channel in range(3):
                start = (first + 1) * stride + x * 3 + channel
                pixels[start::stride] = bytes([color[channel]]) * below
    write_png(path, width, height, pixels)


