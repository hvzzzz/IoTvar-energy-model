import paramiko
import os
import time
from scp import SCPClient


class RaspberryPiSSH:
    def __init__(
        self,
        host="raspberrypi.local",
        username=os.environ["RPI_user"],
        password=os.environ["RPI_pass"],
    ):
        self.host = host
        self.username = username
        self.password = password
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.exec_finish_message = ""
        self.connection_established = False

    def connect(self):
        print("Establishing connection with Raspberry Pi 4B...")
        while not self.connection_established:
            self.client.connect(
                hostname=self.host,
                username=self.username,
                password=self.password,
                allow_agent=False,
                look_for_keys=False,
            )
            self.connection_established = True

        self.connection_established = False
        print("Connected to Raspberry Pi 4B!")

    def execute_command(self, command):
        try:
            stdin, stdout, stderr = self.client.exec_command(command)
            self.exec_finish_message = stdout.read().decode()
            # give time to process the command, bug report https://github.com/paramiko/paramiko/issues/1617
            time.sleep(5)

        except Exception as e:
            print(f"Error executing command: {e}")

    def triggerCPUmeasurements(self, cpuLogname, cpuLogpath):
        samp_period = "250000"  # sampling period for CPU measurements [usec]
        # samp_period = "500000"  # sampling period for CPU measurements [usec]
        # samp_period = "1000000"  # sampling period for CPU measurements [usec]
        command = (
            "cd " + cpuLogpath + " && ./cpu_monitor " + samp_period + " " + cpuLogname
        )
        _, _, _ = self.client.exec_command(command)

    def finishCPUmeasurements(self):
        _, stdout, _ = self.client.exec_command("pidof ./cpu_monitor")
        pid = stdout.read().decode()
        kill_command = "kill -2 " + pid
        _, stdout, _ = self.client.exec_command(kill_command)
        print("Finished CPU usage measurements")

    def get_scp_agent(self):
        scp = SCPClient(self.client.get_transport())
        return scp

    def close(self):
        self.client.close()
