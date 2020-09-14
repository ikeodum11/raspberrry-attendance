import time
import sqlite3
import os
import datetime
import time  # used for sleep command
import sys
import pyfingerprint # for the fingerprint sensor
from pad4pi import rpi_gpio  # for keypad
from pyfingerprint import PyFingerprint
import hashlib
import I2C_LCD_driver


mylcd = I2C_LCD_driver.lcd()

pressed_keys = ''
pin = "0000"
fun = ''
month = ''
year = ''
first_initial = ''
last_initial = ''
employ_number = ''
employee = ''
r = ''
person = ''
# 

day = datetime.date.today().strftime("%m-%d-%y")  # clean date
timestamp = time.strftime('%I:%M %p')  # is called in function to update

## Tries to initialize the sensor
def finger():
    try:
        f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)
    except Exception:
        print('The fingerprint sensor could not be initialized!')
        print('')
        main_menu()
    else:
        print('Currently used templates: ' + str(f.getTemplateCount()))
        print('')
        print_grab()

# read fingerprint
def print_grab():
    global person
    try:
        f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)
        mylcd.lcd_clear()
        mylcd.lcd_display_string('*Waiting For Finger*', 2)
        print('*Waiting For Finger*')
        print('')
        ## Wait that finger is read
        while f.readImage() == False:
            pass
        ## Converts read image to characteristics and stores it in charbuffer 1
        f.convertImage(0x01)

        ## Searches template
        result = f.searchTemplate()

        positionNumber = result[0]

        if positionNumber == -1:
            mylcd.lcd_clear()
            mylcd.lcd_display_string('   No Match Found', 2)
            print('No match found')
            print('')
            time.sleep(2)
            main_menu()
        else:
            print('Found template at position #' + str(positionNumber))
            print('')
            mylcd.lcd_clear()
            mylcd.lcd_display_string('    PLEASE  WAIT', 2)
            print('PLEASE WAIT')
            print('')

            ## Create Hash Value for finger
            ## Loads the found template to charbuffer 1
            f.loadTemplate(positionNumber, 0x01)
            ## Downloads the characteristics of template loaded in charbuffer 1
            characteristics = str(f.downloadCharacteristics(0x01)).encode(
                'utf-8')
            hashval = hashlib.sha256(characteristics).hexdigest()
            ## Hashes characteristics of template
            print('SHA-2 hash of template: ' + hashval)
            print('')
           #GETTING INFORMATION FROM DATABASE
            conn = sqlite3.connect('/home/pi/Desktop/beta/employee.db')
            c = conn.cursor()
            c.execute('SELECT * FROM finger_store WHERE id=?',
                      [positionNumber])
            db_val = c.fetchall()
            for row in db_val:
                person = row[0]
                mylcd.lcd_clear()
                mylcd.lcd_display_string('     ID NUMBER:', 2)
                mylcd.lcd_display_string('    ' + person, 3)
                print("YOUR ID NUMBER:" + person)
                print('')
                time.sleep(2)
            conn.commit()
            conn.close()
            check_if_in()
    except Exception as e:
        print(e)


def check_if_in():
    global person
    conn = sqlite3.connect('/home/pi/Desktop/beta/employee.db')
    c = conn.cursor()
    date = datetime.date.today().strftime("%m-%d-%y")
    c.execute('SELECT status_in FROM employee '
              'WHERE employ_num = ? AND date = ?', [person, date])
    conn.commit()
    result = c.fetchone()
    if result is None:
        write_in()
    else:
        check_if_out()


def write_in():
    conn = sqlite3.connect('/home/pi/Desktop/beta/employee.db')
    c = conn.cursor()
    status_in = 'IN'
    timestamp = time.strftime('%I:%M %p')
    day = datetime.date.today().strftime('%m-%d-%y')
    c.execute("INSERT INTO employee (employ_num, date, status_in, time_in) "
              "VALUES(?, ?, ?, ?)", [person, day, status_in, timestamp])
    mylcd.lcd_clear()
    mylcd.lcd_display_string(' Sign In Successful', 2)
    print('Sign In Successful')
    print('')
    time.sleep(2)
    conn.commit()
    conn.close()
    main_menu()


def check_if_out():
    conn = sqlite3.connect('/home/pi/Desktop/beta/employee.db')
    c = conn.cursor()
    date = datetime.date.today().strftime("%m-%d-%y")
    c.execute('SELECT status_out FROM employee '
              'WHERE employ_num = ? AND date = ?', [person, date])
    conn.commit()
    result = c.fetchone()
    convert = ''.join(map(str, result))
    if convert == 'None':
        write_out()
    else:
        mylcd.lcd_clear()
        mylcd.lcd_display_string('  You Have Already', 1)
        mylcd.lcd_display_string('  Signed IN & OUT', 2)
        mylcd.lcd_display_string('       Today', 3)
        print('You have already signed in and out for today')
        print('')
        time.sleep(2)
        main_menu()


