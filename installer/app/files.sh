say "Installing the app (sudo is needed for the root helper)"
sudo install -Dm755 -o root -g root "$work/loq-center-helper" "$HELPER"
sudo install -Dm644 -o root -g root "$work/dev.loqcenter.policy" "$POLICY"
pkill -u "$(id -u)" -f 'loq-center --daemon' >/dev/null 2>&1 || true  # so the new version runs
install -Dm755 "$work/loq-center" "$BIN/loq-center"

