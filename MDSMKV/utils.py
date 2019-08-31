import serial, glob, sys, io, base64, datetime, logging
from PIL import Image
from calendar import monthrange


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


def image_file_to_bytes(image64, size):
    image_file = io.BytesIO(base64.b64decode(image64))
    img = Image.open(image_file)
    img.thumbnail(size, Image.ANTIALIAS)
    bio = io.BytesIO()
    img.save(bio, format='PNG')
    imgbytes = bio.getvalue()
    return imgbytes


def calculateFutureDate(year, month, day, hour, minute, second, samples, interval):
    if None not in (year, month, day, hour, minute, second, samples, interval):
        seconds_in_future = (int(samples) - 1) * int(interval) if samples else samples
        logging.info("Trying to find the end date for " + str(seconds_in_future) + " seconds in the future")
        start_date = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        logging.info("Starting date is : " + str(start_date))
        end_date = start_date + datetime.timedelta(seconds=seconds_in_future)
        logging.info("Ending date is : " + str(end_date))
        return end_date.year, end_date.month, end_date.day, end_date.hour, end_date.minute, end_date.second
    else:
        logging.critical("The date was not set, got None")
        return year, month, day, hour, minute, second


def validateDate(year, month, day, hour, minute, second):
    if year < 1 or year > 9999:
        year = 1
    if month < 1 or month > 12:
        month = 1
    if day < 1 or day > monthrange(year, month)[1]:
        day = 1
    if hour < 0 or hour > 23:
        hour = 0
    if minute < 0 or minute > 59:
        minute = 0
    if second < 0 or second > 59:
        second = 0
    return year, month, day, hour, minute, second

def getMonthDays(year,month):
    if year is None:
        year=1
    if month is None:
        month=1
    return monthrange(year,month)[1]
# To convert your PNG into Base 64:
#   Go to https://www.base64-image.de/
#   Drag and drop your PNG image onto the webpage
#   Choose "Copy image"
#   Create a string variable name to hold your image
#   Paste data from webpage as a string
#   Delete the "header" stuff - up to the data portion (data:image/png;base64,)


green_button = "iVBORw0KGgoAAAANSUhEUgAAAIwAAAAeCAYAAAD+bvZ2AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAEmUlEQVR4nO2bz08bRxTHv293vF7zwwRwUmOhCDXIbhGplKhKpIpDFakqqMp/EMmoUqX2UqXaQ6Vy4OSeTK/tEeePKOVSqRKqmii" \
               "CA6jKpqjhQEgMLihA1l7veqeHYmrA692whLXxfo6e8czovTffmdmZR3BJclaJAhgDMAFgBMAwgA4AMbdtBDQFBQAagFUAKwDmCFhQJ2f23fyZnCokZ5UhAFOIbdwTBp/J6H8Jiu4AoTJILnoZuPtBBJwpvBQBdBl8txe8MAC+MaThn/" \
               "gDABl1cma90X9tfZXKKYwLZoauPr0vppYk6ts884EHNA/WVgLWk5tl/vzdLHE2raazZr16dQMmmVMSdGlzXrzx26gQe+Hcm0eJ8FthOPd5AE2ElR9EZenjRb7bf/fpZHbjePkJXyVzyi3h8vpc6PYvfRQybGodIzB4S3PcfdwIwfxjY" \
               "ptvDX6qTmYf15YdCYVkTkkIsfVl6dZ8H7G6iuSux4CWh5sMxqPxbasweF2tUZrDgEnlFIZoYUm+/fPoobK4bv3sBuoHfi+JzQo3Qig9/GyF78VuVPc07LBQqGTk1KNRARwwmH0rb2do59zfMai9Q4ZszE/EEX7v4Wjp8XgGwLfAweRK" \
               "zipDLP63Ghn5XTq3UR7Bb4lq74Bxsn/pz4/KZv5aSk3PrFWlZEoe+Esi00ZZHO3p0eF+C4y/3TcBjS0QHliVzPy1KQBfUHJWiYpdhXz3B7/Kp2zPb38HeMRuSaplf/lOqbIfe4cBGAv15GXBFE/t+GCGtjgu9nChnk3Z3IuNMQATTN4" \
               "FTAbhoPBk4LztkAg0qtlh8isQYYIBGGGsCDJFVAPjRHg4frgLHN7aOAuCKBYBYIQBGGacgyqswUQPPvW2PZwDHMMMAKgigho43WmJCwTm4kOV/07QDMAq18NXBcmyrxwIzAXHeUniRhggrDIAK5befUcSG90dOUWE101xEHHNjqF3gQ" \
               "MrDMBcudjztSy9wv+OfzMHtnq4ULt/GHCxpzCKlwBgjgFY0Eu9GnVsdJy+R28Gb7R/Og+oze+S3KCXejUCLVTvkn68En3ypcxe163MHezp2dz+S0xAA3SjE5t77/+kprNfVS+PMvvF+OeRyLNTXT56naF+n7LaXmAcHLBXjJfBkQFq5" \
               "lYy903mirT2XUSspzKNLerV4NzvJSmQGFuKlU5s6kPfq+kfpoCa9zCAML1TToxH2NpNgY4esR0N6jVgfJaYYA9TH4sL2DETi4AwXf3txBNNGdpyHM/7BDdXmIe09jmp3QOm3ny1uIA8EtsldFxX03WeaFZJ5pQPI1ybj1sv+4QDRzqa" \
               "0/MeJgiYZsIC4QUNbJco8omazi7WltmmmYQtff6yuT0a4bqLLgKFuShoFMaW2L9YFqS7tcpSxdZSyZzCiPNMl6nd7zX2JZnbPwz3bPDgmOQ7RSGEHdZdfi1GspzozRLZaqmmysqV8r1OU5fligHJMiGAg3GXS5YDwZJ0vphEsEhAWWA" \
               "oiiFoLKyVROkBODLqZPZ0qbLHSeWUKOcnk/GJyFMyfiAu504BHBqIr/LDZHxaUNNZV8n4/wLyI5Bd+hdqngAAAABJRU5ErkJggg=="