def write_out():
    conn = sqlite3.connect('/home/pi/Desktop/beta/employee.db')
    c = conn.cursor()
    date = datetime.date.today().strftime("%m-%d-%y")
    timestamp = time.strftime('%I:%M %p')
    c.execute("UPDATE employee SET status_out = 'OUT' "
              "WHERE employ_num = ? and date = ?", [person, date])
    c.execute("UPDATE employee SET time_out = ? "
              "WHERE employ_num = ? and date = ?", [timestamp, person, date])
    mylcd.lcd_clear()
    mylcd.lcd_display_string(' Sign Out Successful', 2)
    print('Sign Out Successful')
    print('')
    time.sleep(2)
    conn.commit()
    conn.close()
    main_menu()

# the following code is for registering a user
# admin data entry
def password():
    global fun
    fun = fun.replace(fun, 'password')
    mylcd.lcd_clear()
    mylcd.lcd_display_string('      Password', 2)
    print("Password")
    print('')


def password_input(key):
    global pressed_keys
    global pin
    if key == '#':
        print(pressed_keys)
        if pressed_keys == pin:
            clear_keys()
            employ_month()
            admin_menu()
        else:
            mylcd.lcd_clear()
            mylcd.lcd_display_string(' Incorrect Password', 2)
            print('Incorrect Password')
            print('')
            time.sleep(2)
            main_menu()
    else:
        pressed_keys += key


def admin_menu():
    global fun
    clear_keys()
    mylcd.lcd_clear()
    fun = fun.replace(fun, 'admin_menu')
    mylcd.lcd_display_string('1. Register User', 1)
    mylcd.lcd_display_string('2. Main Menu', 2)
    print('1. Register employee')
    print('2. Main Menu')
    print('')


def admin_input(key):
    global pressed_keys
    if key == '#':
        print(pressed_keys)
        if pressed_keys == "1":
            print("send to employ_month")
            print('')
            clear_keys()
            employ_month()
        elif pressed_keys == "2":
            print("back to main menu")
            print('')
            clear_keys()
            main_menu()
        else:
            mylcd.lcd_clear()
            mylcd.lcd_display_string('   INVALID  ENTRY', 2)
            print('INVALID ENTRY')
            print('')
            time.sleep(2)
            admin_menu()
    else:
        pressed_keys += key
        
        
    
def employ_month():
    global fun
    fun = fun.replace(fun, 'month')
    mylcd.lcd_clear()
    mylcd.lcd_display_string('  employment Month', 2)
    mylcd.lcd_display_string(' (Two Digit Format)', 3)
    print('employment Month')
    print('(Two Digit Format)')
    

def month_input(key):
    global pressed_keys
    global month
    if key == '#':
        months = {'01': 'JAN', '02': 'FEB', '03': 'MAR', '04': 'APR',
                  '05': 'MAY', '06': 'JUN', '07': 'JUL', '08': 'AUG',
                  '09': 'SEP', '10': 'OCT', '11': 'NOV', '12': 'DEC'
                  }
        if pressed_keys in months:
            month = months[pressed_keys]
            clear_keys()
            employ_year()
        else:
            mylcd.lcd_clear()
            mylcd.lcd_display_string('  INCORRECT FORMAT', 2)
            print("INCORRECT FORMAT")
            print('')
            time.sleep(2)
            clear_keys()
            employ_month()
    else:
        pressed_keys += key


def employ_year():
    global fun
    fun = fun.replace(fun, 'year')
    mylcd.lcd_clear()
    mylcd.lcd_display_string('  employment  Year', 2)
    mylcd.lcd_display_string(' (Four Digit Format)', 3)
    print('employment year')
    print('')


def year_input(key):
    global pressed_keys
    global year
    if key == '#':
        if len(pressed_keys) != 4:
            clear_keys()
            mylcd.lcd_clear()
            mylcd.lcd_display_string('  INCORRECT FORMAT', 2)
            print("INCORRECT FORMAT")
            print('')
            time.sleep(2)
            clear_keys()
            employ_year()
        else:
            year = pressed_keys
            clear_keys()
            finitial()
    else:
        pressed_keys += key


