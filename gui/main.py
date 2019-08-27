#!/usr/bin/env python
import base64
import glob
import io
import logging
import serial
import sys
import time
import datetime
from PIL import Image

if sys.version_info[0] >= 3:
    import PySimpleGUI as Sg
else:
    import PySimpleGUI27 as Sg
default_size = (30, 1)
default_size_double = (30, 2)
default_size_half = (default_size[0] // 2, 1)
button_size = (150, 50)
sleep = True
connected = False
ser = None
logging.basicConfig(filename="RDS.log", format='%(asctime)s:%(levelname)s:%(message)s', level=logging.INFO)

logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


class Header:
    Model = None
    SerialId = None
    Coeff1 = None
    Coeff2 = None
    Coeff3 = None
    Coeff4 = None
    Year = None
    Month = None
    Day = None
    Hour = None
    Minute = None
    Second = None
    Interval = None
    Samples = None


header = Header()


def image_file_to_bytes(image64, size):
    image_file = io.BytesIO(base64.b64decode(image64))
    img = Image.open(image_file)
    img.thumbnail(size, Image.ANTIALIAS)
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    imgbytes = bio.getvalue()
    return imgbytes


def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


# noinspection PyUnusedLocal
def ShowMeTheButtons():
    global default_size
    bcolor = '#242834'
    wcolor = ('white', bcolor)

    Sg.ChangeLookAndFeel('DarkTanBlue')
    Sg.SetOptions(auto_size_buttons=False, border_width=0, button_color=Sg.COLOR_SYSTEM_DEFAULT)
    device_selection = [[Sg.Combo(values=serial_ports(), key='_portList_', size=default_size_half),
                         Sg.Button('Connect', image_data=image_file_to_bytes(green_button, button_size), button_color=wcolor, font='Any 15', pad=(0, 0), key='_connect_', size=default_size_half)]]

    device_buttons = [[Sg.Button('Wake Up', image_data=image_file_to_bytes(red_button, button_size), button_color=wcolor, font='Any 15', pad=(0, 4), key='_wakeup_', size=default_size_half),
                       Sg.VSep(pad=(28, 0)),
                       Sg.Button('Get Header', image_data=image_file_to_bytes(blue_button, button_size), button_color=wcolor, font='Any 15', pad=(0, 4), key='_header_', size=default_size_half)]]

    # ------=== Headers Fields ===------
    temp = [[Sg.Text("", size=default_size)]]
    serial_id = [[Sg.Text(header.SerialId, key="_serialID_", size=default_size)]]
    coefficients = [Sg.Text("{} {}\n{} {}".format(header.Coeff1, header.Coeff2, header.Coeff3, header.Coeff4), key="_coefficients_", size=default_size_double)]
    starting_date = [[Sg.Text("{}/{}/{} {}:{}:{}".format(header.Year, header.Month, header.Day, header.Hour, header.Minute, header.Second), key="_starting_date_", size=default_size)]]
    model = [[Sg.Text(header.Model, key="_model_", size=default_size)]]
    samples = [[Sg.Text(header.Samples, key="_sample_", size=default_size)]]
    ending_date = [[Sg.Text("{}/{}/{} {}:{}:{}".format(header.Year, header.Month, header.Day, header.Hour, header.Minute, header.Second), key="_ending_date_", size=default_size)]]
    interval = [[Sg.Text(header.Interval, key="_interval", size=default_size)]]
    # ------=== Display Part ===------
    colums1 = Sg.Column([
        [Sg.Frame('Filename', temp, font='any 18', background_color=bcolor, size=default_size, relief="groove")],
        [Sg.Frame('File Cyclic', temp, font='any 18', background_color=bcolor, size=default_size, relief="groove")],
        [Sg.Frame('Serial No', serial_id, font='any 18', background_color=bcolor, size=default_size, relief="groove")],
        [Sg.Frame('Current Date', temp, font='any 18', background_color=bcolor, size=default_size, relief="groove")],
        [Sg.Frame('Start Time', starting_date, font='any 18', background_color=bcolor, size=default_size, relief="groove")],
        [Sg.Frame('Samples', samples, font='any 18', background_color=bcolor, size=default_size, relief="groove")]
    ])
    set_coefficients = [Sg.Button('Set Coefficients', image_data=image_file_to_bytes(blue_button, button_size),
                  button_color=wcolor, font='Any 15', pad=(0, 6), key='_set_coefficients_', size=default_size)]
    colums2 = Sg.Column([
        [Sg.Frame('Mode', temp, font='any 18', background_color=bcolor, size=default_size, relief="groove")],
        [Sg.Frame('Model', model, font='any 18', background_color=bcolor, size=default_size, relief="groove")],
        [Sg.Frame('Coefficients', [coefficients, set_coefficients], font='any 18', background_color=bcolor, size=default_size_double, relief="groove")],
        [Sg.Frame('End Time', ending_date, font='any 18', background_color=bcolor, size=default_size, relief="groove")],
        [Sg.Frame('Interval', interval, font='any 18', background_color=bcolor, size=default_size, relief="groove")]
    ])
    device_properties = [[colums1, colums2]]

    data_viewer = [[Sg.Frame('Show Data', temp, font='any 18', background_color=bcolor),
                    Sg.Frame('Show Graph', temp, font='any 18', background_color=bcolor)]]

    debug_screen = [[Sg.Frame('Debug panel', temp, font='any 18', background_color=bcolor)]]
    device1 = Sg.Column([[Sg.Frame('Connection to Device', device_selection, font='any 18', background_color=bcolor)]])
    device2 = Sg.Column([[Sg.Frame('Device Controls', device_buttons, font='any 18', background_color=bcolor)]])
    main_screen = [[Sg.Frame("Device", [[device1, device2]], font='any 18', background_color=bcolor)],
                   [Sg.Frame('Device Properties', device_properties, font='any 18', background_color=bcolor)],
                   [Sg.Frame('Data viewer', data_viewer, font='any 18', background_color=bcolor)]]

    layout = [[Sg.TabGroup([
        [Sg.Tab('Tab 1', main_screen, background_color=bcolor, title_color=bcolor), Sg.Tab('Tab 2', debug_screen, background_color=bcolor, title_color=bcolor)]
    ])]]

    window = Sg.Window('Alec Light Intensity',
                       no_titlebar=False,
                       grab_anywhere=True,
                       keep_on_top=True,
                       use_default_focus=False,
                       font='any 15',
                       background_color=bcolor).Layout(layout).Finalize()

    # ---===--- Loop taking in user input --- #

    while True:
        if connected:
            logging.info("Device is connected, toggling on the buttons")
            window.Element('_wakeup_').Update(disabled=False)
            window.Element('_header_').Update(disabled=False)
            window.Element('_set_coefficients_').Update(disabled=False)
        else:
            logging.info("Device is disconnected, toggling off the buttons")
            window.Element('_wakeup_').Update(disabled=True)
            window.Element('_header_').Update(disabled=True)
            window.Element('_set_coefficients_').Update(disabled=True)

        button, values = window.Read()
        logging.info("Available ports are : " + " ".join(serial_ports()))
        window.Element("_portList_").Update(values=serial_ports())
        if button is None:
            break  # exit button clicked
        elif button == "_wakeup_":
            sleep_handler(window)
        elif button == "_header_":
            header_handler(window)
        elif button == "_connect_":
            connect_handler(window, values)
        elif button=="_set_coefficients_":
            set_coeff(window)
        logging.info("Button pressed was: " + button)

def set_coeff(window):
    pass
def header_handler(window):
    global header
    if not sleep:
        result = GetHeader()
        if result is not None:
            result = result[5:len(result) - 2].decode()
            logging.info("Header was successfully received, its content is : " + str(result))
            result = result.split(',')
            header.Model, header.SerialId, header.Coeff1, header.Coeff2, header.Coeff3, header.Coeff4 = result[:6]
            header.Year, header.Month, header.Day, header.Hour, header.Minute, header.Second, header.Interval, header.Samples = map(int, result[6:])
            if header.Year < 1:
                header.Year = 1
            header.Month += 1
            header.Day += 1
            DisplayHeader(window)


def flushEverything():
    if ser is None:
        return
    ser.flush()
    logging.info("Buffer was flush")
    while ser.in_waiting:
        logging.info(str(ser.read(1)) + " was in the reading buffer")
    while ser.out_waiting:
        logging.info(str(ser.write(1)) + " was in the writing buffer")
    ser.reset_input_buffer()
    ser.reset_output_buffer()
    logging.info("Buffer was reseted")


def encodeMessage(data):
    xon = '\x11'
    carriage = '\x0D'
    logging.info(str((xon + xon + data + carriage).encode()) + "was sent")
    return (xon + xon + data + carriage).encode()


def isMatch(result, data):
    encoded_data = encodeMessage(data)
    logging.info(str(encoded_data) + " and " + str(result) + (" succeeded " if encoded_data == result else " failed ") + "to match")
    return encoded_data == result


def checkReadWithMessage():
    time.sleep(0.5)
    ser.flush()
    count = 15
    while count:
        bits = ser.in_waiting
        if bits:
            result = ser.read(bits)
            if result[0:5] == b'\x11\x11ak,':
                logging.info(str(result) + " was read and match the pattern")
                return result
            else:
                logging.critical(str(result) + " was read but didnt match the pattern")
        time.sleep(0.1)
        count -= 1
        logging.info("Reading for new data failed by " + str(15 - count) + "hops")
    return None


def checkRead(data_check):
    """

    :type data_check: str
    """
    time.sleep(0.5)
    ser.flush()
    count = 15
    while count:
        bits = ser.in_waiting
        if bits:
            result = ser.read(bits)
            if isMatch(result, data_check):
                logging.info(str(result) + " was read and matched the confirmation: " + data_check)
                return True
            else:
                logging.critical(str(result) + " was read but didnt match the confirmation:" + data_check)
        time.sleep(0.1)
        count -= 1
        logging.info("Reading for confirmation failed by" + str(15 - count) + "hops")
    return False


def WakeUp():
    """
    :return: None if the serial is not connected, false if the waking up failed and true is succeeded
    """
    global ser
    flushEverything()
    if ser is not None:
        logging.info("Wake up was called on the device")
        ser.write(encodeMessage("AA"))
        return checkRead("er,AA")
    return ser


def Sleep():
    global ser
    flushEverything()
    if ser is not None:
        logging.info("Sleep was called on the device")
        ser.write(encodeMessage("exit,"))
        return checkRead("ak,exit,")
    return ser


def GetHeader():
    global ser
    flushEverything()
    if ser is not None and not sleep:
        logging.info("Get header was called on the device")
        ser.write(encodeMessage("head?,"))
        return checkReadWithMessage()
    logging.critical("Get header was called but the device is asleep or not connected")
    return ser


def calculateFutureDate(year, month, day, hour, minute, second, samples, interval):
    seconds_in_future = (int(samples) - 1) * int(interval) if samples else samples
    logging.info("Trying to find the end date for " + str(seconds_in_future) + " seconds in the future")
    start_date = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
    logging.info("Starting date is : " + str(start_date))
    end_date = start_date + datetime.timedelta(seconds=seconds_in_future)
    logging.info("Ending date is : " + str(end_date))
    return "{}/{}/{} {}:{}:{}".format(end_date.year, end_date.month, end_date.day, end_date.hour, end_date.minute, end_date.second)


def DisplayHeader(window):
    window.Element('_serialID_').Update(header.SerialId)
    window.Element('_coefficients_').Update("{} {}\n{} {}".format(header.Coeff1, header.Coeff2, header.Coeff3, header.Coeff4))
    window.Element('_starting_date_').Update("{}/{}/{} {}:{}:{}".format(header.Year, header.Month, header.Day, header.Hour, header.Minute, header.Second))
    window.Element('_model_').Update(header.Model)
    window.Element('_sample_').Update(header.Samples)
    window.Element('_ending_date_').Update(calculateFutureDate(header.Year, header.Month, header.Day, header.Hour, header.Minute, header.Second, header.Samples, header.Interval))
    window.Element('_interval').Update(header.Interval)


def isOpen():
    global ser
    if ser is not None:
        return ser.isOpen()
    return ser


def Connect(com_port):
    global ser
    if com_port != "":
        try:
            logging.info("Starting to connect to port " + com_port)
            ser = serial.Serial(
                port=com_port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                dsrdtr=True,
                rtscts=True
            )

        except serial.SerialException:
            logging.critical("Failed to connect to port:" + com_port)
        return isOpen()
    logging.critical("No ports were available")
    return None


def Disconnect():
    global ser
    if ser is not None:
        ser.close()
    return isOpen()


def connect_handler(window, values):
    global connected
    logging.info("Starting a connection session")
    if connected:
        result = Disconnect()
        if result is not None and not result:
            window.Element('_connect_').Update("Connect", image_data=image_file_to_bytes(green_button, button_size))
            logging.info("Device was disconnected and the color has been set to green")
            connected = not connected
        else:
            logging.critical("Connection Error")
    else:
        result = Connect(values["_portList_"])
        if result:
            window.Element('_connect_').Update("Disconnect", image_data=image_file_to_bytes(red_button, button_size))
            logging.info("Device was connected and the color has been set to red")
            connected = not connected
        else:
            logging.critical("Connection Error")


def ShowPopUp(*args):
    Sg.Popup(*args,
             title="Error Pop Up",
             button_color=("blue", "white"),
             background_color="red",
             text_color="white",
             button_type=0,
             auto_close=False,
             line_width=60,
             no_titlebar=True,
             grab_anywhere=True,
             keep_on_top=True)


def sleep_handler(window):
    global sleep, connected
    if connected:
        if sleep:
            result = WakeUp()
            if result:
                window.Element('_wakeup_').Update("Sleep", image_data=image_file_to_bytes(green_button, button_size))
                sleep = not sleep
                logging.info("Device has been put into active mode and color has been set to green")
            else:
                logging.critical("Device failed to wake up")
                ShowPopUp('The Device did not respond to the wake up call',
                          'That mean that you should turn off the power switch and turn it on again')
        else:
            result = Sleep()
            if result:
                window.Element('_wakeup_').Update("Wake Up", image_data=image_file_to_bytes(red_button, button_size))
                sleep = not sleep
                logging.info("Device has been put into sleeping mode and color has been set to red")
            else:
                ShowPopUp('The Device did not respond to the sleeping call',
                          'That mean that you might have to redo the process again, this error is undocumented yet')
                logging.critical("Device failed to sleep")
    else:
        logging.critical("Device was not connected while trying to wake up/sleep")


if __name__ == '__main__':
    # To convert your PNG into Base 64:
    #   Go to https://www.base64-image.de/
    #   Drag and drop your PNG image onto the webpage
    #   Choose "Copy image"
    #   Create a string variable name to hold your image
    #   Paste data from webpage as a string
    #   Delete the "header" stuff - up to the data portion (data:image/png;base64,)

    green_button = "iVBORw0KGgoAAAANSUhEUgAAAIwAAAAeCAYAAAD+bvZ2AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAEmUlEQVR4nO2bz08bRxTHv293vF7zwwRwUmOhCDXIbhGplKhKpIpDFakqqMp/EMmoUqX2UqXaQ6Vy4OSeTK/tEeePKOVSqRKqmiiCA6jKpqjhQEgMLihA1l7veqeHYmrA692whLXxfo6e8czovTffmdmZR3BJclaJAhgDMAFgBMAwgA4AMbdtBDQFBQAagFUAKwDmCFhQJ2f23fyZnCokZ5UhAFOIbdwTBp/J6H8Jiu4AoTJILnoZuPtBBJwpvBQBdBl8txe8MAC+MaThn/gDABl1cma90X9tfZXKKYwLZoauPr0vppYk6ts884EHNA/WVgLWk5tl/vzdLHE2raazZr16dQMmmVMSdGlzXrzx26gQe+Hcm0eJ8FthOPd5AE2ElR9EZenjRb7bf/fpZHbjePkJXyVzyi3h8vpc6PYvfRQybGodIzB4S3PcfdwIwfxjYptvDX6qTmYf15YdCYVkTkkIsfVl6dZ8H7G6iuSux4CWh5sMxqPxbasweF2tUZrDgEnlFIZoYUm+/fPoobK4bv3sBuoHfi+JzQo3Qig9/GyF78VuVPc07LBQqGTk1KNRARwwmH0rb2do59zfMai9Q4ZszE/EEX7v4Wjp8XgGwLfAweRKzipDLP63Ghn5XTq3UR7Bb4lq74Bxsn/pz4/KZv5aSk3PrFWlZEoe+Esi00ZZHO3p0eF+C4y/3TcBjS0QHliVzPy1KQBfUHJWiYpdhXz3B7/Kp2zPb38HeMRuSaplf/lOqbIfe4cBGAv15GXBFE/t+GCGtjgu9nChnk3Z3IuNMQATTN4FTAbhoPBk4LztkAg0qtlh8isQYYIBGGGsCDJFVAPjRHg4frgLHN7aOAuCKBYBYIQBGGacgyqswUQPPvW2PZwDHMMMAKgigho43WmJCwTm4kOV/07QDMAq18NXBcmyrxwIzAXHeUniRhggrDIAK5befUcSG90dOUWE101xEHHNjqF3gQMrDMBcudjztSy9wv+OfzMHtnq4ULt/GHCxpzCKlwBgjgFY0Eu9GnVsdJy+R28Gb7R/Og+oze+S3KCXejUCLVTvkn68En3ypcxe163MHezp2dz+S0xAA3SjE5t77/+kprNfVS+PMvvF+OeRyLNTXT56naF+n7LaXmAcHLBXjJfBkQFq5lYy903mirT2XUSspzKNLerV4NzvJSmQGFuKlU5s6kPfq+kfpoCa9zCAML1TToxH2NpNgY4esR0N6jVgfJaYYA9TH4sL2DETi4AwXf3txBNNGdpyHM/7BDdXmIe09jmp3QOm3ny1uIA8EtsldFxX03WeaFZJ5pQPI1ybj1sv+4QDRzqa0/MeJgiYZsIC4QUNbJco8omazi7WltmmmYQtff6yuT0a4bqLLgKFuShoFMaW2L9YFqS7tcpSxdZSyZzCiPNMl6nd7zX2JZnbPwz3bPDgmOQ7RSGEHdZdfi1GspzozRLZaqmmysqV8r1OU5fligHJMiGAg3GXS5YDwZJ0vphEsEhAWWAoiiFoLKyVROkBODLqZPZ0qbLHSeWUKOcnk/GJyFMyfiAu504BHBqIr/LDZHxaUNNZV8n4/wLyI5Bd+hdqngAAAABJRU5ErkJggg=="
    red_button = "iVBORw0KGgoAAAANSUhEUgAAAIwAAAAeCAYAAAD+bvZ2AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAEJklEQVR4nO2bz2vbZhjHP68sy3K8xcHOD5aN0kOQt5AcWsZGIafB2HLof1BwGAy2y+htsBxy8k69b8e4/0TIPbRsjGzQwFDJYYetpYnj0iTIPyS97w6JM6eJY81OIjvS52hJfsXzfvV93l+PICCrljUKLACLwCwwA4wA40H/I2YgqAAOsA1sAWsIsbFk24dBHhbdbli1rNvA8ngq9eCDkREzb5qMJpMkNQ0zkejnxWNCou77NHyffdel0mjwolZz9hqNx0Bpybb/vujZjoIpFwq6BqVbmczDD7NZI5dKXfqLxwwGAtip1/nzzZvmP47zSMFK0ba9TveeoWxZ02OGsX43n58bN80rfVkAIboa3ZWilAq1/UHiVa3G5t7e5r7r3l96/vzF29fP9FTZsj6ZNM21e5OTuaSmBWqk73CHLBhiwZzClZInOzvV3UbjiyXb/q392qmeKlvW9IRpPvt0YiKnBxTLpRB2h4Ut2JA5z2E9KfmlUqnuNhrzS7Z94jQnkSoXCvqorv9+b2pq7lrFMgBEWy6dU7IrJU93d7cOXPdOa0yjty5qSpU+GhubE4Av5fW86TFhj2GiTifBaEIwm83O/VqplIDv4fjjWrWs2++l0/Z8LmfAJYxJYoaKbp/r1uvXzZe1WqFo23+1HGb5/UzG8HocS8QCu9lMZzLGy1ptGfharFrW6LvJ5Ks7+XzH+fNVJ4xYcIPPH9Vq/cB1p3RgYSyVMi9yl65jjLBnOTF9EaT3xgzD3G82F3RgMa3r9JqOjlqMBTPMBMkgaV1HCLGoA7OGEEgpI5saIj9HCzBLNY6WWmZ1YEYBbuwS0SVA30ulUDCjA0fpSKn/lBYx8UTdYYL0dmvIogPbrpS3hKZBhwW7bgGNlryiiSslArZ1YKvmeZ9pF20HdHOcfldqQ3a0qDtMEOqeB0pt6cCa43nfmclkzx0n+uzwsB0q6oIJEn/H9wHWdGDD8TwnK+VIzy0OucNEfbc6CI7nOQix0dpL+imfTn9j9HrkcsgFE/nNzy7xb/o+e/X6z0Xb/ra1l1Q6bDa/yqZSRk8NxoK50Ry6blNBCdrPw1hW6R3D+CF5jstcdUDjMczg4vo+B83mj0XbXoa28zDAiuO6X45o2t0zAuniAP0GPBZMuHSKv1IKx3U3gZXWb2eOaGqa9iyVTOau1abjlDRwKKWou25VKjVfPO+IZouyZX0shFjXE4nAouk34GGf2o8FcxqlFK7vV5VSnxdte7P9WscyE2BdSyTmhBBdU8bQp6RYMCdIKVFSbgL3252lRedCNsvSgZIS4iFCGBfNhGKHuQEoBVI2gUf830K2dlqlsgoeSCFMaHOE40DHghkyjuMtOFqlF+AIeKz6KZV9m3KhMKqUOlOML4Toqxg/Fsu1U1FHAtlGqZNi/GLAYvx/AZDaohvg1aLiAAAAAElFTkSuQmCC"
    blue_button = "iVBORw0KGgoAAAANSUhEUgAAAIwAAAAeCAYAAAD+bvZ2AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAEhklEQVR4nO2bT28bRRiHn9kdr9eOk7ZJ2oYcoEWRkKJUDghxygkJYR/6DXpCQgLJQb0hkUNP5tQbRnDul7BzzxEFR80FKahUQrSlqaMS/1mvvTMcEheT2t5NnHrrrJ+jd2f33ff97W9mPDuCgKTXizNo1oAssAwsAUlgPug1eiGGaTzhLOwDdWAPIXY1uohma6eQrQZp7Fuv9HrpBrChU/YdrkzZpGxIWGAaEJPDhR44ignnSqsNbQUNFw4bcFCri5rzAMjv/JD9c1DTvqVazZWkFiLPXOouC1csUva5x+0fxYSRoDkSzpOKy0HtvtDcKxcy7V6n9ixVOldaJGltivfmV8R0AKHoocLtF8YIGfoBLgz6nzr68f42Tuv2TiH718njr1UqnSt+wnSiaLx/bVaYxmiinBAuJ1SgPYX6/VmFQ+fznUL2l76npnOlRZGKPzRvzs0KY5RiCddhRNgGFzK6h8NqT+E92q/oavNWt9O8StVqriSxY7/Gbs6tjNpZtAi3S4i4Xvr2yNpTtB692MVpf9gZ07ya5mhB3ro+tWKi0J4aTaDHiLBLNlFMz1+FgNhCasV9fJAHvoXjVKXXSzfMlPVbfGHa6t/84hL5Lsmn4O7TQ1cduh+UC5k/Og6zEZuxLOF5QI8XzjejQ0osbIVGXDB+AxDrkmU5h+4G8KVIrxdnjJj5LLk4NWD+7JNRP4lOeLsJ8MI0ntQc1VTXJZq1mG3axoBxi98YQ08EM94E6JNlXNrNprsmgayUINremS8oJoIZcwIIxgQXshJYNoXmyGE6hf//BfwEONHLeBNo0G9ogGUJLBnaQ6izVz3iY8axRwSYdRhHrrAkAYy2whC6f+HfuMOEbVHRlnygpz8e4kpgD8971xzUysezJoIZb4I8vVIA5p4EdlVLf4o5aJbkd8PhEt5rLWOUiKj/cxcA5QnA3JUIim2PbxIMmCX5MlzCg/Shb5KoCybIC9tqxwCKEs1WUxn1Gbxkv5PfdDpD75AiLpgga7+uZ9SBrc5a0k9XqX4V77jMqSs43gkf7+jPg8EFb2LynNTP5ULm685aUr6qrS9sr2qd5XbDrzaH7jEh3//tpmokXAR56MpUOlfMX2u9/C6hen3KObigw1p62EsLUe+SBqXfEZK/Y5e+L/+Y3YCu72FA3DuQqUyiUfnIOCEQv0HR0AmfCCZU+j29QnAQT20jxL2e56bXS4t2q/nwncaL2W7RaJ98jv20OvJd0uv5Vwie2nMVR8ZvlQuZ1z/R7JDOlT5OtJzNhdrz2ZNOc1GJusOcRCF4MjVfcaT9WbmQ2e4+1nebSbzd3Lxae7GSaDd9bzD26Y64YLptoS5t9pOz2660bnc7S4e+mUrnSlJolZ92qncvN15a9iDhjPkkaeIw0JBxDpKX3ZqVvK+FcbqNbN2s5o62ytpu485Us2bbLQer7WIohdTHn3SO95g3coJpCwNlmLjSohGzqcWTdSeWeADky4XM2bbKnmQ1V5rRmjUhyKJZRpzPZvzQ7WX8O9TT8t9mfNgFisBWuZAJtBn/X8BeipVBzcAtAAAAAElFTkSuQmCC"
    ShowMeTheButtons()
