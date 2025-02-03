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
            result = subprocess.run("zenity --password | sudo -S echo 'Sudo password accepted.'", shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print("Failed to get sudo password")
                return None
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
            subprocess.run(["sudo", "apt", "update"], input=sudo_password + "\n", text=True, check=True)
            subprocess.run(["sudo", "apt", "upgrade", "-y"], input=sudo_password + "\n", text=True, check=True)
        elif 'fedora' in distro_name:
            subprocess.run(["sudo", "dnf", "update", "-y"], input=sudo_password + "\n", text=True, check=True)
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

    battery_icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "battery_icon.png")
    battery_icon = Gtk.Image.new_from_file(battery_icon_path)
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
    
    # Subheader
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


def on_brightness_changed(slider):
    value = int(slider.get_value())
    try:
        with open('/sys/class/backlight/intel_backlight/brightness', 'w') as f:
            f.write(str(value))
        print(f"Brightness changed to: {value}%")
    except Exception as e:
        print(f"Failed to change brightness: {e}")

def on_volume_changed(slider):
    value = int(slider.get_value())
    try:
        # Check if PipeWire is running
        result = subprocess.run(["pactl", "info"], capture_output=True, text=True, check=True)
        if "PipeWire" in result.stdout:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{value}%"], check=True)
        else:
            subprocess.run(["amixer", "set", "Master", f"{value}%", "unmute"], check=True)
        print(f"Volume changed to: {value}%")
    except subprocess.CalledProcessError as e:
        print(f"Failed to change volume: {e}")

def get_current_volume():
    try:
        # Check if PipeWire is running
        result = subprocess.run(["pactl", "info"], capture_output=True, text=True, check=True)
        if "PipeWire" in result.stdout:
            result = subprocess.run(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], capture_output=True, text=True, check=True)
            volume = int(result.stdout.split('/')[1].strip().replace('%', ''))
        else:
            result = subprocess.run(["amixer", "get", "Master"], capture_output=True, text=True, check=True)
            volume = int(result.stdout.split('[')[1].split('%')[0])
        return volume
    except subprocess.CalledProcessError as e:
        print(f"Failed to get current volume: {e}")
        return 50  # Default to 50% if there's an error

def on_keyboard_brightness_changed(slider):
    value = int(slider.get_value())
    try:
        with open('/sys/class/leds/asus::kbd_backlight/brightness', 'w') as f:
            f.write(str(value))
        print(f"Keyboard brightness changed to: {value}%")
    except Exception as e:
        print(f"Failed to change keyboard brightness: {e}")

def on_microphone_changed(slider):
    value = int(slider.get_value())
    try:
        # Check if PipeWire is running
        result = subprocess.run(["pactl", "info"], capture_output=True, text=True, check=True)
        if "PipeWire" in result.stdout:
            subprocess.run(["pactl", "set-source-volume", "@DEFAULT_SOURCE@", f"{value}%"], check=True)
        else:
            subprocess.run(["amixer", "set", "Capture", f"{value}%", "unmute"], check=True)
        print(f"Microphone volume changed to: {value}%")
    except subprocess.CalledProcessError as e:
        print(f"Failed to change microphone volume: {e}")

def get_current_microphone_volume():
    try:
        # Check if PipeWire is running
        result = subprocess.run(["pactl", "info"], capture_output=True, text=True, check=True)
        if "PipeWire" in result.stdout:
            result = subprocess.run(["pactl", "get-source-volume", "@DEFAULT_SOURCE@"], capture_output=True, text=True, check=True)
            volume = int(result.stdout.split('/')[1].strip().replace('%', ''))
        else:
            result = subprocess.run(["amixer", "get", "Capture"], capture_output=True, text=True, check=True)
            volume = int(result.stdout.split('[')[1].split('%')[0])
        return volume
    except subprocess.CalledProcessError as e:
        print(f"Failed to get current microphone volume: {e}")
        return 50  # Default to 50% if there's an error