red_button = "iVBORw0KGgoAAAANSUhEUgAAAIwAAAAeCAYAAAD+bvZ2AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAEJklEQVR4nO2bz2vbZhjHP68sy3K8xcHOD5aN0kOQt5AcWsZGIafB2HLof1BwGAy2y+htsBxy8k69b8e4/0TIPbRsjGzQwFDJYYetp" \
             "Ynj0iTIPyS97w6JM6eJY81OIjvS52hJfsXzfvV93l+PICCrljUKLACLwCwwA4wA40H/I2YgqAAOsA1sAWsIsbFk24dBHhbdbli1rNvA8ngq9eCDkREzb5qMJpMkNQ0zkejnxWNCou77NHyffdel0mjwolZz9hqNx0Bpybb/vujZjoIpFw" \
             "q6BqVbmczDD7NZI5dKXfqLxwwGAtip1/nzzZvmP47zSMFK0ba9TveeoWxZ02OGsX43n58bN80rfVkAIboa3ZWilAq1/UHiVa3G5t7e5r7r3l96/vzF29fP9FTZsj6ZNM21e5OTuaSmBWqk73CHLBhiwZzClZInOzvV3UbjiyXb/q392qm" \
             "eKlvW9IRpPvt0YiKnBxTLpRB2h4Ut2JA5z2E9KfmlUqnuNhrzS7Z94jQnkSoXCvqorv9+b2pq7lrFMgBEWy6dU7IrJU93d7cOXPdOa0yjty5qSpU+GhubE4Av5fW86TFhj2GiTifBaEIwm83O/VqplIDv4fjjWrWs2++l0/Z8LmfAJYxJ" \
             "YoaKbp/r1uvXzZe1WqFo23+1HGb5/UzG8HocS8QCu9lMZzLGy1ptGfharFrW6LvJ5Ks7+XzH+fNVJ4xYcIPPH9Vq/cB1p3RgYSyVMi9yl65jjLBnOTF9EaT3xgzD3G82F3RgMa3r9JqOjlqMBTPMBMkgaV1HCLGoA7OGEEgpI5saIj9HC" \
             "zBLNY6WWmZ1YEYBbuwS0SVA30ulUDCjA0fpSKn/lBYx8UTdYYL0dmvIogPbrpS3hKZBhwW7bgGNlryiiSslArZ1YKvmeZ9pF20HdHOcfldqQ3a0qDtMEOqeB0pt6cCa43nfmclkzx0n+uzwsB0q6oIJEn/H9wHWdGDD8TwnK+VIzy0Ouc" \
             "NEfbc6CI7nOQix0dpL+imfTn9j9HrkcsgFE/nNzy7xb/o+e/X6z0Xb/ra1l1Q6bDa/yqZSRk8NxoK50Ry6blNBCdrPw1hW6R3D+CF5jstcdUDjMczg4vo+B83mj0XbXoa28zDAiuO6X45o2t0zAuniAP0GPBZMuHSKv1IKx3U3gZXWb2e" \
             "OaGqa9iyVTOau1abjlDRwKKWou25VKjVfPO+IZouyZX0shFjXE4nAouk34GGf2o8FcxqlFK7vV5VSnxdte7P9WscyE2BdSyTmhBBdU8bQp6RYMCdIKVFSbgL3252lRedCNsvSgZIS4iFCGBfNhGKHuQEoBVI2gUf830K2dlqlsgoeSCFM" \
             "aHOE40DHghkyjuMtOFqlF+AIeKz6KZV9m3KhMKqUOlOML4Toqxg/Fsu1U1FHAtlGqZNi/GLAYvx/AZDaohvg1aLiAAAAAElFTkSuQmCC"
