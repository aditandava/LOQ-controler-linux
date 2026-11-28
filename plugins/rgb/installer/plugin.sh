# ------------------------------------------------------------------ RGB plugin
say "Installing LOQ RGB plugin into $PLUGIN"
mkdir -p "$PLUGIN_DIR"
rm -f "$CONFIG/rgb-enabled"

cat > "$PLUGIN" << 'RGB_PLUGIN_EOF'
@@PLUGIN@@
RGB_PLUGIN_EOF

chmod 0644 "$PLUGIN"
python3 -c "import py_compile; py_compile.compile('$PLUGIN', doraise=True)"

