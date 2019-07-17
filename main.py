import serial,glob,sys,time
#TODO replace assert with return null or throw error
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
    :return: time as list of HH MM SS or null
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
    :return: date as list of YYYY MM DD or null
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

def wakeUp(serial):
    """
    :param serial:  serial connection object
    :return: boolean waking up successful
    """
    checkSerialPort(serial)
    serial.write("..AA.".encode())
    assert serial.read(8)=="..er,AA."
    return True

def sleep(serial):
    """
    :param serial:  serial connection object
    :return: boolean sleep successful
    """
    checkSerialPort(serial)
    serial.write("..exit,.".encode())
    assert serial.read(8) == "..ak,exit,."
    return True

def setDate(serial,date):
    """
    :param serial: serial connection object
    :param date: date as string YYYY-MM-DD
    :return: boolean set date successful
    """
    checkSerialPort(serial)
    year,month,day=date.split("-")
    serial.write("..date,{},{},{},.".format(year,month,day).encode())
    assert serial.read(22)=="..ak,date,{},{},{},.".format(year,month,day)
    serial.write("..go,.".encode())
    assert serial.read(6)=="..ok,."
    return True

def setTime(serial,time):
    """
    :param serial: serial connection object
    :param date: time as string HH-MM-SS
    :return: boolean set time successful
    """
    checkSerialPort(serial)
    hour, minute, second = time.split("-")
    serial.write("..time,{},{},{},.".format( hour, minute, second ).encode())
    assert serial.read(20) == "..ak,time,{},{},{},.".format(hour, minute, second )
    serial.write("..go,.".encode())
    assert serial.read(6) == "..ok,."
    return True

def realTime(serial):
    """"
    :param serial: serial connection object
    :return: data obtained
    """
    checkSerialPort(serial)
    serial.write("..real,.".encode())
    assert serial.read(8)=="..,real,"
    return (serial.read(11).split(".")[0]).split(",")[0:2]

def checkData(data):
    if "0xFF"in data:
        return False
    return True

def memoryData(serial):
    """"
    :param serial: serial connection object
    :return: data obtained
    """
    checkSerialPort(serial)
    serial.write("..open,.".encode())
    assert serial.read(11) == "..ak,open,."
    data=[]
    serial.write("..read,.".encode())
    data.append(serial.read(410))
    while checkData(data[-1]):
        serial.write("..read,.".encode())
        data.append(serial.read(410))
    if len(data)==0:
        for i in range(5):
            serial.write("..retry,.".encode())
            temp =serial.read(410)
            if checkData(temp):
                #TODO expose case particular
                memoryData(serial)

    #TODO check for ..retry,.
    return data

def getHeader(serial):
    """
    :param serial: serial connection object
    :return: header as a list of [Type, SerialId, Coeff1, Coeff2, Coeff3, Coeff4, YYYY, MM, DD, HH, MM, SS, Interval, Samples Acquired]
    """
    checkSerialPort(serial)
    serial.write("..head?,.".encode())
    assert serial.read(5) == "..ak,"
    header=serial.read()
    #TODO fix header reading

def setStartTime(serial,startTime):
    """

    :param serial: serial connection object
    :param startTime: start time as YYYY-MM-DD-HH-MM-SS-Interval
    :return: boolean if successfully set start time
    """
    checkSerialPort(serial)
    year,month,day,hour,minute,second,interval=startTime.split("-")
    serial.write("..start,{},{},{},{},{},{},{},.".format(year,month,day,hour,minute,second,interval).encode())
    assert serial.read(31)=="..ak,start,{},{},{},{},{},{},".format(year,month,day,hour,minute,second)
    #TODO read the reamining bits of interval
    serial.write("..go,.".encode())
    assert serial.read(6) == "..ok,."
    return True

#TODO look at memory erase
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