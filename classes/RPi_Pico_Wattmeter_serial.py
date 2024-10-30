from serial.tools import list_ports
import serial
import time
import csv
from datetime import datetime, timedelta


class RPi_Pico_serial:
    def __init__(self, baud_rate=115200):
        self.baud_rate = baud_rate
        self.serial_port = None
        self.file = None

    def connect_to_port(self):
        pico_ports = list(list_ports.grep("2E8A"))
        if not pico_ports:
            print("No Raspberry Pi Pico found")
            return False
        else:
            pico_serial_port = pico_ports[0].device
            print("Raspberry Pi Pico found at {}".format(pico_serial_port))
            self.serial_port = serial.Serial(pico_serial_port, self.baud_rate)
            return True

    def open_file(self, path, experiment_name):
        current_timestamp = time.time()
        current_datetime_utc = datetime.utcfromtimestamp(current_timestamp)
        current_datetime_local = current_datetime_utc - timedelta(hours=5)
        name = current_datetime_local.strftime("%Y-%m-%d_%H-%M-%S")
        filename = path + name + "_" + experiment_name + ".csv"
        self.file = open(filename, "w", newline="")
        self.file.truncate()

    def record_data(self, num_samples):
        if not self.serial_port or not self.file:
            print("Serial port or file not opened.")
            return
        writer = csv.writer(self.file, delimiter=",")
        writer.writerow(
            ["unixTimestamp", "ucTimestamp", "current_ma", "voltage_v", "power_mw"]
        )
        for _ in range(num_samples):
            try:
                s_bytes = self.serial_port.readline()
                pc_timestamp = time.time()
                decoded_bytes = s_bytes.decode("utf-8").strip("\r\n")
                values = [float(x) for x in decoded_bytes.split(",")]
                values.insert(0, pc_timestamp)

                writer = csv.writer(self.file, delimiter=",")
                writer.writerow(values)
            except Exception as e:
                print(f"Error encountered serial: {e}")

    def close(self):
        if self.file:
            self.file.close()