def wifi_toggle(button):
    try:
        subprocess.run(["nmcli", "radio", "wifi", "on" if button.get_label() == "Wifi Off" else "off"], check=True)
        button.set_label("Wifi Off" if button.get_label() == "Wifi On" else "Wifi On")
    except subprocess.CalledProcessError as e:
        print(f"Failed to toggle wifi: {e}")

def bluetooth_toggle(button):
    try:
        subprocess.run(["bluetoothctl", "power", "on" if button.get_label() == "Bluetooth Off" else "off"], check=True)
        button.set_label("Bluetooth Off" if button.get_label() == "Bluetooth On" else "Bluetooth On")
    except subprocess.CalledProcessError as e:
        print(f"Failed to toggle bluetooth: {e}")

def airplane_toggle(button):
    try:
        subprocess.run(["nmcli", "radio", "all", "on" if button.get_label() == "Airplane Off" else "off"], check=True)
        button.set_label("Airplane Off" if button.get_label() == "Airplane On" else "Airplane On")
    except subprocess.CalledProcessError as e:
        print(f"Failed to toggle airplane mode: {e}")

def mic_toggle(button):
    try:
        # Check if PipeWire is running
        result = subprocess.run(["pactl", "info"], capture_output=True, text=True, check=True)
        if "PipeWire" in result.stdout:
            subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"], check=True)
        else:
            subprocess.run(["amixer", "set", "Capture", "toggle"], check=True)
        button.set_label("Mic Off" if button.get_label() == "Mic On" else "Mic On")
    except subprocess.CalledProcessError as e:
        print(f"Failed to toggle microphone: {e}")



