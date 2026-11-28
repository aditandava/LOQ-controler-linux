# -------------------------------------------------------------------------- GUI

def start_gui():
    try:
        import gi
        gi.require_version("Gtk", "3.0")
        gi.require_version("Gdk", "3.0")
        from gi.repository import Gdk, GLib, Gtk
    except (ImportError, ValueError) as err:
        print(f"GTK is not available: {err}\nInstall python-gobject and gtk3 (or python3-gi).",
              file=sys.stderr)
        return 1
    if Gdk.Display.get_default() is None:
        print("No graphical session detected.", file=sys.stderr)
        return 1
    GLib.set_prgname("loq-center")
    Gtk.Window.set_default_icon_name("loq-center")
    app = Gtk.Application(application_id="dev.loqcenter.App")
    state = {}

    def activate(_app):
        if "ui" not in state:
            state["ui"] = Window(app, Gtk, Gdk, GLib)
        state["ui"].window.present()

    app.connect("activate", activate)
    return app.run([])