def finitial():
    global fun
    fun = fun.replace(fun, 'finitial')
    mylcd.lcd_clear()
    mylcd.lcd_display_string('   First  Initial', 2)
    print('First Initial')
    print('')


def finitial_input(key):
    global pressed_keys
    global first_initial
    if key == '#':
        letters = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E', '6': 'F',
                   '7': 'G', '8': 'H', '9': 'I', '10': 'J', '11': 'K',
                   '12': 'L', '13': 'M', '14': 'N', '15': 'O', '16': 'P',
                   '17': 'Q', '18': 'R', '19': 'S', '20': 'T', '21': 'U',
                   '22': 'V', '23': 'W', '24': 'X', '25': 'Y', '26': 'Z'
                   }
        if pressed_keys in letters:
            first_initial = letters[pressed_keys]
            clear_keys()
            linitial()
        else:
            clear_keys()
            mylcd.lcd_clear()
            mylcd.lcd_display_string('   INVALID  ENTRY', 2)
            print('INVALID ENTRY')
            print('')
            time.sleep(2)
            finitial()
    else:
        pressed_keys += key


def linitial():
    global fun
    fun = fun.replace(fun, 'linitial')
    mylcd.lcd_clear()
    mylcd.lcd_display_string('   Last Initial', 2)
    print('Last Initial')
    print('')


def linitial_input(key):
    global pressed_keys
    global last_initial
    if key == '#':
        letters = {'1': 'A', '2': 'B', '3': 'C', '4': 'D', '5': 'E', '6': 'F',
                   '7': 'G', '8': 'H', '9': 'I', '10': 'J', '11': 'K',
                   '12': 'L', '13': 'M', '14': 'N', '15': 'O', '16': 'P',
                   '17': 'Q', '18': 'R', '19': 'S', '20': 'T', '21': 'U',
                   '22': 'V', '23': 'W', '24': 'X', '25': 'Y', '26': 'Z'
                   }
        if pressed_keys in letters:
            last_initial = letters[pressed_keys]
            clear_keys()
            emlnum()
        else:
            clear_keys()
            mylcd.lcd_clear()
            mylcd.lcd_display_string('   INVALID  ENTRY', 2)
            print('INVALID ENTRY')
            print('')
            time.sleep(2)
            linitial()
    else:
        pressed_keys += key


def emlnum():
    global fun
    fun = fun.replace(fun, 'emlnum')
    mylcd.lcd_clear()
    mylcd.lcd_display_string('   employee Number', 2)
    mylcd.lcd_display_string('    (Two Digits)', 3)
    print('employee Number')
    print('(Two Digits)')
    print('')


def emlnum_entry(key):
    global pressed_keys
    global employ_number
    if key == '#':
        if len(pressed_keys) != 2:
            clear_keys()
            mylcd.lcd_clear()
            mylcd.lcd_display_string('   INVALID  ENTRY', 2)
            print('INVALID ENTRY')
            print('')
            time.sleep(2)
            emlnum()
        else:
            employ_number = pressed_keys
            clear_keys()
            confirm()
    else:
        pressed_keys += key


def confirm():
    global fun
    global employee
    fun = fun.replace(fun, 'confirm')
    employee = first_initial + last_initial + employ_number + "-" + month + year
    mylcd.lcd_clear()
    mylcd.lcd_display_string('    Confirm  ID:', 1)
    mylcd.lcd_display_string('    ' + employee, 2)
    mylcd.lcd_display_string('1. Confirm', 3)
    mylcd.lcd_display_string('2. Cancel', 4)
    print("ID:", employee)
    print("1 : Confirm")
    print("2 : Cancel")
    print('')


def confirm_entry(key):
    global pressed_keys
    global employee
    global first_initial
    global last_initial
    global employ_number
    global month
    global year
    global fun
    if key == '#':
        if pressed_keys == '1':
            clear_keys()
            enroll()
        elif pressed_keys == '2':
            first_initial = first_initial.replace(first_initial, '')
            last_initial = last_initial.replace(last_initial, '')
            employ_number = employ_number.replace(employ_number, '')
            month = month.replace(month, '')
            year = year.replace(year, '')
            clear_keys()
            main_menu()
        else:
            clear_keys()
            mylcd.lcd_clear()
            mylcd.lcd_display_string('    INVALID  ENTRY', 2)
            print('INVALID ENTRY')
            print('')
            time.sleep(2)
            confirm()
    else:
        pressed_keys += key


