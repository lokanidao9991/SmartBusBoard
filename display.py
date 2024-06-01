#!/usr/bin/python
# -*- coding:utf-8 -*-
import sys
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from dateutil.parser import parse
import time
from PIL import Image, ImageDraw, ImageFont
import qrcode
import logging
from zoneinfo import ZoneInfo  # Python 3.9+ timezone handling
import configparser
import socket

# Setup directories for images and libraries
picdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'pic')
libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

from waveshare_epd import epd2in13_V4

logging.basicConfig(level=logging.DEBUG)

# API-URL
url = "https://api.opentransportdata.swiss/trias2020"


def load_configuration():
    """Loads the configuration from config.ini file"""
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')
    config.read(config_path)
    return {
        'STOP_POINT_REF': config['Settings']['stop_point_ref'],
        'NUMBER_OF_RESULTS': int(config['Settings']['number_of_results']),
        'desired_destinations': config['Settings']['desired_destinations'].split(','),
        'THRESHOLD': int(config['Settings']['threshold']),
        'STOP_TITLE': config['Settings']['stop_title'],
        'API_KEY': config['Settings']['api_key']
    }


def get_current_datetime_utc():
    """Gets the current UTC datetime in the required format"""
    now = datetime.now(timezone.utc)
    milliseconds = now.microsecond // 1000
    return now.strftime('%Y-%m-%dT%H:%M:%S.') + str(int(milliseconds)) + 'Z'


def get_departure_time_zurich():
    """Gets the current time in Zurich timezone"""
    zurich_timezone = ZoneInfo("Europe/Zurich")
    current_datetime_zurich = datetime.now(zurich_timezone)
    return current_datetime_zurich.strftime('%Y-%m-%dT%H:%M:%S')


def get_departures(config):
    """Fetches departure information based on the configuration"""
    STOP_POINT_REF = config['STOP_POINT_REF']
    NUMBER_OF_RESULTS = config['NUMBER_OF_RESULTS']
    desired_destinations = config['desired_destinations']
    THRESHOLD = config['THRESHOLD']
    API_KEY = config['API_KEY']

    current_datetime_utc = get_current_datetime_utc()
    current_departure_time_zurich = get_departure_time_zurich()
    data = f'''
        <?xml version="1.0" encoding="UTF-8"?>
        <Trias version="1.1" xmlns="http://www.vdv.de/trias" xmlns:siri="http://www.siri.org.uk/siri" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <ServiceRequest>
                <siri:RequestTimestamp>{current_datetime_utc}</siri:RequestTimestamp>
                <siri:RequestorRef>API-Explorer</siri:RequestorRef>
                <RequestPayload>
                    <StopEventRequest>
                        <Location>
                            <LocationRef>
                                <StopPointRef>{STOP_POINT_REF}</StopPointRef>
                            </LocationRef>
                            <DepArrTime>{current_departure_time_zurich}</DepArrTime>
                        </Location>
                        <Params>
                            <NumberOfResults>{NUMBER_OF_RESULTS}</NumberOfResults>
                            <StopEventType>departure</StopEventType>
                            <IncludePreviousCalls>false</IncludePreviousCalls>
                            <IncludeOnwardCalls>false</IncludeOnwardCalls>
                            <IncludeRealtimeData>true</IncludeRealtimeData>
                        </Params>
                    </StopEventRequest>
                </RequestPayload>
            </ServiceRequest>
        </Trias>
        '''

    headers = {
        "Authorization": API_KEY,
        "Content-Type": "text/XML"
    }

    response = requests.post(url, headers=headers, data=data)
    departures = []
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        for stop_event_result in root.findall('.//{http://www.vdv.de/trias}StopEventResult'):
            line = "Unknown Line"
            destination = "Unknown Destination"
            departure_time = None  # Initialize as None

            line_node = stop_event_result.find(
                './/{http://www.vdv.de/trias}PublishedLineName/{http://www.vdv.de/trias}Text')
            destination_node = stop_event_result.find(
                './/{http://www.vdv.de/trias}DestinationText/{http://www.vdv.de/trias}Text')
            departure_time_node = stop_event_result.find(
                './/{http://www.vdv.de/trias}ServiceDeparture/{http://www.vdv.de/trias}EstimatedTime')

            if line_node is not None:
                line = line_node.text
            if destination_node is not None:
                destination = destination_node.text
            if departure_time_node is not None:
                departure_time_str = departure_time_node.text
                departure_time = parse(departure_time_str)

                now_utc = datetime.now(timezone.utc)
                minutes_until_departure = int((departure_time - now_utc).total_seconds() / 60)

                # Include departure only if it meets criteria
                if minutes_until_departure >= THRESHOLD and (
                        "all" in desired_destinations or "All" in desired_destinations or any(dest in destination for dest in desired_destinations)):
                    departures.append((line, destination, minutes_until_departure))

    else:
        logging.error("Failed to fetch departures: HTTP {}".format(response.status_code))

    departures = sorted(departures, key=lambda x: x[2])[:5]  # Sort and limit to 5 results
    return departures


