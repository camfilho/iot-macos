from flask import Flask, render_template, redirect, Response, stream_with_context
from application.Hardware import Hardware
from application.Streaming import Streaming
import json

# Generic Variables
localhost = "127.0.0.1"
kafka_broker_list = [f"{localhost}:29092"]
services = {
    "iotcenter": {"description": "IoT Center", "port": 8001},
    "vnc": {"description": "VNC Server (raspberrypi:1)", "port": 5901},
    "vnc2": {"description": "VNC Server (raspberrypi:2)", "port": 5902},
    "ftp": {"description": "FTP Server", "port": 21},
    "sftp": {"description": "SFTP Server", "port": 22},
    "ssh": {"description": "SSH Server", "port": 22},
    "rasap": {"description": "Raspberry Pi Access Point", "port": 8005},
    "mariadb": {"description": "MariaDB Database", "port": 3306},
    "jupyerlab": {"description": "Jupyter Notebook Lab", "port": 8888},
    "sparkui": {"description": "Spark UI", "port": 4040},
    "sparkmasterui": {"description": "Spark Master UI", "port": 8080},
    "sparkmaster": {"description": "Spark Master", "port": 7077},
    "sparkworker1": {"description": "Spark Worker 1", "port": 8081},
    "sparkworker2": {"description": "Spark Worker 2", "port": 8082},
    "kafkainternal": {"description": "Kafka Broker (Internal)", "port": 9092},
    "kafkaexternal": {"description": "Kafka Broker (External)", "port": 29092},
    "pythonsocket": {"description": "Python Socket Agent", "port": 1500},
}
hosts = {
    "rasp4": {"ip": "", "alive": "", "description": "Raspberry Pi 4"},
    "picow": {"ip": "", "alive": "", "description": "Raspberry Pi Pico W"},
}

app = Flask(__name__)


@app.route("/")
def routing():
    return redirect("/home")


@app.route("/home")
def home():
    return render_template("home.html", services=services, hosts=hosts)

@app.route("/api/docker_info")
def docker_info():
    hardware = Hardware()
    return hardware.get_docker_containers()

@app.route("/api/check_ports")
def check_ports():
    hardware = Hardware()
    return {
        key: hardware.check_port(localhost, value["port"])
        for key, value in services.items()
    }


@app.route("/api/check_host_status")
def host_status():
    hardware = Hardware()

    data = hosts.copy()
    data["rasp4"]["ip"] = hardware.get_local_ip()
    data["picow"]["ip"] = hardware.get_picow_ip(
        topic="iot_source", servers=kafka_broker_list
    )

    for key, value in data.items():
        value["alive"] = hardware.check_if_host_alive(value["ip"])

    return data


@app.route("/api/load_host_hardware")
def host_hardware():
    hardware = Hardware()
    dataset = {
        "cpu_usage": hardware.get_cpu_usage(),
        "mem_usage": hardware.get_mem_usage(),
        "disk_usage": hardware.get_disk_usage(),
    }
    return dataset


@app.route("/api/kafka_info")
def kafka_info():
    hardware = Hardware()
    kafka = hardware.kafka_client(servers=kafka_broker_list)
    dataset = {
        "topics": kafka.list_topics(),
        "consumer_groups": kafka.list_consumer_groups(),
        "describe_topics": kafka.describe_topics(),
        "describe_cluster": kafka.describe_cluster(),
    }
    kafka.close()
    return dataset

@app.route("/hardware")
def hardware():
    hardware = Hardware()
    return render_template(
        "hardware.html",
        network=hardware.get_all_network(),
        hardware=hardware.get_all_hardware(),
        python=hardware.get_all_python(),
    )


@app.route("/streaming")
def streaming():
    return render_template("streaming.html")


@app.route("/picow-stream-data")
def bme_280_temperature() -> Response:
    streaming = Streaming()
    if streaming.kafka_connect("iot_source", kafka_broker_list):
        response = Response(
            stream_with_context(streaming.iterate_kafka_data()),
            mimetype="text/event-stream",
        )
        response.headers["Cache-Control"] = "no-cache"
        response.headers["X-Accel-Buffering"] = "no"
        return response
    else:
        json_data = json.dumps("NoBrokersAvailable")
        response = Response(
            stream_with_context((f"data:{json_data}\n\n")),
            mimetype="text/event-stream",
        )
        return response


if __name__ == "__main__":
    app.run(debug=True, port=8001, host="0.0.0.0")