blue_button = "iVBORw0KGgoAAAANSUhEUgAAAIwAAAAeCAYAAAD+bvZ2AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAEhklEQVR4nO2bT28bRRiHn9kdr9eOk7ZJ2oYcoEWRkKJUDghxygkJYR/6DXpCQgLJQb0hkUNP5tQbRnDul7BzzxEFR80FKahUQrSl" \
              "qaMS/1mvvTMcEheT2t5NnHrrrJ+jd2f33ff97W9mPDuCgKTXizNo1oAssAwsAUlgPug1eiGGaTzhLOwDdWAPIXY1uohma6eQrQZp7Fuv9HrpBrChU/YdrkzZpGxIWGAaEJPDhR44ignnSqsNbQUNFw4bcFCri5rzAMjv/JD9c1DTvqVa" \
              "zZWkFiLPXOouC1csUva5x+0fxYSRoDkSzpOKy0HtvtDcKxcy7V6n9ixVOldaJGltivfmV8R0AKHoocLtF8YIGfoBLgz6nzr68f42Tuv2TiH718njr1UqnSt+wnSiaLx/bVaYxmiinBAuJ1SgPYX6/VmFQ+fznUL2l76npnOlRZGKPzRv" \
              "zs0KY5RiCddhRNgGFzK6h8NqT+E92q/oavNWt9O8StVqriSxY7/Gbs6tjNpZtAi3S4i4Xvr2yNpTtB692MVpf9gZ07ya5mhB3ro+tWKi0J4aTaDHiLBLNlFMz1+FgNhCasV9fJAHvoXjVKXXSzfMlPVbfGHa6t/84hL5Lsmn4O7TQ1cd" \
              "uh+UC5k/Og6zEZuxLOF5QI8XzjejQ0osbIVGXDB+AxDrkmU5h+4G8KVIrxdnjJj5LLk4NWD+7JNRP4lOeLsJ8MI0ntQc1VTXJZq1mG3axoBxi98YQ08EM94E6JNlXNrNprsmgayUINremS8oJoIZcwIIxgQXshJYNoXmyGE6hf//BfwE" \
              "ONHLeBNo0G9ogGUJLBnaQ6izVz3iY8axRwSYdRhHrrAkAYy2whC6f+HfuMOEbVHRlnygpz8e4kpgD8971xzUysezJoIZb4I8vVIA5p4EdlVLf4o5aJbkd8PhEt5rLWOUiKj/cxcA5QnA3JUIim2PbxIMmCX5MlzCg/Shb5KoCybIC9tq" \
              "xwCKEs1WUxn1Gbxkv5PfdDpD75AiLpgga7+uZ9SBrc5a0k9XqX4V77jMqSs43gkf7+jPg8EFb2LynNTP5ULm685aUr6qrS9sr2qd5XbDrzaH7jEh3//tpmokXAR56MpUOlfMX2u9/C6hen3KObigw1p62EsLUe+SBqXfEZK/Y5e+L/+Y" \
              "3YCu72FA3DuQqUyiUfnIOCEQv0HR0AmfCCZU+j29QnAQT20jxL2e56bXS4t2q/nwncaL2W7RaJ98jv20OvJd0uv5Vwie2nMVR8ZvlQuZ1z/R7JDOlT5OtJzNhdrz2ZNOc1GJusOcRCF4MjVfcaT9WbmQ2e4+1nebSbzd3Lxae7GSaDd9" \
              "bzD26Y64YLptoS5t9pOz2660bnc7S4e+mUrnSlJolZ92qncvN15a9iDhjPkkaeIw0JBxDpKX3ZqVvK+FcbqNbN2s5o62ytpu485Us2bbLQer7WIohdTHn3SO95g3coJpCwNlmLjSohGzqcWTdSeWeADky4XM2bbKnmQ1V5rRmjUhyKJZ" \
              "RpzPZvzQ7WX8O9TT8t9mfNgFisBWuZAJtBn/X8BeipVBzcAtAAAAAElFTkSuQmCC"
