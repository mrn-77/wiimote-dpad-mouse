#!/usr/bin/env python3
import cwiid
import time
import uinput
import subprocess
import sys

# --- CÓDIGOS REALES ---
BTN_A = 8
BTN_B = 4
BTN_HOME = 128
BTN_1 = 2
BTN_2 = 1
BTN_MINUS = 16
BTN_PLUS = 4096
BTN_UP = 2048
BTN_DOWN = 1024
BTN_LEFT = 256
BTN_RIGHT = 512

print("🔌 Presiona 1+2 en el Wiimote...")
try:
    wiimote = cwiid.Wiimote()
except RuntimeError:
    print("❌ No se pudo conectar.")
    sys.exit(1)

# Habilitar reporte de botones + acelerómetro
wiimote.rpt_mode = cwiid.RPT_BTN | cwiid.RPT_ACC
time.sleep(0.5)

print("✅ Conectado.")
print("   - Home = bloquear pantalla (Ctrl+Alt+L)")
print("   - 1 = Pausa (barra espaciadora), 2 = Pantalla completa (F)")
print("   - -/+ = Volumen")
print("   - Sacude el Wiimote hacia adelante para abrir Prime Video en Firefox")
print("   - Apaga el Wiimote con POWER para salir (puede tardar ~2s).")

device = uinput.Device([
    uinput.REL_X, uinput.REL_Y,
    uinput.BTN_LEFT, uinput.BTN_RIGHT,
    uinput.KEY_SPACE, uinput.KEY_F,
    uinput.KEY_LEFTCTRL, uinput.KEY_LEFTALT, uinput.KEY_L
])

step = 15
last_p = last_f = last_minus = last_plus = last_home = False
last_ping_time = time.time()

# Variables para detección de gesto
last_acc = None
gesture_active = False
gesture_reset_time = 0
# Ajusta este umbral según tu sensibilidad (más alto = menos sensible)
THRESHOLD = 35  # valor empírico; prueba entre 30–50

def vol_up():
    subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "0.05+"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def vol_down():
    subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "0.05-"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def lock_screen():
    device.emit(uinput.KEY_LEFTCTRL, 1, syn=False)
    device.emit(uinput.KEY_LEFTALT, 1, syn=False)
    device.emit(uinput.KEY_L, 1, syn=False)
    device.emit(uinput.KEY_L, 0, syn=False)
    device.emit(uinput.KEY_LEFTALT, 0, syn=False)
    device.emit(uinput.KEY_LEFTCTRL, 0)

def open_prime_video():
    print("🎬 Abriendo Prime Video en Firefox...")
    subprocess.Popen(["firefox", "--new-window", "https://www.primevideo.com"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def ping_wiimote(wii):
    """Fuerza una operación de escritura que falle si el Wiimote está apagado."""
    try:
        wii.rpt_mode = cwiid.RPT_BTN | cwiid.RPT_ACC
        return True
    except (cwiid.Error, OSError, IOError):
        return False

try:
    while True:
        # Leer estado del Wiimote
        try:
            state = wiimote.state
            buttons = state.get('buttons', 0)
        except (cwiid.Error, AttributeError):
            print("\n🔌 Error al leer estado. Saliendo...")
            break

        # Ping cada 2 segundos para detectar desconexión
        if time.time() - last_ping_time > 2.0:
            if not ping_wiimote(wiimote):
                print("\n🔌 Wiimote no responde al ping. Saliendo...")
                break
            last_ping_time = time.time()

        # --- Lógica de botones y movimiento (igual que antes) ---
        dx = step if buttons & BTN_RIGHT else (-step if buttons & BTN_LEFT else 0)
        dy = -step if buttons & BTN_UP else (step if buttons & BTN_DOWN else 0)
        if dx or dy:
            device.emit(uinput.REL_X, dx, syn=False)
            device.emit(uinput.REL_Y, dy, syn=True)

        device.emit(uinput.BTN_LEFT, bool(buttons & BTN_B), syn=False)
        device.emit(uinput.BTN_RIGHT, bool(buttons & BTN_A), syn=True)

        if (buttons & BTN_1) and not last_p:
            device.emit(uinput.KEY_SPACE, 1, syn=False)
            device.emit(uinput.KEY_SPACE, 0)
            print("⏸️  Pausa (barra espaciadora)")
        last_p = bool(buttons & BTN_1)

        if (buttons & BTN_2) and not last_f:
            device.emit(uinput.KEY_F, 1, syn=False)
            device.emit(uinput.KEY_F, 0)
            print("🖥️  Pantalla completa (F)")
        last_f = bool(buttons & BTN_2)

        if (buttons & BTN_MINUS) and not last_minus:
            vol_down()
            print("🔉 Volumen -")
        last_minus = bool(buttons & BTN_MINUS)

        if (buttons & BTN_PLUS) and not last_plus:
            vol_up()
            print("🔊 Volumen +")
        last_plus = bool(buttons & BTN_PLUS)

        home_pressed = bool(buttons & BTN_HOME)
        if home_pressed and not last_home:
            lock_screen()
            print("🔒 Bloqueando pantalla (Home)")
        last_home = home_pressed

        # --- Detección de sacudida hacia adelante (eje X) ---
        acc = state.get('acc', (128, 128, 128))
        if last_acc is not None:
            dx_acc = acc[0] - last_acc[0]
            current_time = time.time()

            if dx_acc > THRESHOLD and not gesture_active:
                open_prime_video()
                gesture_active = True
                gesture_reset_time = current_time
            elif gesture_active and (dx_acc < 10 or current_time - gesture_reset_time > 0.6):
                # Reiniciar después de un breve tiempo o cuando se estabiliza
                gesture_active = False

        last_acc = acc

        time.sleep(0.05)

except KeyboardInterrupt:
    print("\n⏹️  Interrupción manual.")
finally:
    try:
        wiimote.close()
    except:
        pass
    device.destroy()
    print("✅ Finalizado.")
