# wiimote-dpad-mouse
Script to use a WiiMote as a mouse on linux (Ubuntu 24.04)

## Install dependencies
sudo apt update
sudo apt-get install wminput python3-cwiid lswm
sudo apt-get install python3-pynput
sudo apt-get install python3-uinput

### Configuration
sudo usermod -aG input $USER
sudo usermod -aG uinput $USER
modprobe uinput
echo "uinput" | sudo tee /etc/modules-load.d/uinput.conf
sudo groupadd uinput
sudo usermod -aG uinput $USER
echo 'KERNEL=="uinput", MODE="0660", GROUP="uinput", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-uinput.rules
sudo udevadm control --reload-rules && sudo udevadm trigger

