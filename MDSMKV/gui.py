#!/usr/bin/env python3
import logging
import sys
import logging.handlers as handlers
import PySimpleGUI as Sg
import datetime
from threading import Thread
from utils import serial_ports, image_file_to_bytes, green_button, blue_button, red_button, calculateFutureDate, validateDate, getMonthDays
from rs232Commands import Header,Disconnect, Connect, Sleep, WakeUp, GetHeader, device, GetCurrentDate, GetCurrentTime, SendMessage, SendCommand, encodeMessage, checkReadWithMessage, sendRead

# This limit is an hard limit for Alec Co device, if yours doesnt have it, please change it
MAX_SAMPLES = 512000
DELAY_TO_START = 3  # minutes between device date and start time
FLAG_ERROR = False
filename = ""
flag_change = True
bcolor = '#242834'
wcolor = ('white', bcolor)
device = device
default_size = (34, 1)
default_size_double = (34, 2)
default_size_half = (default_size[0] // 2, 1)
button_size = (150, 50)
current_data_value, current_data_value2, exit_real_time = 0, 0, False
data_array = []
import os

if not os.path.exists("./log"):
    os.makedirs("./log")
if not os.path.exists("./save"):
    os.makedirs("./save")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Here we define our formatter
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')

logHandler = handlers.TimedRotatingFileHandler('./log/RDS.log', when='M', interval=10, backupCount=0)
logHandler.setLevel(logging.INFO)
logHandler.setFormatter(formatter)

errorLogHandler = handlers.RotatingFileHandler('./log/CRITICAL_ERROR.log', maxBytes=5000, backupCount=0)
errorLogHandler.setLevel(logging.ERROR)
errorLogHandler.setFormatter(formatter)

stdout_logger = logging.StreamHandler(sys.stdout)
stdout_logger.setLevel(logging.INFO)
stdout_logger.setFormatter(formatter)

logger.addHandler(stdout_logger)
logger.addHandler(logHandler)
logger.addHandler(errorLogHandler)


def ShowMainWindow():
    global flag_change
    Sg.ChangeLookAndFeel('DarkTanBlue')
    Sg.SetOptions(auto_size_buttons=False, border_width=0, button_color=Sg.COLOR_SYSTEM_DEFAULT, input_elements_background_color="#596470")
    # ----=== Device part ===-------
    device_selection = [[Sg.Combo(values=serial_ports(), key='_portList_', size=default_size_half),
                         Sg.VSep(pad=(10, 0)),
                         Sg.Button('Connect', image_data=image_file_to_bytes(green_button, button_size), button_color=wcolor, font='Any 15', pad=(0, 0), key='_connect_', size=default_size_half)]]

    device_buttons = [[Sg.Button('Wake Up', image_data=image_file_to_bytes(red_button, button_size), button_color=wcolor, font='Any 15', pad=(25, 4), key='_wakeup_', size=default_size_half),
                       Sg.VSep(pad=(0, 0)),
                       Sg.Button('Get Header', image_data=image_file_to_bytes(blue_button, button_size), button_color=wcolor, font='Any 15', pad=(25, 4), key='_header_', size=default_size_half)]]

    device1 = Sg.Column([[Sg.Frame('Device Connection (OFF)', device_selection, title_color="red", font='any 18', background_color=bcolor, key="_device_connection_")]])
    device2 = Sg.Column([[Sg.Frame('Device Controls (Asleep)', device_buttons, title_color="red", font='any 18', background_color=bcolor, key="_device_control_")]])

    # ------=== Headers Fields ===------

    serial_id = Sg.Text(device.header.SerialId, key="_serialID_", size=default_size_half)
    coefficients = [Sg.Text("{} {}\n{} {}".format(device.header.Coeff1, device.header.Coeff2, device.header.Coeff3, device.header.Coeff4), key="_coefficients_", size=default_size_double)]
    starting_date = Sg.Text("{}/{}/{} {}:{}:{}".format(device.header.Year, device.header.Month, device.header.Day, device.header.Hour, device.header.Minute, device.header.Second),
                            key="_starting_date_", size=default_size_half)
    model = Sg.Text(device.header.Model, key="_model_", size=default_size_half)
    samples = Sg.Text(device.header.Samples, key="_sample_", size=default_size_half)
    ending_date = Sg.Text("{}/{}/{} {}:{}:{}".format(device.header.Year, device.header.Month, device.header.Day, device.header.Hour, device.header.Minute, device.header.Second), key="_ending_date_",
                          size=default_size_half)
    interval = Sg.Text(device.header.Interval, key="_interval", size=default_size_half)
    current_date = Sg.Text("{}/{}/{} {}:{}:{}".format(None, None, None, None, None, None), key="_current_date_", size=default_size_half)
    # -----==== Buttons Part ===------
    set_coefficients = [Sg.Button('Set Coefficients', image_data=image_file_to_bytes(blue_button, button_size),
                                  button_color=wcolor, font='Any 10', pad=(122, 7), key='_set_coefficients_')]
    set_serial_id = Sg.Button('Set Serial Id', image_data=image_file_to_bytes(blue_button, button_size),
                              button_color=wcolor, font='Any 15', pad=((23, 23), 0), key='_set_serial_id_', size=default_size)
    set_model = Sg.Button('Set Model', image_data=image_file_to_bytes(blue_button, button_size),
                          button_color=wcolor, font='Any 15', pad=((23, 23), 0), key='_set_model_', size=default_size)
    set_start_time = Sg.Button('Set Start Date', image_data=image_file_to_bytes(blue_button, button_size),
                               button_color=wcolor, font='Any 15', pad=((23, 23), 0), key='_set_start_time_', size=default_size)
    set_samples = Sg.Button('Set Samples', image_data=image_file_to_bytes(blue_button, button_size),
                            button_color=wcolor, font='Any 15', pad=((23, 23), 0), key='_set_samples_', size=default_size)
    set_interval = Sg.Button('Set Frequency', image_data=image_file_to_bytes(blue_button, button_size),
                             button_color=wcolor, font='Any 15', pad=((23, 23), 0), key='_set_interval_', size=default_size)
    set_ending_date = Sg.Button('Set Ending Date', image_data=image_file_to_bytes(blue_button, button_size),
                                button_color=wcolor, font='Any 13', pad=((23, 23), 0), key='_set_end_time_', size=default_size)
    set_header = [Sg.Button('Start', image_data=image_file_to_bytes(red_button, button_size),
                            button_color=wcolor, font='Any 10', pad=(122, 0), key='_set_headers_')]
    set_current_date = Sg.Button('Set Current Date', image_data=image_file_to_bytes(blue_button, button_size),
                                 button_color=wcolor, font='Any 13', pad=((23, 23), 0), key='_set_current_date_', size=default_size)

    # ------=== Header Display Part ===------
    colums1 = Sg.Column([
        [Sg.Frame('Serial ID', [[serial_id, set_serial_id]], font='any 18', background_color=bcolor, size=default_size, relief="groove", key="_serial_id_frame_")],
        [Sg.Frame('Start Time', [[starting_date, set_start_time]], font='any 18', background_color=bcolor, size=default_size, relief="groove", key="_start_time_frame_")],
        [Sg.Frame('End Time', [[ending_date, set_ending_date]], font='any 18', background_color=bcolor, size=default_size, relief="groove", key="_end_time_frame_")],
        [Sg.Frame('Sample Number', [[samples, set_samples]], font='any 18', background_color=bcolor, size=default_size, relief="groove", key="_samples_frame_")],
        [Sg.Frame('Current Date', [[current_date, set_current_date]], font='any 18', background_color=bcolor, size=default_size, relief="groove", key="_current_date_frame_")]
    ])

    colums2 = Sg.Column([
        [Sg.Frame('Model', [[model, set_model]], font='any 18', background_color=bcolor, size=default_size, relief="groove", key="_model_frame_")],
        [Sg.Frame('Coefficients', [coefficients, set_coefficients], font='any 18', background_color=bcolor, size=default_size_double, relief="groove", key="_coefficients_frame_")],
        [Sg.Frame('Interval between Samples', [[interval, set_interval]], font='any 18', background_color=bcolor, size=default_size, relief="groove", key="_interval_frame_")],
        [Sg.Frame('Send Configuration', [set_header], font='any 18', background_color=bcolor, size=default_size, relief="groove", key="_header_frame_")]
    ])
    # -------==== Data Display Part ====----------
    set_real_time = Sg.Button('Real Time', image_data=image_file_to_bytes(blue_button, button_size),
                              button_color=wcolor, font='Any 13', pad=(25, 8), key='_set_real_time_', size=default_size)
    set_memory = Sg.Button('From Memory', image_data=image_file_to_bytes(blue_button, button_size),
                           button_color=wcolor, font='Any 13', pad=(25, 8), key='_set_memory_', size=default_size)
    show_graph = Sg.Button('Show Graph', image_data=image_file_to_bytes(blue_button, button_size),
                           button_color=wcolor, font='Any 13', pad=(23, 8), key='_show_graph_', size=default_size)
    show_table = Sg.Button('Show Table', image_data=image_file_to_bytes(blue_button, button_size),
                           button_color=wcolor, font='Any 13', pad=(23, 8), key='_show_table_', size=default_size)
    delete_button = Sg.Button("ERASE", image_data=image_file_to_bytes(red_button, button_size),
                              button_color=wcolor, font='Any 13', pad=(122, 8), key='_DELETE_', size=default_size)
    set_filename = Sg.Button('Set Filename', image_data=image_file_to_bytes(blue_button, button_size),
                             button_color=wcolor, font='Any 13', pad=(23, 8), key='_set_filename_', size=default_size)
    filename_box = Sg.InputText("", size=default_size_half, background_color="#596470", pad=(5, 8), key='filename')
    data1 = Sg.Column([
        [Sg.Frame('Filename', [[filename_box, set_filename]], font='any 18', background_color=bcolor, size=default_size, relief="groove")],
        [Sg.Frame('Show Data', [[show_table, Sg.VSep(pad=(4, 0)), show_graph]], font='any 18', background_color=bcolor, size=default_size)]
    ])

    data2 = Sg.Column([
        [Sg.Frame('Mode', [[set_real_time, set_memory]], font='any 18', background_color=bcolor, size=default_size, relief="groove")],
        [Sg.Frame('ERASE DEVICE DATA', [[delete_button]], font='any 18', background_color=bcolor, size=default_size)]
    ])

    main_screen = [[Sg.Frame("Device", [[device1, device2]], font='any 18', background_color=bcolor)],
                   [Sg.Frame('Device Configuration', [[colums1, colums2]], font='any 18', background_color=bcolor)],
                   [Sg.Frame('Data Recovery', [[data1, data2]], font='any 18', background_color=bcolor)]]

    # debug_screen = [[Sg.Frame('Debug panel', temp, font='any 18', background_color=bcolor)]]
    # layout = [[Sg.TabGroup([
    #    [Sg.Tab('Main Panel', main_screen, title_color="red", background_color=bcolor), Sg.Tab('Debug Panel', debug_screen, title_color="red", background_color=bcolor)]
    # ])]]
    layout = main_screen
    window = Sg.Window('Alec Light Intensity',
                       no_titlebar=False,
                       keep_on_top=True,
                       use_default_focus=False,
                       font='any 15',
                       background_color=bcolor).Layout(layout).Finalize()

    # ---===--- Loop taking in user input --- #

    while True:
        if flag_change:
            toggle_buttons(window, device.connected, "Device is connected, toggling on the buttons", "Device is disconnected, toggling off the buttons",
                           '_wakeup_', '_header_', '_set_coefficients_', "_set_serial_id_", "_set_model_", "_set_start_time_", "_set_samples_", "_set_interval_",
                           "_set_end_time_", "_set_headers_", "_set_current_date_", "_set_real_time_", "_set_memory_", '_DELETE_')
            toggle_buttons(window, not device.sleep and device.connected, "Device is awake, toggling on the buttons", "Device is asleep, toggling off the buttons",
                           '_header_', '_set_coefficients_', "_set_serial_id_", "_set_model_", "_set_start_time_", "_set_samples_", "_set_interval_",
                           "_set_end_time_", "_set_headers_", "_set_current_date_", "_set_real_time_", "_set_memory_", '_DELETE_')
            toggle_buttons(window, not device.sleep and device.connected and device.header.SerialId is not None, "Header were set, toggling on the buttons",
                           "Header are unset, toggling off the buttons",
                           '_set_coefficients_', "_set_serial_id_", "_set_model_", "_set_start_time_", "_set_samples_", "_set_interval_",
                           "_set_end_time_", "_set_headers_", "_set_current_date_", "_set_real_time_", "_set_memory_", '_DELETE_')
            toggle_buttons(window,False,"Not enabled","Not enabled","_show_graph_","_show_table_")
            window.Element("filename").Update(filename)
            flag_change = False
        button, values = window.Read(timeout=100)
        window.Element("_portList_").Update(values=serial_ports())
        if button is None:
            break  # exit button clicked
        else:
            if button != "__TIMEOUT__":
                logging.info("Button pressed was: " + button)
        if button == "_wakeup_":
            sleep_handler(window, values)
        if button == "_header_":
            header_handler(window)
        if button == "_connect_":
            connect_handler(window, values)
        if button == "_set_coefficients_":
            open_coefficient_window(window)
        if button == "_set_serial_id_":
            open_serial_id_window(window)
        if button == "_set_interval_":
            open_interval_window(window)
        if button == "_set_start_time_":
            open_start_time_window(window)
        if button == "_set_end_time_":
            open_end_time_window(window)
        if button == "_set_current_date_":
            open_current_time_window(window)
        if button == "_set_samples_":
            open_samples_window(window)
        if button == "_set_headers_":
            send_headers(window, values)

            if sys.platform.startswith('win'):
                window.Enable()
            else:
                window.UnHide()
        if button == "_set_model_":
            open_model_window(window)
        if button == "_set_memory_":
            start_memory_transfer(window)
        if button == "_set_real_time_":
            start_real_time_transfer(window)
        if button == "_DELETE_":
            open_delete_window(window)
        if button == "_set_filename_":
            open_filename_window(window)
        # Refresh Current Date
        if device.header.currentDate is not None:
            device.header.currentDate = device.header.currentDate + (datetime.datetime.now() - device.header.dateTimeNow)
            device.header.dateTimeNow = datetime.datetime.now()
            now = device.header.currentDate
            window.Element('_current_date_').Update("{}/{}/{} {}:{}:{}".format(now.year, now.month, now.day, now.hour, now.minute, now.second))


def checkIntInput(lower, upper, values, key, windows):
    if len(str(values[key])) and str(values[key])[-1] not in ('0123456789'):  # if last char entered not a digit
        windows.Element(key).Update(values[key][:-1])
    elif len(str(values[key])) and int(values[key]) < lower:
        windows.Element(key).Update(lower)
    elif len(str(values[key])) and int(values[key]) > upper:
        windows.Element(key).Update(upper)


def real_time(args):
    global current_data_value, exit_real_time, device, current_data_value2
    fails = 0
    logging.info("Starting logging real time data")
    while not exit_real_time:
        try:
            device.serial_device.write(encodeMessage("real,"))
            result = checkReadWithMessage("real")
            if result is None or not result:
                logging.critical("Real Time result was wrong : " + str(fails) + "/10")
                fails += 1
                if fails > 10:
                    exit_real_time = True
            else:
                current_data_value = result[7:len(result) - 2].decode().split(",")[0]
                current_data_value2 = result[7:len(result) - 2].decode().split(",")[1]
                logging.info(result[7:len(result) - 2].decode())
                logging.info(current_data_value)
                logging.info(current_data_value2)
        except Exception:
            logging.error("Fatal error in real time", exc_info=True)


def write_to_file(window):
    global data_array, filename
    while os.path.isfile(filename):
        logging.critical("File exist already")
        filename = filename[:-4] + '_'
        filename += "1.Raw"
    f = open(filename, "w+")
    result = GetHeader()
    if result is not None:
        result = result[5:len(result) - 2].decode()
        logging.info("Header was successfully received, its content is : " + str(result))
        result = result.split(',')
        device.header.Model, device.header.SerialId, device.header.Coeff1, device.header.Coeff2, device.header.Coeff3, device.header.Coeff4 = result[:6]
        year, month, day, hour, minute, second, device.header.Interval, device.header.Samples = map(int, result[6:])
    else:
        logging.critical("Header failed")
        ShowPopUp(window, "No file were written, header failed")
        return
    f.write('/  Alec MDS5 Data Processing\n')
    f.write('FileName={}\n'.format(filename))
    f.write('InstType={}\n'.format(device.header.Model))
    f.write('InstNo={}\n'.format(device.header.SerialId))
    f.write('Comment={}\n'.format("DATA CORRUPTION DETECTED, 65535 number will be wrong" if FLAG_ERROR else ""))
    f.write('StartTime={}/{}/{} {}:{}:{}\n'.format(year, month, day, hour, minute, second))
    start_date = datetime.datetime(year, month, day, hour, minute, second)
    year, month, day, hour, minute, second = calculateFutureDate(year, month, day, hour, minute, second, device.header.Samples, device.header.Interval)
    f.write('EndTime={}/{}/{} {}:{}:{}\n'.format(year, month, day, hour, minute, second))
    f.write('StepTime={} seconds\n'.format(device.header.Interval))
    f.write('CoefDate={}/{}/{} {}:{}:{}\n'.format(device.header.currentDate.year, device.header.currentDate.month, device.header.currentDate.day,
                                                  device.header.currentDate.hour, device.header.currentDate.minute, device.header.currentDate.second))
    f.write('Samples={}\n'.format(device.header.Samples))
    f.write("\n[Coef]\n")
    f.write("{},{},{},{}\n".format(device.header.Coeff1, device.header.Coeff2, device.header.Coeff3, device.header.Coeff4))
    f.write("\n[Item]\n")
    delta = datetime.timedelta(seconds=device.header.Interval)
    for i in range(device.header.Samples):
        current_array = data_array[i // 100]
        data1 = current_array[(i % 100) * 4 + 1] << 8 | current_array[(i % 100) * 4]
        data2 = current_array[(i % 100) * 4 + 3] << 8 | current_array[(i % 100) * 4 + 2]
        f.write("{}/{}/{} {}:{}:{},{},{},\n".format(start_date.year, start_date.month, start_date.day, start_date.hour, start_date.minute, start_date.second, data1, data2))
        start_date += delta
    f.close()


def start_real_time_transfer(window):
    global exit_real_time
    if not device.sleep and device.connected and device.header.Interval != 0:
        exit_real_time = False
        if sys.platform.startswith('win'):
            window.Disable()
        else:
            window.Hide()
        layout = [[Sg.Quit(button_color=('white', 'black')), Sg.T('', pad=(100, 0), font='Any 15', key='output', auto_size_text=True, size=(5, 1)),
                   Sg.T('', pad=(50, 0), font='Any 15', key='output2', auto_size_text=True, size=(5, 1))],
                  [Sg.Graph((500, 500), (0, 0), (500, 400), background_color='black', key='graph')], ]
        window_real_time = Sg.Window('Real Time Graph', layout, grab_anywhere=True, keep_on_top=True, background_color='black', no_titlebar=True, use_default_focus=False)

        graph = window_real_time.Element('graph')
        output = window_real_time.Element('output')
        output2 = window_real_time.Element('output2')
        thread = Thread(target=real_time, args=(None,))
        thread.start()
        last_data_value = last_data_value2 = i = 0
        prev_x, prev_y = 0, 0
        while True and not exit_real_time:
            event, values = window_real_time.Read(timeout=100)
            if event == 'Quit' or event is None:  # always give the user a way out
                break
            data_value = int(current_data_value)
            data_value2 = int(current_data_value2)
            if data_value == last_data_value and data_value2 == last_data_value2:
                continue
            logging.info("e{}".format(data_value))
            logging.info("e{}".format(data_value2))
            output.Update(data_value)
            output2.Update(data_value2)
            if data_value > 2098:
                data_value = 2098
            if data_value2 > 2098:
                data_value2 = 2098
            data_value2 = data_value2 / 2098 * 400
            data_value = data_value / 2098 * 400
            new_x = i
            if i >= 500:
                graph.Move(-150, 0)  # shift graph over if full of data
                prev_x = prev_x - 150
            graph.DrawLine((prev_x, prev_y), (new_x, data_value), color='white')
            graph.DrawLine((prev_x, prev_y), (new_x, data_value2), color='blue')
            prev_x = new_x
            i += 1 if i < 500 else 0
            last_data_value = int(current_data_value)
            last_data_value2 = int(current_data_value2)
        if exit_real_time:
            ShowPopUp(window, "Real time failed")
        exit_real_time = True
        window_real_time.close()
        if sys.platform.startswith('win'):
            window.Enable()
        else:
            window.UnHide()



def start_memory_transfer(window):
    global data_array, filename, FLAG_ERROR
    if not device.sleep and device.connected and device.header.Interval != 0:
        if sys.platform.startswith('win'):
            window.Disable()
        else:
            window.Hide()
        result = SendCommand("open,", "ak,open")
        if result is None or not result:
            logging.critical("Opening the device did not work")
            ShowPopUp(window, "Opening the device did not work")

            if sys.platform.startswith('win'):
                window.Enable()
            else:
                window.UnHide()
            return
        amount = device.header.Samples // 100 + 1
        logging.info("Reading for {} messages of 100 samples".format(amount))
        while amount:
            result = sendRead("read,", "retry,")
            if result is None or not result:
                logging.critical("Reading didnt work")
                ShowPopUp(window, "Reading didnt work")

                if sys.platform.startswith('win'):
                    window.Enable()
                else:
                    window.UnHide()
                return
            result = result[2:len(result) - 1]
            logging.info("This numbers might be useful : " + ",".join(map(str, result[:7])))
            result = result[7:]
            data_array.append(result)
            amount -= 1
        result = sendRead("read,", "retry,")
        result = result[2:len(result) - 1]
        correct = result[:7] == [255] * 7
        if not correct:
            logging.critical("There was a data corruption, the data can not be assessed as correct")
            ShowPopUp(window, "There was a data corruption, the data can not be assessed as correct")
        if filename == "":
            ShowPopUp(window, "No Folder was set, please select one")
            open_filename_window(window)
        if checkLastArray(data_array[-1]):
            logging.critical("The last array is likely corrupt, we will assess the others")
            errors = 0
            for data in data_array:
                errors += 1 if ("255,255,255,255" not in ",".join(map(str, data))) else 0
            logging.critical("The last array was corrupted so as {} others".format(errors))
            FLAG_ERROR = True
            write_to_file(window)
            ShowPopUp(window,
                      "There was a data corruption, "
                      "\n A grand Total of {} transfer failed, this can be due to a bad connection "
                      "\n The data was written but there is is an error mention at the top of the file"
                      "\n The wrong results will look something like : 65535 in the file : "
                      "\n{}".format(errors + 1, filename))

            return
        write_to_file(window)
        ShowConfirmation(window, "The Data transfer was successful and the data was written to the desired file : \n{}".format(filename))

        if sys.platform.startswith('win'):
            window.Enable()
        else:
            window.UnHide()


def checkLastArray(data):
    amount = device.header.Samples % 100
    correctPart = data[:amount * 4]
    invalidPart = data[amount * 4:]
    logging.info("Correct Part: " + ",".join(map(str, correctPart)))
    logging.info("Invalid Part: " + ",".join(map(str, invalidPart)))
    return invalidPart == [255] * (100 - amount) and ("255,255,255,255" not in ",".join(map(str, correctPart)))


def send_headers(window, values):
    # check starting date is at least 2 min ahead of current date
    # Get Date saved on device as Year, month and day
    date = GetCurrentDate()
    # Get Time saved on device as Hour, Minute and Seconds
    time = GetCurrentTime()
    if date is not None and time is not None:
        if sys.platform.startswith('win'):
            window.Disable()
        else:
            window.Hide()
        date = date[7:len(date) - 2].decode()
        logging.info("Current Date was successfully received, its content is : " + str(date))
        time = time[7:len(time) - 2].decode()
        logging.info("Current Time was successfully received, its content is : " + str(time))
        year, month, day = map(int, date.split(','))
        hour, minute, second = map(int, time.split(','))
        year, month, day, hour, minute, second = validateDate(year, month, day, hour, minute, second)
        device.header.currentDate = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        current_start_time = datetime.datetime(device.header.Year, device.header.Month, device.header.Day, device.header.Hour, device.header.Minute, device.header.Second)
        if (current_start_time - device.header.currentDate).total_seconds() < DELAY_TO_START * 60:
            logging.critical("Starting Time must be at least 3 minutes after current device date time")
            ShowPopUp(window, "Starting Time must be at least 3 minutes after current device date time, Aborted")
            return
        if device.header.Interval == 0:
            logging.critical("Interval was not set, please set one")
            ShowPopUp(window, "Interval was not set, please set one, Aborted")
            return

        # print(SendMessage("write,L,201394,-1.01078e+00,1.010783e+00,0,0,0000,00,00,00,00,00,0,0,"))
        result = SendMessage("write,{},{},{},{},{},{},{},{},{},{},{},{},{},{},".format(device.header.Model, device.header.SerialId, device.header.Coeff1,
                                                                                       device.header.Coeff2, device.header.Coeff3, device.header.Coeff4, str(device.header.Year).rjust(4, '0'),
                                                                                       str(device.header.Month).rjust(2, '0'), str(device.header.Day).rjust(2, '0')
                                                                                       , str(device.header.Hour).rjust(2, '0'), str(device.header.Minute).rjust(2, '0'),
                                                                                       str(device.header.Second).rjust(2, '0'), device.header.Interval, 0))
        if result is None or not result:
            logging.critical("Set header sequence failed, aborting")
            ShowPopUp(window, "Set header sequence failed, aborting ", "{},{},{},{},{},{},{},{},{},{},{},{},{},{},".format(str(device.header.Model), device.header.SerialId, device.header.Coeff1,
                                                                                                                           device.header.Coeff2, device.header.Coeff3, device.header.Coeff4,
                                                                                                                           str(device.header.Year).rjust(4, '0'),
                                                                                                                           str(device.header.Month).rjust(2, '0'), str(device.header.Day).rjust(2, '0')
                                                                                                                           , str(device.header.Hour).rjust(2, '0'),
                                                                                                                           str(device.header.Minute).rjust(2, '0'),
                                                                                                                           str(device.header.Second).rjust(2, '0'), device.header.Interval, 0))
            return
        result = SendMessage("start,{},{},{},{},{},{},{},".format(str(device.header.Year).rjust(4, '0'), str(device.header.Month).rjust(2, '0'), str(device.header.Day).rjust(2, '0')
                                                                  , str(device.header.Hour).rjust(2, '0'), str(device.header.Minute).rjust(2, '0'), str(device.header.Second).rjust(2, '0')
                                                                  , device.header.Interval))
        if result is None or not result:
            logging.critical("Start time sequence was not successful, aborting")
            ShowPopUp(window, "Start time sequence was not successful, aborting")
            return
        validated_state(window)
        sleep_handler(window, values)
        connect_handler(window, values)
        ShowConfirmation(window,
                         "Please UNPLUG the device \nThe start sequence was initiated, it will start at: {}/{}/{} {}:{}:{}".format(str(device.header.Year).rjust(4, '0'),
                                                                                                                                   str(device.header.Month).rjust(2, '0'),
                                                                                                                                   str(device.header.Day).rjust(2, '0'),
                                                                                                                                   str(device.header.Hour).rjust(2, '0'),
                                                                                                                                   str(device.header.Minute).rjust(2, '0'),
                                                                                                                                   str(device.header.Second).rjust(2, '0')))
    else:
        logging.critical("Date and Time were unavailable on the device the Starting was aborted")
        ShowPopUp(window, "Date and Time were unavailable on the device the Starting was aborted")


def open_filename_window(window):
    global filename
    window.Disappear()
    if sys.platform.startswith('win'):
        window.Disable()
    else:
        window.Hide()
    if not os.path.exists("./save"):
        os.makedirs("./save")
    dirname = Sg.filedialog.askdirectory(initialdir="./save", title='Please select a directory')
    if device.header.SerialId is None:
        filename = Sg.filedialog.askopenfilename(initialdir=dirname if not None else "./save", title="Select file", filetypes=(("txt files", "*.txt"), ("all files", "*.*")))
    else:
        result = GetHeader()
        if result is not None:
            result = result[5:len(result) - 2].decode()
            logging.info("Header was successfully received, its content is : " + str(result))
            result = result.split(',')
            device.header.Model, device.header.SerialId, device.header.Coeff1, device.header.Coeff2, device.header.Coeff3, device.header.Coeff4 = result[:6]
            year, month, day, hour, minute, second, device.header.Interval, device.header.Samples = map(int, result[6:])
        else:
            logging.critical("Header failed on file selection")
            ShowPopUp(window, "Header failed on file selection")
            year, month, day, hour, minute, second = 0, 0, 0, 0, 0, 0
        filename = dirname + "/{}__{}_{}_{}__{}_{}_{}.Raw".format(device.header.SerialId, year, month, day, hour, minute, second)
    logging.info("Filename was set to {}".format(filename))
    window.Element("filename").Update(filename)
    window.Reappear()

    if sys.platform.startswith('win'):
        window.Enable()
    else:
        window.UnHide()
    pass


def open_delete_window(window):
    delete_layout = [[Sg.Text("Warning make sure to save the data first before erasing, this is Irremediable", text_color="red", font="Any 13", size=(50, 2))],
                     [Sg.Button('No do not erase', key="_delete_refused_", image_data=image_file_to_bytes(green_button, button_size), button_color=wcolor, pad=(50, 0)),
                      Sg.Button('Yes erase', key="_delete_granted_", image_data=image_file_to_bytes(red_button, button_size), button_color=wcolor, pad=(0, 0))]]
    window_delete = Sg.Window('Erase Data', delete_layout, keep_on_top=True)
    if sys.platform.startswith('win'):
        window.Disable()
    else:
        window.Hide()
    while True:
        button, values = window_delete.Read(timeout=100)
        if button is None:
            break
        if button == "_delete_granted_":
            if sys.platform.startswith('win'):
                window_delete.Disable()
            else:
                window_delete.Hide()
            logging.info("Data was asked to be erased")
            SendMessage("erase,")
            SendCommand("go,", "ok")
            header_handler(window)
            prime_state(window)
            DisplayHeader(window)
            window_delete.Close()
            break
        if button == "_delete_refused_":
            break

    if sys.platform.startswith('win'):
        window.Enable()
    else:
        window.UnHide()
    del delete_layout, window_delete, button, values
    return


def prime_state(window):
    keys = ["_serial_id_frame_", "_start_time_frame_", "_end_time_frame_", '_samples_frame_', '_current_date_frame_', '_model_frame_', '_coefficients_frame_', '_interval_frame_', '_header_frame_']
    for key in keys:
        set_none(window, key)


def validated_state(window):
    keys = ["_serial_id_frame_", "_start_time_frame_", "_end_time_frame_", '_samples_frame_', '_current_date_frame_', '_model_frame_', '_coefficients_frame_', '_interval_frame_', '_header_frame_']
    for key in keys:
        set_validated(window, key)


def open_model_window(window):
    model_layout = [[Sg.Input(do_not_clear=True, enable_events=True, key='_input_model_', default_text=device.header.Model, size=default_size),
                     Sg.Text("Warning do not change those settings if you are not sure, once written, there is no way of getting back the old ones", text_color="red", font="Any 13", size=(50, 2))],
                    [Sg.Button('Validate', key="_model_filled_", image_data=image_file_to_bytes(green_button, button_size), button_color=wcolor, pad=(300, 0))]]
    window_model = Sg.Window('Fill Serial Id', model_layout, keep_on_top=True)
    if sys.platform.startswith('win'):
        window.Disable()
    else:
        window.Hide()
    while True:
        button, values = window_model.Read(timeout=100)
        if button is None:
            break
        if button == "_model_filled_":
            device.header.Model = values['_input_model_'] if values['_input_model_'] else None
            logging.info("Model was changed to : {} ".format(device.header.Model))
            DisplayHeader(window)
            set_unvalidated(window, "_model_frame_")
            window_model.Close()
            break

    if sys.platform.startswith('win'):
        window.Enable()
    else:
        window.UnHide()
    del model_layout, window_model, button, values
    return


def open_start_time_window(window):
    start_time_layout = [[Sg.Spin(list(range(1, 10000)), initial_value=device.header.Year, enable_events=True, size=(4, 1), auto_size_text=True, font='Any 15',
                                  background_color=bcolor, text_color="white", key="_input_interval_year_"),
                          Sg.Text("Y", size=(2, 0)),
                          Sg.Spin(list(range(1, 13)), initial_value=device.header.Month, enable_events=True, size=(2, 1), auto_size_text=True, font='Any 15',
                                  background_color=bcolor, text_color="white", key="_input_interval_month_"),
                          Sg.Text("M", size=(2, 0)),
                          Sg.Spin(list(range(1, getMonthDays(device.header.Year, device.header.Month) + 1)), initial_value=device.header.Day, enable_events=True,
                                  size=(2, 1), auto_size_text=True, font='Any 15', background_color=bcolor, text_color="white", key="_input_interval_day_"),
                          Sg.Text("D", size=(2, 0)),
                          Sg.Spin(list(range(0, 24)), initial_value=device.header.Hour, enable_events=True,
                                  size=(2, 1), auto_size_text=True, font='Any 15', background_color=bcolor, text_color="white", key="_input_interval_hours_"),
                          Sg.Text("H", size=(2, 0)),
                          Sg.Spin(list(range(0, 60)), initial_value=device.header.Minute, enable_events=True, size=(2, 1), auto_size_text=True, font='Any 15',
                                  background_color=bcolor, text_color="white", key="_input_interval_minute_"),
                          Sg.Text("M", size=(2, 0)),
                          Sg.Spin(list(range(0, 60)), initial_value=device.header.Second, enable_events=True, size=(2, 1), auto_size_text=True, font='Any 15',
                                  background_color=bcolor, text_color="white", key="_input_interval_seconds_"),
                          Sg.Text("S", size=(2, 0))],
                         [Sg.Button('Validate', key="_start_time_filled_", image_data=image_file_to_bytes(green_button, button_size), button_color=wcolor, pad=(150, 0))]]
    window_start_time = Sg.Window('Fill Start Time', start_time_layout, keep_on_top=True)
    if sys.platform.startswith('win'):
        window.Disable()
    else:
        window.Hide()
    while True:
        button, values = window_start_time.Read(timeout=10)
        if button is None:
            break
        checkIntInput(0, 59, values, "_input_interval_seconds_", window_start_time)
        checkIntInput(0, 59, values, "_input_interval_minute_", window_start_time)
        checkIntInput(0, 23, values, "_input_interval_hours_", window_start_time)
        checkIntInput(1, 12, values, "_input_interval_month_", window_start_time)
        checkIntInput(1, 9999, values, "_input_interval_year_", window_start_time)
        checkIntInput(1, getMonthDays(values["_input_interval_year_"], values["_input_interval_month_"]), values, "_input_interval_day_", window_start_time)
        if button == "_start_time_filled_":
            logging.info("Start time was updated to : {}/{}/{} {}:{}:{}".format(values["_input_interval_year_"], values["_input_interval_month_"], values["_input_interval_day_"],
                                                                                values["_input_interval_hours_"], values["_input_interval_minute_"], values["_input_interval_seconds_"]))
            device.header.Year, device.header.Month, device.header.Day, \
            device.header.Hour, device.header.Minute, device.header.Second = values["_input_interval_year_"], values["_input_interval_month_"], values["_input_interval_day_"], \
                                                                             values["_input_interval_hours_"], values["_input_interval_minute_"], values["_input_interval_seconds_"]
            DisplayHeader(window)
            set_unvalidated(window, "_start_time_frame_")
            window_start_time.Close()
            break

    if sys.platform.startswith('win'):
        window.Enable()
    else:
        window.UnHide()
    del start_time_layout, window_start_time, button, values
    return


def open_serial_id_window(window):
    serial_id_layout = [[Sg.Input(do_not_clear=True, enable_events=True, key='_input_serial_id_', default_text=device.header.SerialId, size=default_size),
                         Sg.Text("Warning do not change those settings if you are not sure, once written, there is no way of getting back the old ones", text_color="red", font="Any 13",
                                 size=(50, 2))],
                        [Sg.Button('Validate', key="_serial_id_filled_", image_data=image_file_to_bytes(green_button, button_size), button_color=wcolor, pad=(300, 0))]]
    window_serial_id = Sg.Window('Fill Serial Id', serial_id_layout, keep_on_top=True)
    if sys.platform.startswith('win'):
        window.Disable()
    else:
        window.Hide()
    while True:
        button, values = window_serial_id.Read(timeout=100)
        if button is None:
            break
        if button == "_serial_id_filled_":
            device.header.SerialId = values['_input_serial_id_'] if values['_input_serial_id_'] else None
            logging.info("Serial Id was changed to : {} ".format(device.header.SerialId))
            DisplayHeader(window)
            set_unvalidated(window, "_serial_id_frame_")
            window_serial_id.Close()
            break

    if sys.platform.startswith('win'):
        window.Enable()
    else:
        window.UnHide()
    del serial_id_layout, window_serial_id, button, values
    return


def open_current_time_window(window):
    device.header.currentDate = device.header.currentDate + (datetime.datetime.now() - device.header.dateTimeNow)
    device.header.dateTimeNow = datetime.datetime.now()
    now = device.header.currentDate
    current_time_layout = [[Sg.Spin(list(range(1, 10000)), initial_value=now.year, enable_events=True, size=(4, 1), auto_size_text=True, font='Any 15',
                                    background_color=bcolor, text_color="white", key="_input_interval_year_"),
                            Sg.Text("Y", size=(2, 0)),
                            Sg.Spin(list(range(1, 13)), initial_value=now.month, enable_events=True, size=(2, 1), auto_size_text=True, font='Any 15',
                                    background_color=bcolor, text_color="white", key="_input_interval_month_"),
                            Sg.Text("M", size=(2, 0)),
                            Sg.Spin(list(range(1, getMonthDays(now.year, now.month) + 1)), initial_value=now.day, enable_events=True,
                                    size=(2, 1), auto_size_text=True, font='Any 15', background_color=bcolor, text_color="white", key="_input_interval_day_"),
                            Sg.Text("D", size=(2, 0)),
                            Sg.Spin(list(range(0, 24)), initial_value=now.hour, enable_events=True,
                                    size=(2, 1), auto_size_text=True, font='Any 15', background_color=bcolor, text_color="white", key="_input_interval_hours_"),
                            Sg.Text("H", size=(2, 0)),
                            Sg.Spin(list(range(0, 60)), initial_value=now.minute, enable_events=True, size=(2, 1), auto_size_text=True, font='Any 15',
                                    background_color=bcolor, text_color="white", key="_input_interval_minute_"),
                            Sg.Text("M", size=(2, 0)),
                            Sg.Spin(list(range(0, 60)), initial_value=now.second, enable_events=True, size=(2, 1), auto_size_text=True, font='Any 15',
                                    background_color=bcolor, text_color="white", key="_input_interval_seconds_"),
                            Sg.Text("S", size=(2, 0))],
                           [Sg.Button('Set to The Current Time', key="_current_time_fill_", image_data=image_file_to_bytes(blue_button, button_size), button_color=wcolor, pad=((100, 0), 0)),
                            Sg.Button('Validate', key="_current_time_filled_", image_data=image_file_to_bytes(green_button, button_size), button_color=wcolor, pad=(0, 0))]]
    window_current_time = Sg.Window('Set Current Time For The Device', current_time_layout, keep_on_top=True)
    if sys.platform.startswith('win'):
        window.Disable()
    else:
        window.Hide()
    while True:
        button, values = window_current_time.Read(timeout=10)
        if button is None:
            set_unvalidated(window, "_current_date_frame_")
            break
        checkIntInput(0, 59, values, "_input_interval_seconds_", window_current_time)
        checkIntInput(0, 59, values, "_input_interval_minute_", window_current_time)
        checkIntInput(0, 23, values, "_input_interval_hours_", window_current_time)
        checkIntInput(1, 12, values, "_input_interval_month_", window_current_time)
        checkIntInput(1, 9999, values, "_input_interval_year_", window_current_time)
        checkIntInput(1, getMonthDays(values["_input_interval_year_"], values["_input_interval_month_"]), values, "_input_interval_day_", window_current_time)
        # Set to current date
        if button == "_current_time_fill_":
            device.header.currentDate = datetime.datetime.now()
            device.header.dateTimeNow = datetime.datetime.now()
            logging.info("Date was updated to the current date : " + ", ".join(map(str, device.header.currentDate.timetuple())))
        else:
            device.header.currentDate = datetime.datetime(values["_input_interval_year_"], values["_input_interval_month_"],
                                                          min(getMonthDays(values["_input_interval_year_"], values["_input_interval_month_"]), values["_input_interval_day_"]),
                                                          values["_input_interval_hours_"], values["_input_interval_minute_"], values["_input_interval_seconds_"])
            device.header.dateTimeNow = datetime.datetime.now()
        # update method
        if device.header.currentDate is not None:
            device.header.currentDate = device.header.currentDate + (datetime.datetime.now() - device.header.dateTimeNow)
            device.header.dateTimeNow = datetime.datetime.now()
            now = device.header.currentDate
            window_current_time.Element('_input_interval_year_').Update(now.year)
            window_current_time.Element('_input_interval_month_').Update(now.month)
            window_current_time.Element('_input_interval_day_').Update(now.day)
            window_current_time.Element('_input_interval_hours_').Update(now.hour)
            window_current_time.Element('_input_interval_minute_').Update(now.minute)
            window_current_time.Element('_input_interval_seconds_').Update(now.second)
        # Validate
        if button == "_current_time_filled_":
            device.header.dateTimeNow = datetime.datetime.now()
            device.header.currentDate = datetime.datetime(values["_input_interval_year_"], values["_input_interval_month_"], values["_input_interval_day_"],
                                                          values["_input_interval_hours_"], values["_input_interval_minute_"], values["_input_interval_seconds_"])
            logging.info("Date was updated to : " + ", ".join(map(str, device.header.currentDate.timetuple())))
            current_start_time = datetime.datetime(device.header.Year, device.header.Month, device.header.Day, device.header.Hour, device.header.Minute, device.header.Second)
            if current_start_time < device.header.currentDate:
                device.header.Year, device.header.Month, device.header.Day, device.header.Hour, device.header.Minute, device.header.Second, k, l, m = device.header.currentDate.timetuple()
                set_unvalidated(window, "_start_time_frame_")
                logging.info("Starting date was updated to : " + ", ".join(map(str, current_start_time.timetuple())))
            DisplayHeader(window)
            if sys.platform.startswith('win'):
                window_current_time.Disable()
            else:
                window_current_time.Hide()
            if not SendMessage("date,{},{},{},".format(values["_input_interval_year_"], values["_input_interval_month_"], values["_input_interval_day_"])):
                ShowPopUp(window, "Setting the Date on the device failed", "this is unprecedented, please check the connection")
                header_handler(window)
                break
            if not SendMessage("time,{},{},{},".format(values["_input_interval_hours_"], values["_input_interval_minute_"], values["_input_interval_seconds_"])):
                ShowPopUp(window, "Setting the Time on the device failed", "this is unprecedented, please check the connection")
                header_handler(window)
                break
            set_validated(window, "_current_date_frame_")
            break

    if sys.platform.startswith('win'):
        window_current_time.Enable()
    else:
        window_current_time.UnHide()
    window_current_time.Close()

    if sys.platform.startswith('win'):
        window.Enable()
    else:
        window.UnHide()
    del current_time_layout, window_current_time, button, values
    return


def open_end_time_window(window):
    year, month, day, hour, minute, second = calculateFutureDate(device.header.Year, device.header.Month, device.header.Day, device.header.Hour,
                                                                 device.header.Minute, device.header.Second, device.header.Samples, device.header.Interval)
    end_time_layout = [[Sg.Spin(list(range(1, 10000)), initial_value=year, enable_events=True, size=(4, 1), auto_size_text=True, font='Any 15',
                                background_color=bcolor, text_color="white", key="_input_interval_year_"),
                        Sg.Text("Y", size=(2, 0)),
                        Sg.Spin(list(range(1, 13)), initial_value=month, enable_events=True, size=(2, 1), auto_size_text=True, font='Any 15',
                                background_color=bcolor, text_color="white", key="_input_interval_month_"),
                        Sg.Text("M", size=(2, 0)),
                        Sg.Spin(list(range(1, getMonthDays(year, month) + 1)), initial_value=day, enable_events=True,
                                size=(2, 1), auto_size_text=True, font='Any 15', background_color=bcolor, text_color="white", key="_input_interval_day_"),
                        Sg.Text("D", size=(2, 0)),
                        Sg.Spin(list(range(0, 24)), initial_value=hour, enable_events=True,
                                size=(2, 1), auto_size_text=True, font='Any 15', background_color=bcolor, text_color="white", key="_input_interval_hours_"),
                        Sg.Text("H", size=(2, 0)),
                        Sg.Spin(list(range(0, 60)), initial_value=minute, enable_events=True, size=(2, 1), auto_size_text=True, font='Any 15',
                                background_color=bcolor, text_color="white", key="_input_interval_minute_"),
                        Sg.Text("M", size=(2, 0)),
                        Sg.Spin(list(range(0, 60)), initial_value=second, enable_events=True, size=(2, 1), auto_size_text=True, font='Any 15',
                                background_color=bcolor, text_color="white", key="_input_interval_seconds_"),
                        Sg.Text("S", size=(2, 0))],
                       [Sg.Button('Validate', key="_end_time_filled_", image_data=image_file_to_bytes(green_button, button_size), button_color=wcolor, pad=(150, 0))]]
    window_end_time = Sg.Window('Fill End Time', end_time_layout, keep_on_top=True, finalize=True)
    if sys.platform.startswith('win'):
        window.Disable()
    else:
        window.Hide()
    while True:
        button, values = window_end_time.Read(timeout=10)
        if button is None:
            break
        checkIntInput(0, 59, values, "_input_interval_seconds_", window_end_time)
        checkIntInput(0, 59, values, "_input_interval_minute_", window_end_time)
        checkIntInput(0, 23, values, "_input_interval_hours_", window_end_time)
        checkIntInput(1, 12, values, "_input_interval_month_", window_end_time)
        checkIntInput(1, 9999, values, "_input_interval_year_", window_end_time)
        checkIntInput(1, getMonthDays(values["_input_interval_year_"], values["_input_interval_month_"]), values, "_input_interval_day_", window_end_time)
        if button == "_end_time_filled_":
            logging.info("End time was updated to : {}/{}/{} {}:{}:{}".format(values["_input_interval_year_"], values["_input_interval_month_"], values["_input_interval_day_"],
                                                                              values["_input_interval_hours_"], values["_input_interval_minute_"], values["_input_interval_seconds_"]))
            current_end_time = datetime.datetime(values["_input_interval_year_"], values["_input_interval_month_"], values["_input_interval_day_"],
                                                 values["_input_interval_hours_"], values["_input_interval_minute_"], values["_input_interval_seconds_"])
            old_end_time = datetime.datetime(year, month, day, hour, minute, second)
            current_start_time = datetime.datetime(device.header.Year, device.header.Month, device.header.Day, device.header.Hour, device.header.Minute, device.header.Second)

            if current_end_time < current_start_time:
                current_end_time = old_end_time
                logging.info("End time was changed to due to being under start time : " + ", ".join(map(str, current_end_time.timetuple())))
            if device.header.Interval is None or device.header.Interval == 0:
                if int((current_end_time - current_start_time).total_seconds() + 1) > MAX_SAMPLES:
                    device.header.Interval = int(int((current_end_time - current_start_time).total_seconds()) // MAX_SAMPLES + 1)
                    device.header.Samples = int(int((current_end_time - current_start_time).total_seconds()) // device.header.Interval + 1)
                else:
                    device.header.Interval = 1
                    device.header.Samples = int((current_end_time - current_start_time).total_seconds() + 1)
                set_unvalidated(window, "_interval_frame_")
            else:
                if int(int((current_end_time - current_start_time).total_seconds()) // device.header.Interval + 1) > MAX_SAMPLES:
                    device.header.Interval = int(int((current_end_time - current_start_time).total_seconds()) // MAX_SAMPLES + 1)
                    device.header.Samples = int(int((current_end_time - current_start_time).total_seconds()) // device.header.Interval + 1)
                else:
                    device.header.Samples = int(int((current_end_time - current_start_time).total_seconds()) // device.header.Interval + 1)
            logging.info("Samples were set to : " + str(device.header.Samples))
            logging.info("Interval was set to : " + str(device.header.Interval))
            DisplayHeader(window)
            set_unvalidated(window, "_samples_frame_")
            set_unvalidated(window, "_end_time_frame_")
            window_end_time.Close()
            break

    if sys.platform.startswith('win'):
        window.Enable()
    else:
        window.UnHide()
    del end_time_layout, window_end_time, button, values
    return


def open_interval_window(window):
    interval_layout = [[Sg.DropDown([1, 60, 120, 600], default_value=1, key="_interval_value_"), Sg.Text("Seconds")],
                       [Sg.Button('Validate', key="_interval_filled_", image_data=image_file_to_bytes(green_button, button_size), button_color=wcolor, pad=(150, 0))]]
    window_interval = Sg.Window('Fill Interval Between Samples', interval_layout, keep_on_top=True)
    if sys.platform.startswith('win'):
        window.Disable()
    else:
        window.Hide()
    while True:
        button, values = window_interval.Read(timeout=10)
        if button is None:
            break
        if values["_interval_value_"] not in [1, 60, 120, 600]:
            window_interval.Element("_interval_value_").Update(1)
        if button == "_interval_filled_":
            device.header.Interval = values['_interval_value_'] if values['_interval_value_'] is not None else 0
            logging.info("Interval was changed to : {} ".format(device.header.Interval))
            DisplayHeader(window)
            set_unvalidated(window, "_interval_frame_")
            set_unvalidated(window, "_end_time_frame_")
            window_interval.Close()
            break

    if sys.platform.startswith('win'):
        window.Enable()
    else:
        window.UnHide()
    del interval_layout, window_interval, button, values
    return


def open_samples_window(window):
    sample_layout = [[Sg.Spin(list(range(0, MAX_SAMPLES)), initial_value=device.header.Samples, enable_events=True, size=(7, 1), auto_size_text=True, font='Any 15',
                              background_color=bcolor, text_color="white", key="_input_samples_", pad=((120, 0), 0)),
                      Sg.Text("samples\n (limited to " + str(MAX_SAMPLES) + ")", size=(30, 0))],
                     [Sg.Button('Validate', key="_samples_filled_", image_data=image_file_to_bytes(green_button, button_size), button_color=wcolor, pad=(150, 0))]]
    window_sample = Sg.Window('Fill Number of Samples', sample_layout, keep_on_top=True)
    if sys.platform.startswith('win'):
        window.Disable()
    else:
        window.Hide()
    while True:
        button, values = window_sample.Read(timeout=10)
        if button is None:
            break
        checkIntInput(0, MAX_SAMPLES, values, "_input_samples_", window_sample)
        if button == "_samples_filled_":
            device.header.Samples = values['_input_samples_'] if values['_input_samples_'] is not None else 0
            logging.info("Sample Number was changed to : {} ".format(device.header.Samples))
            DisplayHeader(window)
            set_unvalidated(window, "_end_time_frame_")
            set_unvalidated(window, "_samples_frame_")
            window_sample.Close()
            break

    if sys.platform.startswith('win'):
        window.Enable()
    else:
        window.UnHide()
    del sample_layout, window_sample, button, values
    return


def open_coefficient_window(window):
    coefficient_layout = [[Sg.Input(do_not_clear=True, enable_events=True, key='_input_coeff1_', default_text=device.header.Coeff1, size=default_size),
                           Sg.Input(do_not_clear=True, enable_events=True, key='_input_coeff2_', default_text=device.header.Coeff2, size=default_size)],
                          [Sg.Input(do_not_clear=True, enable_events=True, key='_input_coeff3_', default_text=device.header.Coeff3, size=default_size),
                           Sg.Input(do_not_clear=True, enable_events=True, key='_input_coeff4_', default_text=device.header.Coeff4, size=default_size)],
                          [Sg.Button('Validate', key="_coefficent_filled_", image_data=image_file_to_bytes(green_button, button_size), button_color=wcolor, pad=(150, 0))]]

    window_coefficent = Sg.Window('Fill Coefficients', coefficient_layout, keep_on_top=True)
    if sys.platform.startswith('win'):
        window.Disable()
    else:
        window.Hide()
    while True:

        button, values = window_coefficent.Read(timeout=100)
        if button is None:
            break
        for i in range(1, 5):
            key = '_input_coeff{}_'.format(i)
            if len(values[key]) and values[key][-1] not in ('0123456789.eE-'):  # if last char entered not a digit
                window_coefficent.Element(key).Update(values[key][:-1])  # delete last char from input
        if button == "_coefficent_filled_":
            device.header.Coeff1 = values['_input_coeff1_'] if values['_input_coeff1_'] else None
            device.header.Coeff2 = values['_input_coeff2_'] if values['_input_coeff2_'] else None
            device.header.Coeff3 = values['_input_coeff3_'] if values['_input_coeff3_'] else None
            device.header.Coeff4 = values['_input_coeff4_'] if values['_input_coeff4_'] else None
            logging.info("Coefficients were changed to : {} {} {} {}".format(device.header.Coeff1, device.header.Coeff2, device.header.Coeff3, device.header.Coeff4))
            DisplayHeader(window)
            set_unvalidated(window, "_coefficients_frame_")
            window_coefficent.Close()
            break

    if sys.platform.startswith('win'):
        window.Enable()
    else:
        window.UnHide()
    del coefficient_layout, window_coefficent, button, values
    return


def set_unvalidated(window, element):
    window.Element(element).TKFrame.configure(foreground="orange")


def set_warning(window, element):
    window.Element(element).TKFrame.configure(foreground="red")


def set_validated(window, element):
    window.Element(element).TKFrame.configure(foreground="green")


def set_none(window, element):
    window.Element(element).TKFrame.configure(foreground="white")


def toggle_buttons(window, flag, up_message, down_message, *button_keys):
    if flag:
        disabled_state = False
        logging.info(up_message)
    else:
        disabled_state = True
        logging.info(down_message)
    for key in button_keys:
        window.Element(key).Update(disabled=disabled_state)


def DisplayHeader(window):
    window.Element('_serialID_').Update(device.header.SerialId)
    window.Element('_coefficients_').Update("{} {}\n{} {}".format(device.header.Coeff1, device.header.Coeff2, device.header.Coeff3, device.header.Coeff4))
    window.Element('_starting_date_').Update("{}/{}/{} {}:{}:{}".format(device.header.Year, device.header.Month, device.header.Day, device.header.Hour, device.header.Minute, device.header.Second))
    window.Element('_model_').Update(device.header.Model)
    window.Element('_sample_').Update(device.header.Samples)
    year, month, day, hour, minute, second = calculateFutureDate(device.header.Year, device.header.Month, device.header.Day, device.header.Hour,
                                                                 device.header.Minute, device.header.Second, device.header.Samples, device.header.Interval)
    window.Element('_ending_date_').Update("{}/{}/{} {}:{}:{}".format(year, month, day, hour, minute, second))
    window.Element('_interval').Update(device.header.Interval)
    if device.header.currentDate is None:
        window.Element('_current_date_').Update("{}/{}/{} {}:{}:{}".format(None, None, None, None, None, None))
    else:
        now = device.header.currentDate
        window.Element('_current_date_').Update("{}/{}/{} {}:{}:{}".format(now.year, now.month, now.day, now.hour, now.minute, now.second))


def connect_handler(window, values):
    global flag_change,filename
    logging.info("Starting a connection session")
    if device.connected:
        if not device.sleep:
            sleep_handler(window,values)

        result = Disconnect()
        if result is None or not result:
            window.Element('_connect_').Update("Connect", image_data=image_file_to_bytes(green_button, button_size))
            window.Element('_device_connection_').TKFrame.configure(text='Device Connection (OFF)')
            set_warning(window, "_device_connection_")
            logging.info("Device was disconnected and the color has been set to green")
            device.connected = not device.connected

        else:
            logging.critical("Connection Error")
    else:
        result = Connect(values["_portList_"])
        if result is not None and result:
            window.Element('_connect_').Update("Disconnect", image_data=image_file_to_bytes(red_button, button_size))
            window.Element('_device_connection_').TKFrame.configure(text='Device Connection (ON)')
            set_validated(window, "_device_connection_")
            logging.info("Device was connected and the color has been set to red")
            filename=""
            device.header=Header()
            DisplayHeader(window)
            device.connected = not device.connected
        else:
            logging.critical("Connection Error")
    flag_change = True


def header_handler(window):
    global flag_change
    if not device.sleep and device.connected:
        # Get Header with coefficients, serial id, type of model, samples number, interval and start time saved to it
        result = GetHeader()
        if result is not None:
            result = result[5:len(result) - 2].decode()
            logging.info("Header was successfully received, its content is : " + str(result))
            result = result.split(',')
            device.header.Model, device.header.SerialId, device.header.Coeff1, device.header.Coeff2, device.header.Coeff3, device.header.Coeff4 = result[:6]
            year, month, day, hour, minute, second, device.header.Interval, device.header.Samples = map(int, result[6:])
            device.header.Year, device.header.Month, device.header.Day, device.header.Hour, device.header.Minute, device.header.Second = validateDate(year, month, day, hour, minute, second)
        else:
            logging.critical("The Header collection failed, please report this bug")
            ShowPopUp(window, "The Header collection failed", "Please report this bug")

        # Get Date saved on device as Year, month and day
        date = GetCurrentDate()
        # Get Time saved on device as Hour, Minute and Seconds
        time = GetCurrentTime()
        if date is not None and time is not None:
            date = date[7:len(date) - 2].decode()
            logging.info("Current Date was successfully received, its content is : " + str(date))
            time = time[7:len(time) - 2].decode()
            logging.info("Current Time was successfully received, its content is : " + str(time))
            year, month, day = map(int, date.split(','))
            hour, minute, second = map(int, time.split(','))
            year, month, day, hour, minute, second = validateDate(year, month, day, hour, minute, second)
            device.header.currentDate = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
            current_start_time = datetime.datetime(device.header.Year, device.header.Month, device.header.Day, device.header.Hour, device.header.Minute, device.header.Second)
            if current_start_time < device.header.currentDate:
                device.header.Year, device.header.Month, device.header.Day, device.header.Hour, device.header.Minute, device.header.Second, k, l, m = device.header.currentDate.timetuple()
                set_unvalidated(window, "_start_time_frame_")
                logging.info("Starting date was updated to : " + ", ".join(map(str, current_start_time.timetuple())))
            device.header.dateTimeNow = datetime.datetime.now()
            DisplayHeader(window)
        else:
            logging.critical("The Date or/and time collection failed, please report this bug")
            ShowPopUp(window, "The Date or/and time collection failed", "Please report this bug")

    else:
        logging.critical("The Device is asleep or disconnected, the header was not collected")
    flag_change = True


def ShowPopUp(window, *args):
    if sys.platform.startswith('win'):
        window.Disable()
    else:
        window.Hide()
    Sg.Popup(*args, title="Error Pop Up", button_color=("blue", "white"), background_color="red", text_color="white", button_type=0, auto_close=False, line_width=60,
             no_titlebar=True, grab_anywhere=True, keep_on_top=True)

    if sys.platform.startswith('win'):
        window.Enable()
    else:
        window.UnHide()


def ShowConfirmation(window, *args):
    if sys.platform.startswith('win'):
        window.Disable()
    else:
        window.Hide()
    Sg.Popup(*args, title="Confirmation Pop Up", button_color=("blue", "white"), background_color="green", text_color="blue", button_type=0, auto_close=False, line_width=60,
             no_titlebar=True, grab_anywhere=True, keep_on_top=True)

    if sys.platform.startswith('win'):
        window.Enable()
    else:
        window.UnHide()


def sleep_handler(window, values):
    global flag_change
    if device.connected:
        if device.sleep:
            result = WakeUp()
            if result:
                window.Element('_wakeup_').Update("Sleep", image_data=image_file_to_bytes(green_button, button_size))
                window.Element('_device_control_').TKFrame.configure(text='Device Controls (Awake)')
                set_validated(window, '_device_control_')
                device.sleep = not device.sleep
                logging.info("Device has been put into active mode and color has been set to green")
                prime_state(window)
            else:
                logging.critical("Device failed to wake up")
                ShowPopUp(window, 'The Device did not respond to the wake up call',
                          'That mean that you should turn off the manual power switch and turn it on again',
                          'You should also reconnect on the Software side ')
                connect_handler(window, values)
        else:
            result = Sleep()
            if result:
                window.Element('_wakeup_').Update("Wake Up", image_data=image_file_to_bytes(red_button, button_size))
                window.Element('_device_control_').TKFrame.configure(text='Device Controls (Asleep)')
                set_warning(window, '_device_control_')
                device.sleep = not device.sleep
                logging.info("Device has been put into sleeping mode and color has been set to red")
            else:
                ShowPopUp(window, 'The Device did not respond to the sleeping call',
                          'That mean that you might have to redo the process again, this error is undocumented yet',
                          'You may have forgotten to turn on the power brick')
                logging.critical("Device failed to sleep")
    else:
        logging.critical("Device was not connected while trying to wake up/sleep")
    flag_change = True
