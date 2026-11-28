say "Reloading udev rules"
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=usb --subsystem-match=hidraw

say "Done!"
if pgrep -u "$(id -u)" -f "loq-center" > /dev/null 2>&1; then
  say "Close the currently open LOQ Center window and reopen it to see the LOQ RGB tab."
else
  say "Open LOQ Center — the LOQ RGB tab will appear automatically."
fi
say "Remove RGB support any time with: bash loq_rgb.sh --uninstall"
