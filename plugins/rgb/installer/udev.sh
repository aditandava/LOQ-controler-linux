# ------------------------------------------------------------------ udev rules
# Edit PIDs freely for newer Lenovo LOQ / Legion / IdeaPad Gaming models.
say "Installing udev rules for ITE RGB keyboard"
sudo tee "$RULES" > /dev/null << 'RULES_EOF'
@@RULES@@
RULES_EOF

