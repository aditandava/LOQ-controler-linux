def build_packet(profile):
    """33-byte ITE 8295 HID Feature Report (Report ID 0xCC, command 0x16)."""
    effect = profile.get("effect", "Static")
    colors = profile.get("colors", EMPTY_PROFILE["colors"])
    brightness = max(1, min(2, int(profile.get("brightness", 2))))
    speed = max(1, min(4, int(profile.get("speed", 1))))

    pkt = bytearray(33)
    pkt[0] = 0xCC
    pkt[1] = 0x16
    if effect == "Off":
        pkt[2], pkt[3], pkt[4] = 0x01, 0x01, 0x01
        return bytes(pkt)

    pkt[2] = EFFECT_CODES.get(effect, 0x01)
    pkt[3] = speed
    pkt[4] = brightness
    idx = 5
    for hx in colors[:4]:
        r, g, b = hex_to_rgb(hx)
        pkt[idx], pkt[idx + 1], pkt[idx + 2] = r & 0xFF, g & 0xFF, b & 0xFF
        idx += 3
    if effect == "Wave":
        pkt[19] = 0x01
    return bytes(pkt)


