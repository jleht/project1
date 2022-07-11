import serial
import time
from classes.check_serial import SerialConnection
from classes.teensy import Teensy
import coloredlogs
import logging

fmt = '[ %(asctime)s :: %(levelname)s ] %(message)s'
coloredlogs.install(fmt=fmt, level=logging.DEBUG)
# logging.basicConfig(level=logging.DEBUG, format=fmt, encoding='utf-8')

sc = SerialConnection()

teensy_port = sc.find_machine(0x1209, 0xAD10)
if teensy_port:
    t = Teensy(teensy_port)

    t.move_axis('z100')
    t.move_axis('x-100')

# print(teensy_port)
# teensy = serial.Serial(teensy_port)

# teensy.baudrate = 9600
# teensy.write_timeout = None
# teensy.timeout = None
# output = []
# def sendCmd(cmd):
#         try:
#             cmd = cmd.strip()+'\r'
#             cmd = cmd.encode()

#             teensy.write(cmd)
#             time.sleep(0.1)

#             data = []
#             data.append(teensy.read_until(serial.CR))
#             # while teensy.in_waiting>0:
#             #     print(teensy.in_waiting)
#             #     raw = teensy.read_until(serial.CR)
#             #     data.append(raw)
#             #     time.sleep(0.1)
#             return data
#         except serial.SerialException as e:
#             print(e)

# def printOutput(output):
#     if not isinstance(output, int):
#             for msg in output:
#                 print(msg.decode('utf-8', "ignore"))

# _ = sendCmd("zh1")
# _ = sendCmd('zm1000')

# _ = sendCmd('xh1')
# _ = sendCmd('xp38433')

output = t.warmup()
print(output)
