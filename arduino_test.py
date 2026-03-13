import serial, time
ser = serial.Serial("COM8", 9600, timeout=1)  # use your COM port
time.sleep(2)  # Arduino reset time
ser.write(b"HOUSE:OFF\n")
print(ser.readline().decode().strip())
