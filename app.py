import gi
import psutil
import os
import subprocess
import distro
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, GLib

gi.require_version('Gtk', '4.0')


def prepare():
    if not isZenityInstalled():
        messageZen("Warning", "Zenity is not installed and could not be installed.")
        return False

    try:
        result = subprocess.run(["pgrep", "-x", "zenity"], capture_output=True, text=True)
        if result.returncode == 0:
            messageZen("Warning", "Zenity is already running.")
            return False
    except subprocess.CalledProcessError as e:
        messageZen("Error", f"Failed to check if Zenity is running: {e}")
        return False

    return True

def messageZen(title, message):
    if prepare():
        try:
            subprocess.run(["zenity", "--info", "--title", title, "--text", message], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to show message: {e}")

def errorZen(title, message):
    if prepare():
        try:
            subprocess.run(["zenity", "--error", "--title", title, "--text", message], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to show error: {e}")

def update_battery_status(percentage_label, health_label):
    battery = psutil.sensors_battery()
    battery_percentage = int(battery.percent) if battery else None
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

def isZenityInstalled():
    try:
        subprocess.run(["zenity", "--version"], check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError:
        subprocess.run(["sudo", "apt", "install", "-y", "zenity"], check=True)
        return False

def sudoPasswordPrompt():
    if isZenityInstalled():
        try:
            result = subprocess.run(["zenity", "--password"], check=True, capture_output=True, text=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Failed to get sudo password: {e}")
            return None
    else:
        print("Zenity is not installed")
        return None

def killAllProcess(_):
    sudo_password = sudoPasswordPrompt()
    if not sudo_password:
        print("No sudo password provided")
        return

    try:
        subprocess.run(["sudo", "pkill", "-9", "-u", os.getlogin()], input=sudo_password + "\n", text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to kill all process: {e}")

def clearSessionManagement(_):
    sudo_password = sudoPasswordPrompt()
    if not sudo_password:
        print("No sudo password provided")
        return

    try:
        subprocess.run(["sudo", "rm", "-rf", "/tmp/*"], input=sudo_password + "\n", text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to clear session management: {e}")

def clearSwapFile(_):
    sudo_password = sudoPasswordPrompt()
    if not sudo_password:
        print("No sudo password provided")
        return

    try:
        subprocess.run(["sudo", "swapoff", "-a"], input=sudo_password + "\n", text=True, check=True)
        subprocess.run(["sudo", "swapon", "-a"], input=sudo_password + "\n", text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to clear swap file: {e}")

def clearCache(_):
    sudo_password = sudoPasswordPrompt()
    if not sudo_password:
        print("No sudo password provided")
        return

    try:
        subprocess.run(["sudo", "-S", "rm", "-rf", "/var/cache/pacman/pkg/"], input=sudo_password + "\n", text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to clear cache: {e}")

def clearOrphanFile(_):
    sudo_password = sudoPasswordPrompt()
    if not sudo_password:
        print("No sudo password provided")
        return

    try:
        subprocess.run(["sudo", "pacman", "-Rns", "$(pacman -Qdtq)"], input=sudo_password + "\n", text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to clear orphan file: {e}")

def check_distro_and_update(_):
    distro_name = distro.id().lower()  # Get the lowercase distribution ID
    sudo_password = sudoPasswordPrompt()
    if not sudo_password:
        messageZen("Error", "No sudo password provided")
        return

    try:
        if 'arch' in distro_name or 'manjaro' in distro_name:
            subprocess.run(["sudo", "pacman", "-Syu", "--noconfirm"], input=sudo_password + "\n", text=True, check=True)
            subprocess.run(["yay", "-Syu", "--noconfirm"], check=True)
            subprocess.run(["paru", "-Syu", "--noconfirm"], check=True)
        elif 'ubuntu' in distro_name or 'debian' in distro_name:
            subprocess.run(["sudo", "-S", "apt", "update"], input=sudo_password + "\n", text=True, check=True)
            subprocess.run(["sudo", "-S", "apt", "upgrade", "-y"], input=sudo_password + "\n", text=True, check=True)
        else:
            messageZen("Error", f"Unsupported distribution: {distro_name}")
            return
        messageZen("Success", "System update completed successfully.")
    except subprocess.CalledProcessError as e:
        messageZen("Error", f"Failed to update system: {e}")

def create_main_page():
    battery = psutil.sensors_battery()
    battery_percentage = int(battery.percent) if battery else None
    battery_health = "Good"
    is_charging = battery.power_plugged if battery else False

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
    subheader_label = Gtk.Label(label="Change Power Profiles Daemon Settings")
    subheader_label.set_halign(Gtk.Align.START)
    subheader_label.set_margin_start(20)
    subheader_label.set_margin_top(6)
    subheader_label.set_margin_bottom(10)
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
    
    subheader_label = Gtk.Label(label="Basic System Maintenance (In Progress)")
    subheader_label.set_halign(Gtk.Align.START)
    subheader_label.set_margin_start(20)
    subheader_label.set_margin_top(6)
    subheader_label.set_margin_bottom(2)
    column_box.append(subheader_label)

    # Add a 3x2 grid with buttons
    grid = Gtk.Grid()
    grid.set_column_spacing(50)
    grid.set_row_spacing(20)
    grid.set_margin_start(20)
    grid.set_margin_end(20)
    grid.set_margin_top(10)
    grid.set_margin_bottom(10)
    grid.set_halign(Gtk.Align.CENTER)

    button_texts = ["Clear Pacman Cache", "Clear Orphan file ⚠️", "Clear Swap file", "Kill All Process", "Clear Session Management", "System Update"]
    for i, text in enumerate(button_texts):
        button = Gtk.Button(label=text)
        if text == "System Update":
            button.connect("clicked", check_distro_and_update)
        elif text == "Clear Orphan file ⚠️":
            button.connect("clicked", clearOrphanFile)
        elif text == "Clear Swap file":
            button.connect("clicked", clearSwapFile)
        elif text == "Clear Pacman Cache":
            button.connect("clicked", clearCache)
        elif text == "Kill All Process":
            button.connect("clicked", killAllProcess)
        elif text == "Clear Session Management":
            button.connect("clicked", clearSessionManagement)

        grid.attach(button, i % 2, i // 2, 1, 1)

    column_box.append(grid)

    # Add footer
    footer_label = Gtk.Label(label="Alpha build for Arch or Arch based Systems")
    footer_label.set_halign(Gtk.Align.CENTER)
    footer_label.set_margin_top(10)
    column_box.append(footer_label)

    return column_box, percentage_label, health_label

def create_second_page():
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    asusctl_status_label = Gtk.Label()
    asusctl_status_label.set_halign(Gtk.Align.START)
    asusctl_status_label.set_margin_start(20)
    asusctl_status_label.set_margin_top(6)
    try:
        subprocess.run(["asusctl", "--version"], check=True, capture_output=True, text=True)
        asusctl_status_label.set_text("✅ asusctl is installed")
    except subprocess.CalledProcessError:
        asusctl_status_label.set_text("❌ asusctl is not installed")
    box.append(asusctl_status_label)

    label = Gtk.Label(label="Disk Usage / Memory Usage")
    label.set_halign(Gtk.Align.CENTER)
    label.set_margin_top(10)

    box.append(label)

    disk_usage = psutil.disk_usage('/')
    memory_usage = psutil.virtual_memory()

    disk_usage_label = Gtk.Label(label=f"Disk Usage: {disk_usage.percent}%")
    memory_usage_label = Gtk.Label(label=f"Memory Usage: {memory_usage.percent}%")
    free_space_label = Gtk.Label(label=f"Free Space: {disk_usage.free // (1024 ** 3)} GB")
    free_memory_label = Gtk.Label(label=f"Free Memory: {memory_usage.available // (1024 ** 2)} MB")

    disk_usage_label.set_halign(Gtk.Align.START)
    memory_usage_label.set_halign(Gtk.Align.START)
    free_space_label.set_halign(Gtk.Align.START)
    free_memory_label.set_halign(Gtk.Align.START)

    grid = Gtk.Grid()
    grid.set_column_spacing(50)
    grid.set_row_spacing(20)
    grid.set_margin_start(20)
    grid.set_margin_end(20)
    grid.set_margin_top(10)
    grid.set_margin_bottom(10)
    grid.set_halign(Gtk.Align.CENTER)

    grid.attach(disk_usage_label, 0, 0, 1, 1)
    grid.attach(memory_usage_label, 1, 0, 1, 1)
    grid.attach(free_space_label, 0, 1, 1, 1)
    grid.attach(free_memory_label, 1, 1, 1, 1)

    box.append(grid)

    # Add horizontal separator
    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    separator.set_margin_start(20)
    separator.set_margin_end(20)
    separator.set_margin_top(10)
    separator.set_margin_bottom(10)
    separator.set_size_request(-1, 8)  # Increase the height/thickness of the separator
    box.append(separator)



    return box

def on_activate(app):
    if not prepare():
        return

    messageZen("Welcome", "Welcome to System Maintenance")
    
    win = Gtk.ApplicationWindow(application=app)
    win.set_title("System Maintenance")
    win.set_default_size(400, 600)
    print("Current working directory:", os.getcwd())

    try:
        icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        icon_info = icon_theme.lookup_icon("icon.png", 48, 1, Gtk.TextDirection.NONE, Gtk.IconLookupFlags.GENERIC_FALLBACK)
        if icon_info:
            icon = GdkPixbuf.Pixbuf.new_from_file(icon_info.get_filename())
            win.set_icon(icon)
        else:
            print("Icon not found")
    except Exception as e:
        print(f"Error setting icon: {e}")

    stack = Gtk.Stack()
    stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
    stack.set_transition_duration(1000)

    main_page, percentage_label, health_label = create_main_page()
    second_page = create_second_page()

    stack.add_titled(main_page, "main", "Main Page")
    stack.add_titled(second_page, "More", "Configure Page")

    stack_switcher = Gtk.StackSwitcher()
    stack_switcher.set_stack(stack)
    stack_switcher.set_margin_start(10)
    stack_switcher.set_margin_end(10)
    stack_switcher.set_margin_top(20)
    stack_switcher.set_margin_bottom(10)

    vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    vbox.append(stack)
    vbox.append(stack_switcher)

    win.set_child(vbox)
    win.present()

    GLib.timeout_add_seconds(5, update_battery_status, percentage_label, health_label)

app = Gtk.Application()
app.connect('activate', on_activate)
app.run(None)
