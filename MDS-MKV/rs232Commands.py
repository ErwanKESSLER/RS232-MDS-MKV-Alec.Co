import logging, serial, time


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
    Interval = 0
    Samples = None
    currentDate = None
    dateTimeNow = None


class Device:
    sleep = True
    connected = False
    serial_device = None
    header = Header()


device = Device()


def flushEverything():
    if device.serial_device is None or device.sleep or not device.connected:
        logging.critical("The device is not usable and cannot be flushed")
        return
    device.serial_device.flush()
    logging.info("Buffer was flush")
    while device.serial_device.in_waiting:
        logging.info(str(device.serial_device.read(1)) + " was in the reading buffer")
    while device.serial_device.out_waiting:
        logging.info(str(device.serial_device.write(1)) + " was in the writing buffer")
    device.serial_device.reset_input_buffer()
    device.serial_device.reset_output_buffer()
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


def SendMessage(msg):
    global device
    flushEverything()
    if device.serial_device is not None and not device.sleep and device.connected:
        logging.info("Send message was called on the device with : " + msg)
        device.serial_device.write(encodeMessage(msg))
        if checkReadWithMessage('ak'):
            time.sleep(0.5)
            logging.info("Message {} was acknowledged".format(msg))
            device.serial_device.write(encodeMessage("go,"))
            time.sleep(0.5)
            if checkReadWithMessage('ok'):
                logging.info("Device started the command")
                return True
            logging.critical("Device didnt want to start the command")
            return False
        else:
            logging.critical("Message {} was not acknowledged".format(msg))
            return False
    logging.critical("Send message was called but the device is asleep or not connected")
    return device.serial_device


def SendCommand(msg, ak):
    global device
    flushEverything()
    if device.serial_device is not None and not device.sleep and device.connected:
        logging.info("Send command was called on the device with : " + msg)
        device.serial_device.write(encodeMessage(msg))
        result = checkReadWithMessage(ak)
        if result:
            logging.info("Command {} was acknowledged with : {}".format(msg, result))
            return result
        else:
            logging.critical("Command {} was not acknowledged".format(msg))
            return False
    logging.critical("Send Command was called but the device is asleep or not connected")
    return device.serial_device


def checkReadWithMessage(msg):
    time.sleep(0.5)
    device.serial_device.flush()
    count = 15
    while count:
        bits = device.serial_device.in_waiting
        if bits:
            result = device.serial_device.read(bits)
            if result[0:(3 + len(msg))-(1 if msg=="" else 0)] == b'\x11\x11' + msg.encode() + (b',' if msg != "" else b''):
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
    device.serial_device.flush()
    count = 15
    while count:
        bits = device.serial_device.in_waiting
        if bits:
            result = device.serial_device.read(bits)
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
    global device
    flushEverything()
    if device.serial_device is not None:
        logging.info("Wake up was called on the device")
        device.serial_device.write(encodeMessage("AA"))
        return checkRead("er,AA")
    return device.serial_device


def Sleep():
    global device
    flushEverything()
    if device.serial_device is not None:
        logging.info("Sleep was called on the device")
        device.serial_device.write(encodeMessage("exit,"))
        return checkRead("ak,exit,")
    return device.serial_device


def GetHeader():
    global device
    flushEverything()
    if device.serial_device is not None and not device.sleep and device.connected:
        logging.info("Get header was called on the device")
        device.serial_device.write(encodeMessage("head?,"))
        return checkReadWithMessage('ak')
    logging.critical("Get header was called but the device is asleep or not connected")
    return device.serial_device


def GetCurrentDate():
    global device
    flushEverything()
    if device.serial_device is not None and not device.sleep and device.connected:
        logging.info("Get Current Date was called on the device")
        device.serial_device.write(encodeMessage("date?,"))
        return checkReadWithMessage('date')
    logging.critical("Get Current Date was called but the device is asleep or not connected")
    return device.serial_device


def GetCurrentTime():
    global device
    flushEverything()
    if device.serial_device is not None and not device.sleep and device.connected:
        logging.info("Get Current Time was called on the device")
        device.serial_device.write(encodeMessage("time?,"))
        return checkReadWithMessage('time')
    logging.critical("Get Current Time was called but the device is asleep or not connected")
    return device.serial_device


def isOpen():
    global device
    if device.serial_device is not None:
        return device.serial_device.isOpen()
    return device.serial_device


def Connect(com_port):
    global device
    if com_port != "":
        try:
            logging.info("Starting to connect to port " + com_port)
            device.serial_device = serial.Serial(
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
    global device
    if device.serial_device is not None:
        device.serial_device.close()
        ser = None
    return isOpen()
