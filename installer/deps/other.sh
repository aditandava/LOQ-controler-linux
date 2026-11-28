deps_other() {
  command -v python3 >/dev/null || die "python3 is required."
  command -v pkexec >/dev/null || die "polkit (pkexec) is required."
}

