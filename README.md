RS232-MDS-MKV-Alec.Co

---
For general use:

On Windows: 

(- Install the drivers (for win10 1804+ make sure to install prolific 3.8.28.0 or below driver else it will not work) : https://www.ugreen.com/drivers/list-USB_To_RS232_Driver-en.html) (optional try first the release)

- Go in the release : https://github.com/ErwanKESSLER/RS232-MDS-MKV-Alec.Co/releases/tag/0.1win and execute the .exe (if not working please build from the sources you will need python 3.7 from their site and then from (1) steps in the HOW TO)

On linux

(- Install the drivers : https://www.ugreen.com/upload/file/FTDI232_Linux.zip) ( optional, try to see if it is available in /dev/ttyUSB0 or /dev/ttyS0 ...)

- Install tk with `sudo apt install python-tk` or `sudo pacman -S tk` (or yay...)

- Run the release file https://github.com/ErwanKESSLER/RS232-MDS-MKV-Alec.Co/releases/tag/0.1linux (there is different one depending of your OS, if it doesnt run out of the box, please build from sources) with sudo to access /dev/tty ports

------

**ONE LINE RUNNER (for apt based)**

`sudo apt-get update && sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install git curl python3.7 python3.7-tk && 
git clone https://github.com/ErwanKESSLER/RS232-MDS-MKV-Alec.Co && cd RS232-MDS-MKV-Alec.Co && 
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && sudo python3.7 get-pip.py && rm get-pip.py && 
sudo python3.7 -m pip install -r requirements.txt && sudo python3.7 -m pip install -U Pillow  && 
sudo python3.7 MDSMKV/main.py `


**ONE LINER BUILDER (for apt based)**


`sudo apt-get update && sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install git curl python3.7 python3.7-tk 
python3.7-dev && git clone https://github.com/ErwanKESSLER/RS232-MDS-MKV-Alec.Co && cd RS232-MDS-MKV-Alec.Co && 
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && sudo python3.7 get-pip.py && rm get-pip.py && 
sudo python3.7 -m pip install -r requirements.txt && sudo python3.7 -m pip install pyinstaller &&
sudo python3.7 -m pip install -U Pillow && cd MDSMKV && pyinstaller --onefile main.py --distpath Release --clean -n MDSMKV 
&& sudo Release/MDSMKV` 

**HOW TO BUILD FROM SOURCES**

- First and foremost, please run `sudo apt-get update` or `pacman -Sy` to update your cache

- You need git and curl so if you dont have them, please do `sudo apt install git curl` or `sudo pacman -S git curl`

- Clone the repository `git clone https://github.com/ErwanKESSLER/RS232-MDS-MKV-Alec.Co` and cd to it `cd RS232-MDS-MKV-Alec.Co`

- Install Python 3.7+ with `sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt install python3.7` or `sudo pacman -S python3.7` (or yay...)

- Install Tk on linux `sudo apt install python3.7-tk` or `sudo pacman -S tk` (or yay...)

- Install pip if not available `curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && sudo python3.7 get-pip.py && rm get-pip.py`

- Do `sudo python3.7 -m pip install -r requirements.txt` at the folder root (1)

- You can try to run the program directly: `sudo python3.7 MDSMKV/main.py`

- If there is an error with PIL in it then you need to run that `sudo python3.7 -m pip install -U Pillow`

**TO FREEZE (CREATE AN EXECUTABLE OF) THE PROGRAM ON YOUR MACHINE (AND POSSIBLY OTHERS)**

- Do `sudo apt install python3.7-dev`

- Do `sudo python3.7 -m pip install pyinstaller`

- Do `cd MDSMKV && pyinstaller --onefile main.py --distpath Release --clean -n MDSMKV`

- You can now run your release file from the Release folder with `sudo Release/MDSMKV` 

*Warning it is recommended to execute in sudo so you can access the /dev/tty port, you can also make them usable for standard user but it requires to modify the system*

if needed :

- https://www.ugreen.com/drivers/list-USB_To_RS232_Driver-en.html collect the correct rs232 driver


----