# Registration enrollment process begins here
# Checking db to see if ID already taken
def enroll():
    global employee
    global r
    global fun
    print(employee)
    r = employee
    print('employee ID:', r)
    print('')
    conn = sqlite3.connect('/home/pi/Desktop/beta/employee.db')
    c = conn.cursor()
    db_val = c.execute('SELECT employ_num FROM finger_store WHERE employ_num IN (VALUES(?))',
                        [r])
    coun = (len(list(db_val)))
    if coun >= 1:
        mylcd.lcd_clear()
        mylcd.lcd_display_string(' ID Already Exists', 2)
        print('ID Already Exists')
        print('')
        time.sleep(2)
        conn.commit()
        conn.close()
        main_menu()
    else:
        conn.commit()
        conn.close()
        
        try:
            f = PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

            if (f.verifyPassword() == False):
                print('Contact Admin')
                print('')
                time.sleep(2)
                raise ValueError('The given fingerprint sensor password wrong')

        except Exception as e:
            mylcd.lcd_clear()
            mylcd.lcd_display_string('   Contact  Admin', 2)
            print('Contact Admin')
            print('')
            time.sleep(2)
            print('The fingerprint sensor could not be initialized')
            print('Exception message: ' + str(e))
            print('')
            main_menu()

        print('Currently used templates: ' + str(f.getTemplateCount()))
        print('')

        try:
            mylcd.lcd_clear()
            mylcd.lcd_display_string('*Waiting For Finger*', 2)
            print('*Waiting For Finger*')
            print('')

            # Wait for finger to be read

            while (f.readImage() == False):
                pass

            f.convertImage(0x01)

            result = f.searchTemplate()
            positionNumber = result[0]

            if (positionNumber >= 0):
                mylcd.lcd_clear()
                mylcd.lcd_display_string('Fingerprint  Already', 2)
                mylcd.lcd_display_string('       Exists', 3)
                print('Fingerprint Already Exists' + str(positionNumber))
                print('')
                time.sleep(2)
                main_menu()
            else:
                mylcd.lcd_clear()
                mylcd.lcd_display_string('  *Remove  Finger*', 2)
                print('*Remove Finger*')
                print('')
                time.sleep(2)
                mylcd.lcd_clear()
                mylcd.lcd_display_string('*Place Finger Again*', 2)
                print('*Place Finger Again*')
                print('')

                # waiting for second read
                while (f.readImage() == False):
                    pass

                f.convertImage(0X02)

                if (f.compareCharacteristics() == 0):
                    mylcd.lcd_clear()
                    mylcd.lcd_display_string('Fingers Do Not Match', 2)
                    print('Fingers Do Not Match')
                    print('')
                    time.sleep(2)

                f.createTemplate()

                positionNumber = f.storeTemplate()

                f.loadTemplate(positionNumber, 0X01)

                characteristics = str(f.downloadCharacteristics(0x01)).encode(
                    'utf-8')

                cre_hash = hashlib.sha256(characteristics).hexdigest()
                conn = sqlite3.connect('/home/pi/Desktop/beta/employee.db')
                c = conn.cursor()
                c.execute(
                    'INSERT INTO finger_store (employ_num, hashval, id) '
                    'VALUES (?,?,?)', (r, cre_hash, positionNumber))
                conn.commit()
                conn.close()
                mylcd.lcd_clear()
                mylcd.lcd_display_string('    Fingerprint', 2)
                mylcd.lcd_display_string('    Registered', 3)
                print('Fingerprint Registered In Position' + str(positionNumber))
                print('')
                time.sleep(2)
                admin_menu()

        except Exception as e:
            print('Operation failed- Exception message: ' + str(e))
            print('')
            main_menu()


# Keypad stuff

KEYPAD = [
    ["1", "2", "3", "A"],
    ["4", "5", "6", "B"],
    ["7", "8", "9", "C"],
    ["*", "0", "#", "D"]
]

# same as calling: factory.create_4_by_4_keypad, still we put here fyi:
ROW_PINS = [5, 6, 13, 19]  # BCM numbering; Board numbering is: 7,8,10,11 (see pinout.xyz/)
COL_PINS = [12, 16, 20, 21]  # BCM numbering; Board numbering is: 12,13,15,16 (see pinout.xyz/)

factory = rpi_gpio.KeypadFactory()

# Try keypad = factory.create_4_by_3_keypad() or
# Try keypad = factory.create_4_by_4_keypad() #for reasonable defaults
# or define your own:
keypad = factory.create_keypad(keypad=KEYPAD, row_pins=ROW_PINS,
                               col_pins=COL_PINS)


def printkey(key):
    print(key)
    
keypad.registerKeyPressHandler(printkey)


# function to clear string
def clear_keys():
    global pressed_keys
    pressed_keys = pressed_keys.replace(pressed_keys, '')


