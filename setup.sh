#!/bin/bash

# Update and upgrade the system
sudo apt-get update
sudo apt-get upgrade -y

# Install necessary packages
sudo apt-get install -y python3 python3-pip python3-pandas python3-flask git

# Install Python packages
pip3 install requests python-dateutil qrcode[pil] pillow configparser

# Install the waveshare e-Paper library
git clone https://github.com/waveshare/e-Paper
cd e-Paper/RaspberryPi_JetsonNano/python/ || exit
sudo python3 setup.py install
cd ../../../..

# Prompt the user for the OpenTransportData API key
read -p "Please enter your OpenTransportData API key (or press Enter to use the example config): " api_key

if [ -z "$api_key" ]; then
    api_key="YOUR_API_KEY"
fi

# Create the config.ini file
cat <<EOT > /home/pi/AbfahrtDemo/config.ini
[Settings]
stop_point_ref = YOUR_STOP_POINT_REF
stop_title = YOUR_STOP_TITLE
number_of_results = 5
desired_destinations = all
threshold = 5
api_key = $api_key
EOT

# Create a systemd service file for the application
sudo tee /etc/systemd/system/abfahrtdemo.service > /dev/null <<EOT
[Unit]
Description=Start display.py and app.py at boot
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/AbfahrtDemo/start_scripts.sh
WorkingDirectory=/home/pi/AbfahrtDemo
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOT

# Create the start script
cat <<EOT > /home/pi/AbfahrtDemo/start_scripts.sh
#!/bin/bash
python3 /home/pi/AbfahrtDemo/display.py &
python3 /home/pi/AbfahrtDemo/app.py &
EOT

# Make the start script executable
chmod +x /home/pi/AbfahrtDemo/start_scripts.sh

# Reload systemd to apply the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable abfahrtdemo.service

echo "Setup complete. You can start the service with 'sudo systemctl start abfahrtdemo.service'"
