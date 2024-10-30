from classes.RPi_Pico_Wattmeter_serial import RPi_Pico_serial
from classes.RPi_ssh_agent import RaspberryPiSSH

from multiprocessing import Process


def take_measurements(experiment_name):
    recorder = RPi_Pico_serial()
    seconds = 90000000
    num_samples = seconds * 200
    save_path = "./data/new_data/"

    if recorder.connect_to_port():
        recorder.open_file(save_path, experiment_name)
        recorder.record_data(num_samples)
        recorder.close()
    else:
        print("Could not find RPi Pico")


def make_ssh_command(
    sensor_number="1",
    test_time="1",
    file_name="perf_fiware",
    platform_url="localhost",
    strategy="green",
    freshness_frequency="1",
    notification_url="1",
):
    exec_path = "cd 2023-iotvar-hardware/Code/Phase_1/iothandler/application"

    mvn_call = (
        "mvn exec:java -Dexec.mainClass=iotvarPerformance.fiware.IotvarFiwareExample "
        + '-Dexec.args="'
        + f"{sensor_number} {test_time} {file_name} {platform_url} {strategy} "
        + f'{freshness_frequency} {notification_url}"'
    )
    command = f"{exec_path} && {mvn_call}"
    return command


def get_startTimestamp(exec_finish_message):
    timestampIndex = exec_finish_message.find("StartTime:")
    Timestamp = exec_finish_message[timestampIndex + 11 : timestampIndex + 11 + 13]
    return Timestamp


if __name__ == "__main__":
    experiment_name = "dynamic_refresh_time_60seconds"
    freshness = "60"
    testTime = "300"

    power_measure = Process(target=take_measurements, args=(experiment_name,))
    # ssh
    ssh_client = RaspberryPiSSH()
    # ssh_client_iotvar_sender = RaspberryPiSSH()

    ssh_client.connect()

    log_file = open(
        "./data/new_data/" + experiment_name + "_experiment_metadata.csv", "w"
    )
    log_file.write("%s" % "sensorNumber,testTime,freshness,startTimestamp\n")
    power_measure.start()
    cpuLogname = experiment_name + "_CPU_usage.csv"
    cpuLogpath = (
        "/home/han4n/2023-iotvar-hardware/Code/Phase_3/IoTVar_PowerProfiler/extras/"
    )
    ssh_client.triggerCPUmeasurements(cpuLogname, cpuLogpath)

    for i in [25, 50, 75, 100, 125, 150, 175, 200]:
        for j in range(25):
            print("number of sensors: " + str(i) + " experiment: " + str(j + 1))
            command = make_ssh_command(
                sensor_number=str(i), test_time=testTime, freshness_frequency=freshness
            )
            # ssh_client_iotvar_sender.connect()
            ssh_client.execute_command(command)
            startTimestamp = get_startTimestamp(ssh_client.exec_finish_message)
            log_file.write(
                "%s" % str(i)
                + ","
                + testTime
                + ","
                + freshness
                + ","
                + startTimestamp
                + "\n"
            )
            # ssh_client_iotvar_sender.close()
    power_measure.terminate()
    log_file.close()
    ssh_client.finishCPUmeasurements()
    print("Finished experiments")
    print("Transfering CPU log file")

    scp = ssh_client.get_scp_agent()
    destination = "/home/han4n/2023-iotvar-hardware/Code/Phase_3/IoTVar_PowerProfiler/data/new_data"

    scp.get(cpuLogpath + cpuLogname, destination)

    ssh_client.close()
    print("Transfer complete")