def create_second_page():
    scrolled_window = Gtk.ScrolledWindow()
    scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scrolled_window.set_min_content_height(400)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    scrolled_window.set_child(box)

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

    # Add horizontal separator
    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    separator.set_margin_start(20)
    separator.set_margin_end(20)
    separator.set_margin_top(10)
    separator.set_size_request(-1, 8)  # Increase the height/thickness of the separator
    grid.attach(separator, 0, 2, 2, 1)

    box.append(grid)

    # Brightness Slider
    brightness_label = Gtk.Label(label="Brightness (In progress)")
    brightness_label.set_halign(Gtk.Align.START)
    grid.attach(brightness_label, 0, 3, 1, 1)

    brightness_adjustment = Gtk.Adjustment(value=50, lower=0, upper=100, step_increment=1, page_increment=10, page_size=0)
    brightness_slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=brightness_adjustment)
    brightness_slider.set_digits(0)
    brightness_slider.set_hexpand(True)
    brightness_slider.set_valign(Gtk.Align.CENTER)
    brightness_slider.connect("value-changed", on_brightness_changed)
    grid.attach(brightness_slider, 1, 3, 1, 1)

    # Keyboard Brightness Slider
    keyboard_brightness_label = Gtk.Label(label="Keyboard Brightness(In progress)")
    keyboard_brightness_label.set_halign(Gtk.Align.START)
    grid.attach(keyboard_brightness_label, 0, 4, 1, 1)
    
    keyboard_brightness_adjustment = Gtk.Adjustment(value=50, lower=0, upper=100, step_increment=1, page_increment=10, page_size=0)
    keyboard_brightness_slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=keyboard_brightness_adjustment)
    keyboard_brightness_slider.set_digits(0)
    keyboard_brightness_slider.set_hexpand(True)
    keyboard_brightness_slider.set_valign(Gtk.Align.CENTER)
    keyboard_brightness_slider.connect("value-changed", on_keyboard_brightness_changed)
    grid.attach(keyboard_brightness_slider, 1, 4, 1, 1)

    # Volume Slider
    volume_label = Gtk.Label(label="Volume")
    volume_label.set_halign(Gtk.Align.START)
    grid.attach(volume_label, 0, 5, 1, 1)
    
    current_volume = get_current_volume()
    volume_adjustment = Gtk.Adjustment(value=current_volume, lower=0, upper=100, step_increment=1, page_increment=10, page_size=0)
    volume_slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=volume_adjustment)
    volume_slider.set_digits(0)
    volume_slider.set_hexpand(True)
    volume_slider.set_valign(Gtk.Align.CENTER)
    volume_slider.connect("value-changed", on_volume_changed)
    grid.attach(volume_slider, 1, 5, 1, 1)

    # Microphone Slider
    microphone_label = Gtk.Label(label="Microphone (In progress)")
    microphone_label.set_halign(Gtk.Align.START)
    grid.attach(microphone_label, 0, 6, 1, 1)

    current_microphone_volume = get_current_microphone_volume()
    microphone_adjustment = Gtk.Adjustment(value=current_microphone_volume, lower=0, upper=100, step_increment=1, page_increment=10, page_size=0)
    microphone_slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=microphone_adjustment)
    microphone_slider.set_digits(0)
    microphone_slider.set_hexpand(True)
    microphone_slider.set_valign(Gtk.Align.CENTER)
    microphone_slider.connect("value-changed", on_microphone_changed)
    grid.attach(microphone_slider, 1, 6, 1, 1)

    box.append(grid)

    # Add horizontal separator
    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    separator.set_margin_start(20)
    separator.set_margin_end(20)
    separator.set_margin_top(10)
    separator.set_margin_bottom(10)
    separator.set_size_request(-1, 8)  # Increase the height/thickness of the separator
    box.append(separator)

    # Subheader
    subheader_label = Gtk.Label(label="Quick Toggles (In Progress)")
    subheader_label.set_halign(Gtk.Align.START)
    subheader_label.set_margin_start(20)
    subheader_label.set_margin_top(6)
    subheader_label.set_margin_bottom(2)
    box.append(subheader_label)

    # Add a row of 5 square buttons with SVG icons
    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    button_box.set_halign(Gtk.Align.CENTER)
    
    # Add SVG icons inside the buttons
    svg_icons = ["wifi.svg", "bluetooth.svg", "airplane.svg", "mic.svg", "about.svg"]
    button_functions = [wifi_toggle, bluetooth_toggle, airplane_toggle, mic_toggle, about_dialog]
    button_labels = ["Wifi", "Bluetooth", "Airplane", "Mic", "About"]

    for icon_name, func, label in zip(svg_icons, button_functions, button_labels):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        button = Gtk.Button()
        button.set_size_request(50, 50)  # Set the size to make them square

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), icon_name)
        icon = Gtk.Image.new_from_file(icon_path)
        button.set_child(icon)
        button.connect("clicked", func)

        label_widget = Gtk.Label(label=label)
        label_widget.set_halign(Gtk.Align.CENTER)

        vbox.append(button)
        vbox.append(label_widget)
        button_box.append(vbox)

    box.append(button_box)

    # Add horizontal separator
    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    separator.set_margin_start(20)
    separator.set_margin_end(20)
    separator.set_margin_top(10)
    separator.set_margin_bottom(10)
    separator.set_size_request(-1, 8)  # Increase the height/thickness of the separator
    box.append(separator)

    # Subheader
    subheader_label = Gtk.Label(label="Fan and Temperature (In Progress)")
    subheader_label.set_halign(Gtk.Align.START)
    subheader_label.set_margin_start(20)
    subheader_label.set_margin_top(6)
    subheader_label.set_margin_bottom(2)
    box.append(subheader_label)

    # Fan and Temperature Grid
    fan_temp_grid = Gtk.Grid()
    fan_temp_grid.set_column_spacing(50)
    fan_temp_grid.set_row_spacing(20)
    fan_temp_grid.set_margin_start(20)
    fan_temp_grid.set_margin_end(20)
    fan_temp_grid.set_margin_top(10)
    fan_temp_grid.set_margin_bottom(10)
    fan_temp_grid.set_halign(Gtk.Align.CENTER)

    # CPU Temperature
    cpu_temp_label = Gtk.Label(label="CPU Temperature:")
    cpu_temp_value = Gtk.Label(label="N/A")
    fan_temp_grid.attach(cpu_temp_label, 0, 0, 1, 1)
    fan_temp_grid.attach(cpu_temp_value, 1, 0, 1, 1)

    # GPU Temperature
    gpu_temp_label = Gtk.Label(label="GPU Temperature:")
    gpu_temp_value = Gtk.Label(label="N/A")
    fan_temp_grid.attach(gpu_temp_label, 0, 1, 1, 1)
    fan_temp_grid.attach(gpu_temp_value, 1, 1, 1, 1)

    # CPU Fan Speed
    cpu_fan_label = Gtk.Label(label="CPU Fan Speed:")
    cpu_fan_value = Gtk.Label(label="N/A")
    fan_temp_grid.attach(cpu_fan_label, 0, 2, 1, 1)
    fan_temp_grid.attach(cpu_fan_value, 1, 2, 1, 1)

    # GPU Fan Speed
    gpu_fan_label = Gtk.Label(label="GPU Fan Speed:")
    gpu_fan_value = Gtk.Label(label="N/A")
    fan_temp_grid.attach(gpu_fan_label, 0, 3, 1, 1)
    fan_temp_grid.attach(gpu_fan_value, 1, 3, 1, 1)

    box.append(fan_temp_grid)

    def update_fan_temp():
        try:
            # Fetch CPU temperature using sensors
            cpu_temp_result = subprocess.run(["sensors"], capture_output=True, text=True, check=True)
            cpu_temp_lines = [line for line in cpu_temp_result.stdout.split('\n') if 'Core 0' in line]
            if cpu_temp_lines:
                cpu_temp = cpu_temp_lines[0].split()[2]
                cpu_temp_value.set_text(cpu_temp)

            # Fetch GPU temperature using sensors
            gpu_temp_lines = [line for line in cpu_temp_result.stdout.split('\n') if 'temp1' in line]
            if gpu_temp_lines:
                gpu_temp = gpu_temp_lines[0].split()[1]
                gpu_temp_value.set_text(gpu_temp)

            # Fetch CPU fan speed using sensors
            cpu_fan_result = subprocess.run(["sensors"], capture_output=True, text=True, check=True)
            cpu_fan_lines = [line for line in cpu_fan_result.stdout.split('\n') if 'fan1' in line]
            if cpu_fan_lines:
                cpu_fan_speed = cpu_fan_lines[0].split()[1]
                cpu_fan_value.set_text(f"{cpu_fan_speed} RPM")

            # Fetch GPU fan speed using sensors
            gpu_fan_lines = [line for line in cpu_fan_result.stdout.split('\n') if 'fan2' in line]
            if gpu_fan_lines:
                gpu_fan_speed = gpu_fan_lines[0].split()[1]
                gpu_fan_value.set_text(f"{gpu_fan_speed} RPM")
        except Exception as e:
            print(f"Failed to update fan and temperature: {e}")

        return True  # Continue calling this function

    GLib.timeout_add_seconds(5, update_fan_temp)

    
    return scrolled_window

