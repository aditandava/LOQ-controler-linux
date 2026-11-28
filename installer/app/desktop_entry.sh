mkdir -p "$(dirname "$DESKTOP")" "$CONFIG/loq-center"
cat > "$DESKTOP" <<DESKTOP_EOF
[Desktop Entry]
Type=Application
Name=LOQ Center
Comment=Battery, performance, display and GPU controls
Exec="$BIN/loq-center"
Icon=$icon_ref
Terminal=false
Categories=Settings;HardwareSettings;
StartupWMClass=loq-center
DESKTOP_EOF

