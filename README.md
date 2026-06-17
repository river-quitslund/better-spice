# spice-view

  Minimal, decoration-free SPICE viewer for libvirt/QEMU VMs. Connects by
  libvirt domain name, shares keyboard/mouse, and resizes the guest display
  to match the window in real time.

  ## Requirements

  - `python3-gobject`
  - `spice-gtk3` (provides the `SpiceClientGtk`/`SpiceClientGLib` typelibs)
  - `spice-vdagent` running in the guest (needed for live resize)
  - `virsh` (libvirt) for resolving a VM name to its SPICE URI

  ## Usage

      spice-view <vm-name>              # connect by libvirt domain name
      spice-view spice://host:port      # or connect directly by URI

      spice-view kali --no-reconnect    # don't auto-retry on disconnect
      spice-view kali --no-resize       # disable guest auto-resize
      spice-view kali -c qemu:///session --title "my vm"

  ## Options

  | Flag             | Description                                      |
  |------------------|---------------------------------------------------|
  | `-c, --connect`  | libvirt connection URI (default `qemu:///system`) |
  | `--title`        | window title (default: VM/target name)            |
  | `--no-reconnect` | don't retry when the VM is unreachable/restarts   |
  | `--no-resize`    | don't resize the guest display with the window    |