def get_ip_address():
    """Gets the local IP address"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # This connection does not need to be successful
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception:
        ip_address = "127.0.0.1"
    finally:
        s.close()
    return ip_address


def truncate_text(text, max_length=25):
    """Truncate text to a maximum length and add ellipsis if necessary."""
    if len(text) > max_length:
        return text[:max_length - 3] + '...'
    return text


def display_departures(departures):
    """Displays departures on the e-Paper screen"""
    global update_count, font20
    try:
        epd = epd2in13_V4.EPD()
        epd.init()  # Initialize the display
        epd.Clear()  # Clear the display

        config = load_configuration()  # Load configuration

        # Fonts
        try:
            font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 12)
            font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
            font20 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 20)
        except IOError:
            logging.info("Using default font")
            font = ImageFont.load_default()
            font24 = ImageFont.load_default()

        # Create a new blank image for black content
        HBlackimage = Image.new('1', (epd.height, epd.width), 255)
        draw = ImageDraw.Draw(HBlackimage)

        # Display the current time on the first line to the right
        current_time = time.strftime('%H:%M:%S')
        time_x = 155  # Adjust X position based on your display's dimensions
        time_y = 0  # Adjust Y position as needed
        draw.text((time_x, time_y), current_time, font=font24, fill=0)

        # Header
        stop_text = truncate_text(config['STOP_TITLE'], 15)
        stop_title = stop_text
        draw.text((0, 3), stop_title, font=font20, fill=0)
        draw.text((0, 18), "------------------------------------------------------------------", font=font, fill=0)

        # Starting Y position for departures
        y = 35

        # Absolute X positions for line, destination, and minutes
        x_line = 0  # Line starts at 5 pixels from the left
        x_destination = 40  # Destination starts at 30 pixels from the left
        x_minutes = 190  # Minutes start at 190 pixels from the left, ensuring it's right-aligned

        for line, destination, minutes_until_departure in departures:
            # Draw line number
            line_text = f"[{line}]"
            draw.text((x_line, y), line_text, font=font, fill=0)

            # Draw destination (shortened if necessary to fit)
            destination_text = truncate_text(destination, 25)
            draw.text((x_destination, y), destination_text, font=font, fill=0)

            # Draw minutes until departure
            minutes_text = f"{minutes_until_departure}'"
            draw.text((x_minutes, y), minutes_text, font=font, fill=0)

            y += 18  # Increment Y position for the next entry

        # Generate QR code for the frontend URL
        ip_address = get_ip_address()
        frontend_url = f"http://{ip_address}:5000"
        logging.info(f"Frontend URL: {frontend_url}")
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(frontend_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill='black', back_color='white')

        # Resize QR code to fit on the display
        qr_img = qr_img.resize((50, 50), Image.LANCZOS)

        # Combine the QR code image with the main image using absolute positions
        qr_position = (205, 75)  # Absolute position on the display
        HBlackimage.paste(qr_img, qr_position)

        # Debugging: Save the entire image to ensure the QR code is inserted
        image_save_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "display_image.png")
        HBlackimage.save(image_save_path)
        logging.info(f"Display image saved to {image_save_path}")

        # Display the image on the e-Paper
        epd.display(epd.getbuffer(HBlackimage))

    except IOError as e:
        logging.info(e)
    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        epd2in13_V4.epdconfig.module_exit()
        sys.exit()


def display_message(text):
    """Displays a message on the e-Paper screen"""
    try:
        epd = epd2in13_V4.EPD()  # Initialize the display
        epd.init()  # Initialize the display library
        epd.Clear()  # Clear the display content

        # Prepare font and drawing context
        try:
            font = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
        except IOError:
            logging.info("Using default font")
            font = ImageFont.load_default()

        image = Image.new('1', (epd.width, epd.height), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(image)

        # Position the text in the center of the screen
        w, h = draw.textsize(text, font=font)
        draw.text(((epd.width - w) / 2, (epd.height - h) / 2), text, font=font, fill=0)

        epd.display(epd.getbuffer(image))  # Show the image
    except IOError as e:
        logging.info(e)
    except KeyboardInterrupt:
        logging.info("ctrl + c:")
        epd2in13_V4.epdconfig.module_exit()
        sys.exit()


def main():
    """Main function to manage the display updates"""
    while True:
        config = load_configuration()  # Load configuration at the beginning of each loop
        now = datetime.now()
        # If it's between 01:00 and 07:00
        if 1 <= now.hour < 7:
            # Calculate hours to sleep until 07:00
            hours_to_sleep = 7 - now.hour if now.hour > 1 else 6
            logging.info(f"After 01:00 ({now.hour}:{now.minute}), script sleeps for {hours_to_sleep} hours.")
            display_message("Good Night =)")
            time.sleep(hours_to_sleep * 3600)  # Sleep for the calculated number of hours
        else:
            departures = get_departures(config)
            display_departures(departures)
            time.sleep(30)  # API allows requests every 30 seconds


if __name__ == "__main__":
    main()
