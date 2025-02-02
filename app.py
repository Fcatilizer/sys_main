import gi
import psutil
import os
import subprocess
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, GLib

gi.require_version('Gtk', '4.0')

def update_battery_status(percentage_label, health_label):
    battery = psutil.sensors_battery()
    battery_percentage = battery.percent if battery else None
    battery_health = "Good"
    is_charging = battery.power_plugged if battery else False

    charging_icon = "⚡" if is_charging else ""
    percentage_label.set_text(f"{battery_percentage}% {charging_icon}")
    health_label.set_text(f"Health: {battery_health}")

    return True  # Continue calling this function

def change_power_profile(profile, buttons):
    try:
        subprocess.run(["powerprofilesctl", "set", profile], check=True)
        print(f"Power profile changed to: {profile}")
        for button in buttons:
            if button.get_label().startswith(profile.capitalize()):
                button.set_label(f"{profile.capitalize()} ✅")
            else:
                button.set_label(button.get_label().replace(" ✅", ""))
    except subprocess.CalledProcessError as e:
        print(f"Failed to change power profile: {e}")

def get_active_power_profile():
    try:
        result = subprocess.run(["powerprofilesctl", "get"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Failed to get active power profile: {e}")
        return None

def on_activate(app):
    battery = psutil.sensors_battery()
    battery_percentage = battery.percent if battery else None
    battery_health = "Good"
    is_charging = battery.power_plugged if battery else False

    win = Gtk.ApplicationWindow(application=app)
    win.set_title("System Maintenance")
    win.set_default_size(400, 600)
    print("Current working directory:", os.getcwd())

    try:
        icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        icon_info = icon_theme.lookup_icon("icon.png", 48, 1, Gtk.TextDirection.NONE, Gtk.IconLookupFlags.GENERIC_FALLBACK)
        if (icon_info):
            icon = GdkPixbuf.Pixbuf.new_from_file(icon_info.get_filename())
            gicon = Gio.Icon.new_for_string(icon_info.get_filename())
            image = Gtk.Image.new_from_gicon(gicon, Gtk.IconSize.DIALOG)
            win.set_icon(icon)
        else:
            print("Icon not found")
    except Exception as e:
        print(f"Error setting icon: {e}")

    # Battery Status
    column_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
    row_box.set_halign(Gtk.Align.CENTER)

    battery_icon = Gtk.Image.new_from_file("battery_icon.png")
    battery_icon.set_size_request(120, 120)

    charging_icon = "⚡" if is_charging else ""
    percentage_label = Gtk.Label(label=f"{battery_percentage}% {charging_icon}")
    health_label = Gtk.Label(label=f"Health: {battery_health}")

    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
    vbox.set_halign(Gtk.Align.START)
    vbox.set_valign(Gtk.Align.CENTER)
    vbox.append(percentage_label)
    vbox.append(health_label)

    row_box.append(battery_icon)
    row_box.append(vbox)
    column_box.append(row_box)

    # Add horizontal separator
    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    separator.set_margin_start(20)
    separator.set_margin_end(20)
    separator.set_margin_top(10)
    separator.set_margin_bottom(10)
    separator.set_size_request(-1, 8)  # Increase the height/thickness of the separator
    column_box.append(separator)

    # Subheader
    subheader_label = Gtk.Label(label="Change Power Profile Settings")
    subheader_label.set_halign(Gtk.Align.START)
    subheader_label.set_margin_start(20)
    subheader_label.set_margin_top(6)
    subheader_label.set_margin_bottom(2)
    column_box.append(subheader_label)

    # Power Profiles Buttons
    power_profiles = ["balanced", "power-saver", "performance"]
    power_profile_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    power_profile_buttons.set_halign(Gtk.Align.CENTER)
    
    buttons = []
    active_profile = get_active_power_profile()
    for profile in power_profiles:
        label = f"{profile.capitalize()} ✅" if profile == active_profile else profile.capitalize()
        button = Gtk.Button(label=label)
        button.set_margin_top(10)
        button.set_margin_bottom(10)
        button.set_margin_start(10)
        button.set_margin_end(10)
        button.connect("clicked", lambda btn, p=profile: change_power_profile(p, buttons))
        buttons.append(button)
        power_profile_buttons.append(button)
    
    column_box.append(power_profile_buttons)

    # Add horizontal separator
    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    separator.set_margin_start(20)
    separator.set_margin_end(20)
    separator.set_margin_top(10)
    separator.set_margin_bottom(10)
    separator.set_size_request(-1, 8)  # Increase the height/thickness of the separator
    column_box.append(separator)
    
    # Subheader
    subheader_label = Gtk.Label(label="Basic System Maintenance (Not Built Yet)")
    subheader_label.set_halign(Gtk.Align.START)
    subheader_label.set_margin_start(20)
    subheader_label.set_margin_top(6)
    subheader_label.set_margin_bottom(2)
    column_box.append(subheader_label)


    # Add a 3x2 grid with buttons
    grid = Gtk.Grid()
    grid.set_column_spacing(50)  # Increase column spacing
    grid.set_row_spacing(20)     # Increase row spacing
    grid.set_margin_start(20)
    grid.set_margin_end(20)
    grid.set_margin_top(10)
    grid.set_margin_bottom(10)
    grid.set_halign(Gtk.Align.CENTER)  # Center the grid horizontally

    button_texts = ["Clear Cache", "Clear Orphan file ⚠️", "Clear Swap file", "Kill All Process ", "Clear Session Management", "System Update"]
    for i, text in enumerate(button_texts):
        button = Gtk.Button(label=text)
        grid.attach(button, i % 2, i // 2, 1, 1)

    column_box.append(grid)

    # Add footer
    footer_label = Gtk.Label(label="Alpha build for Arch or Arch based Systems")
    footer_label.set_halign(Gtk.Align.CENTER)
    footer_label.set_margin_top(10)
    column_box.append(footer_label)

    win.set_child(column_box)
    win.present()

    # Update battery status every 5 seconds
    GLib.timeout_add_seconds(5, update_battery_status, percentage_label, health_label)

app = Gtk.Application()
app.connect('activate', on_activate)
app.run(None)
