#!/usr/bin/env python3
import argparse
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("SpiceClientGtk", "3.0")
gi.require_version("SpiceClientGLib", "2.0")
from gi.repository import GLib, GObject, Gtk, SpiceClientGLib, SpiceClientGtk

RECONNECT_DELAY_SECONDS = 2


def resolve_uri(target, libvirt_uri):
    if "://" in target:
        return target
    out = subprocess.run(
        ["virsh", "-c", libvirt_uri, "domdisplay", target],
        capture_output=True, text=True,
    )
    if out.returncode != 0:
        sys.exit(f"virsh domdisplay {target!r} failed: {out.stderr.strip()}")
    uri = out.stdout.strip()
    if not uri:
        sys.exit(f"VM {target!r} has no graphical display configured")
    return uri


class Viewer:
    def __init__(self, target, libvirt_uri, title, reconnect, resize):
        self.target = target
        self.libvirt_uri = libvirt_uri
        self.reconnect = reconnect
        self.resize = resize
        self.display = None

        self.window = Gtk.Window()
        self.window.set_decorated(False)
        self.window.set_default_size(1024, 768)
        self.window.set_title(title or target)
        self.window.connect("destroy", lambda *_: Gtk.main_quit())

        self.session = None
        self.connect()

    def connect(self):
        uri = resolve_uri(self.target, self.libvirt_uri)
        self.session = SpiceClientGLib.Session()
        self.session.set_property("uri", uri)
        GObject.Object.connect(self.session, "channel-new", self.on_channel_new)
        GObject.Object.connect(self.session, "disconnected", self.on_disconnected)
        if not self.session.connect():
            sys.exit(f"failed to connect to {uri}")

    def on_channel_new(self, _session, channel):
        if isinstance(channel, SpiceClientGLib.DisplayChannel):
            channel_id = channel.get_property("channel-id")
            display = SpiceClientGtk.Display.new(self.session, channel_id)
            display.set_property("resize-guest", self.resize)
            display.set_property("grab-keyboard", True)
            display.set_property("grab-mouse", True)
            display.set_property("scaling", True)

            if self.display is not None:
                self.window.remove(self.display)
            self.display = display
            self.window.add(display)
            display.show()
            self.window.show()

    def on_disconnected(self, _session):
        if self.display is not None:
            self.window.remove(self.display)
            self.display = None
        if self.reconnect:
            GLib.timeout_add_seconds(RECONNECT_DELAY_SECONDS, self.try_reconnect)
        else:
            Gtk.main_quit()

    def try_reconnect(self):
        try:
            self.connect()
        except SystemExit:
            return True
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="libvirt domain name, or a spice:// URI")
    parser.add_argument("-c", "--connect", default="qemu:///system",
                         help="libvirt connection URI (default: qemu:///system)")
    parser.add_argument("--title", help="window title (default: target name)")
    parser.add_argument("--no-reconnect", action="store_false", dest="reconnect",
                         help="don't retry when the VM is unreachable or restarts")
    parser.add_argument("--no-resize", action="store_false", dest="resize",
                         help="don't resize the guest display when the window resizes")
    args = parser.parse_args()

    Viewer(args.target, args.connect, args.title, args.reconnect, args.resize)
    Gtk.main()


if __name__ == "__main__":
    main()
