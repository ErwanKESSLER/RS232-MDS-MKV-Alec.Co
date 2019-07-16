import serial,glob,sys,time
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


def checkSerialPort(serial):
    serial.isOpen()

def ReadTime(serial):
    """
    :param serial: serial connection object
    :return: time as list of HH MM SS
    """
    checkSerialPort(serial)
    serial.write("..date?,.".encode())
    assert serial.read(1)=="."
    assert serial.read(1)=="."
    assert serial.read(1)=="t"
    assert serial.read(1)=="i"
    assert serial.read(1)=="m"
    assert serial.read(1)=="e"
    assert serial.read(1)==","
    current=[serial.read(1)]

    while current[-1]!=".":
        current.append(serial.read(1))
    current.pop()
    return "".join(current).split(",")


def ReadDate(serial):
    """
    :param serial: serial connection object
    :return: date as list of YYYY MM DD
    """
    checkSerialPort(serial)
    serial.write("..date?,.".encode())
    assert serial.read(1) == "."
    assert serial.read(1) == "."
    assert serial.read(1) == "d"
    assert serial.read(1) == "a"
    assert serial.read(1) == "t"
    assert serial.read(1) == "e"
    assert serial.read(1) == ","
    current = [serial.read(1)]

    while current[-1] != ".":
        current.append(serial.read(1))
    current.pop()
    return "".join(current).split(",")


def main():
    res=serial_ports()
    if len(res)!=1:
        print("error")


    ser = serial.Serial(
            port="COM6",
            baudrate=9600,
            bytesize=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stopbits=serial.STOPBITS_ONE
        )
    ser.isOpen()







    except Exception as e1:
        print("error communicating...: " + str(e1))
        ser.close()


main()