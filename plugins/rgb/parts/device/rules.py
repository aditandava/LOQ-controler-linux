def rule_config():
    pids, catchall = [], False
    if ITE_RULES.exists():
        for raw in (_read(ITE_RULES) or "").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or "048d" not in line.lower():
                continue
            m = re.search(r'ATTRS?\{idProduct\}=="([0-9A-Fa-f]{4})"', line)
            if m:
                pid = int(m.group(1), 16)
                if pid not in pids:
                    pids.append(pid)
            elif re.search(r'ATTRS?\{idVendor\}=="048d"', line, re.I):
                catchall = True
    for pid in ITE_PIDS:
        if pid not in pids:
            pids.append(pid)
    return pids, catchall


