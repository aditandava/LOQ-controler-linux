install_deps() {
  if command -v pacman >/dev/null; then deps_pacman
  elif command -v apt-get >/dev/null; then deps_apt
  elif command -v dnf >/dev/null; then deps_dnf
  elif command -v zypper >/dev/null; then deps_zypper
  else deps_other
  fi
}

install_deps