def about_dialog(_):
    try:
        # Check if fastfetch is installed
        subprocess.run(["fastfetch", "--version"], check=True, capture_output=True, text=True)
        fetch_command = ["fastfetch"]
    except subprocess.CalledProcessError:
        try:
            # Check if neofetch is installed
            subprocess.run(["neofetch", "--version"], check=True, capture_output=True, text=True)
            fetch_command = ["neofetch", "--stdout"]
        except subprocess.CalledProcessError:
            fetch_command = None

    if fetch_command:
        try:
            result = subprocess.run(fetch_command, capture_output=True, text=True, check=True)
            message = result.stdout
        except subprocess.CalledProcessError as e:
            message = f"Failed to fetch system information: {e}"
    else:
        distro_name = distro.name()
        host_name = os.uname().nodename
        user_name = os.getlogin()
        cpu_info = subprocess.run(["lscpu"], capture_output=True, text=True).stdout.split('\n')[0]
        memory_info = subprocess.run(["free", "-h"], capture_output=True, text=True).stdout.split('\n')[1]
        message = f"Distro: {distro_name}\nHost: {host_name}\nUser: {user_name}\nCPU: {cpu_info}\nMemory: {memory_info}"

    try:
        subprocess.run(["zenity", "--info", "--title", "System Information", "--text", message, "--width=600", "--height=400"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to show system information: {e}")

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