def store_key(key):
    global pressed_keys
    if key == '#':
        print(pressed_keys)
        if pressed_keys == "1":
            clear_keys()
            finger()
        elif pressed_keys == "2":
            print("send to pwd")
            clear_keys()
            password()
        elif pressed_keys == "3":
            print("send to shutdown")
            clear_keys()
            shutdownmenu()
        else:
            mylcd.lcd_clear()
            mylcd.lcd_display_string('   INVALID  ENTRY', 2)
            print('INVALID ENTRY')
            print('')
            time.sleep(2)
            main_menu()
    else:
        pressed_keys += key
        
        
def shutdownmenu():
    global fun
    clear_keys()
    mylcd.lcd_clear()
    fun = fun.replace(fun, 'shutdownmenu')
    mylcd.lcd_display_string('**Confirm Shutdown**', 1)
    mylcd.lcd_display_string('1. Confirm', 2)
    mylcd.lcd_display_string('2. Cancel' , 3)
    print('**Confirm Shutdown**')
    print('1. Confirm')
    print('2. Cancel')
    print('')
    
    
def confirm_shutdown(key):
    global pressed_keys
    if key == '#':
        print(pressed_keys)
        if pressed_keys == "1":
            print('Send to shutdown')
            print('')
            shutdown()
        elif pressed_keys == "2":
            mylcd.lcd_clear()
            mylcd.lcd_display_string(' Process  Cancelled', 2)
            print('Process Cancelled')
            print('')
            time.sleep(2)
            main_menu()
        else:
            mylcd.lcd_clear()
            mylcd.lcd_display_string('   INVALID  ENTRY', 2)
            print('INVALID ENTRY')
            print('')
            time.sleep(2)
            shutdownmenu()
    else:
        pressed_keys += key
        
        
def shutdown():
    mylcd.lcd_clear()
    mylcd.lcd_display_string('    Shutting down', 1)
    mylcd.lcd_display_string('      [       ]      ', 3)
    time.sleep(.3)
    mylcd.lcd_display_string('      [   *   ]      ', 3)
    time.sleep(.3)
    mylcd.lcd_display_string('      [  ***  ]      ', 3)
    time.sleep(.3)
    mylcd.lcd_display_string('      [ ***** ]      ', 3)
    time.sleep(.3)
    mylcd.lcd_display_string('      [*******]      ', 3)
    time.sleep(.3)
    mylcd.lcd_clear()
    mylcd.lcd_display_string('      Now Safe', 2)
    mylcd.lcd_display_string('    To Shut Down', 3)    
    os.system("sudo shutdown -h now")


# initial options
def boot_sequence():
    mylcd.lcd_clear()
    mylcd.lcd_display_string('       BOOTING', 1)
    mylcd.lcd_display_string('      [       ]      ', 3)
    time.sleep(.1)
    mylcd.lcd_display_string('      [   *   ]      ', 3)
    time.sleep(.1)
    mylcd.lcd_display_string('      [  ***  ]      ', 3)
    time.sleep(.1)
    mylcd.lcd_display_string('      [ ***** ]      ', 3)
    time.sleep(.1)
    mylcd.lcd_display_string('      [*******]      ', 3)
    time.sleep(.1)
    main_menu()


def main_menu():
    global fun
    clear_keys()
    mylcd.lcd_clear()
    mylcd.lcd_display_string('Select, then press #', 1)
    mylcd.lcd_display_string('1. Sign In & Out', 2)
    mylcd.lcd_display_string('2. Admin Menu', 3)
    mylcd.lcd_display_string('3. Shutdown', 4)
    print('1. Sign in & Out')
    print('2. Admin Menu')
    print('3. Shutdown')
    print('')
    fun = fun.replace(fun, 'main_menu')


boot_sequence()


# This function is called each time a keypad button is
def keyHandler(key):
    if fun == 'main_menu':
        store_key(key)
    elif fun == 'password':
        password_input(key)
    elif fun == 'admin_menu':
        admin_input(key)
    elif fun == 'month':
        month_input(key)
    elif fun == 'year':
        year_input(key)
    elif fun == 'finitial':
        finitial_input(key)
    elif fun == 'linitial':
        linitial_input(key)
    elif fun == 'emlnum':
        emlnum_entry(key)
    elif fun == 'confirm':
        confirm_entry(key)
    elif fun == 'shutdownmenu':
        confirm_shutdown(key)


keypad.registerKeyPressHandler(keyHandler)

try:
    while (True):
        time.sleep(0.2)
except:
    keypad.cleanup()
