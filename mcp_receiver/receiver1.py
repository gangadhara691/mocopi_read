import socket
import struct
import matplotlib.pyplot as plt
import threading
import queue
from queue import Queue

bone_map = [
    "Hips",  # 0
    "Spine",  # 1
    None,  # 2
    "Chest",  # 3
    None,  # 4
    "UpperChest",  # 5
    None,  # 6
    "-",  # 7
    "-",  # 8
    "Neck",  # 9
    "Head",  # 10
    "RightShoulder",  # 11
    "RightUpperArm",  # 12
    "RightLowerArm",  # 13
    "RightHand",  # 14
    "LeftShoulder",  # 15
    "LeftUpperArm",  # 16
    "LeftLowerArm",  # 17
    "LeftHand",  # 18
    "RightUpperLeg",  # 19
    "RightLowerLeg",  # 20
    "RightFoot",  # 21
    "RightToes",  # 22
    "LeftUpperLeg",  # 23
    "LeftLowerLeg",  # 24
    "LeftFoot",  # 25
    "LeftToes"  # 26
]

# Add the following imports for plot animation
from matplotlib.animation import FuncAnimation

# Uncomment the following line if using Matplotlib with a non-default backend
# import matplotlib
# matplotlib.use('Qt5Agg')


def is_field(name):
    return name.isalpha()


def _deserialize(data, index, length, is_list=False):
    result = [] if is_list else {}
    end_pos = index + length
    while end_pos - index > 8 and is_field(data[index + 4: index + 8]):
        size = struct.unpack("@i", data[index: index + 4])[0]
        index += 4
        field = data[index: index + 4]
        index += 4
        value, index2 = _deserialize(data, index, size, field in [b"btrs", b"bons"])
        index = index2
        if is_list:
            result.append(value)
        else:
            result[field.decode()] = value
    if len(result) == 0:
        body = data[index: index + length]
        return body, index + len(body)
    else:
        return result, index


def _process_packet(message):
    data = _deserialize(message, 0, len(message), False)[0]
    data["head"]["ftyp"] = data["head"]["ftyp"].decode()
    data["head"]["vrsn"] = ord(data["head"]["vrsn"])
    data["sndf"]["ipad"] = struct.unpack("@BBBBBBBB", data["sndf"]["ipad"])
    data["sndf"]["rcvp"] = struct.unpack("@H", data["sndf"]["rcvp"])[0]
    if "skdf" in data:
        for item in data["skdf"]["bons"]:
            item["bnid"] = struct.unpack("@H", item["bnid"])[0]
            item["pbid"] = struct.unpack("@H", item["pbid"])[0]
            item["tran"] = struct.unpack("@fffffff", item["tran"])
    elif "fram" in data:
        data["fram"]["fnum"] = struct.unpack("@I", data["fram"]["fnum"])[0]
        data["fram"]["time"] = struct.unpack("@I", data["fram"]["time"])[0]
        for item in data["fram"]["btrs"]:
            item["bnid"] = struct.unpack("@H", item["bnid"])[0]
            item["tran"] = struct.unpack("@fffffff", item["tran"])
    return data


class Receiver:
    def __init__(self, addr="10.18.80.194", port=12351):
        self.addr = addr
        self.port = port
        self.figure = None
        self.axes = None
        self.lines = []
        self.queue = Queue()
        self.stop_event = threading.Event()

    def plot_human_frame(self, data):
        # Process the human frame data and update the plot
        # Modify this function according to your data structure and plotting requirements
        # Example:
        frame_data = data["fram"]
        fnum = frame_data["fnum"]
        time = frame_data["time"]
        btrs = frame_data["btrs"]

        # Create the plot if it doesn't exist
        if self.figure is None:
            self.figure = plt.figure()
            self.axes = self.figure.add_subplot(111)
            self.lines = []
            for item in btrs:
                line, = self.axes.plot([], [], label=f"Bone {item['bnid']}")
                self.lines.append(line)
            self.axes.legend()

        # Update the plot data
        for i, item in enumerate(btrs):
            bnid = item["bnid"]
            tran = item["tran"]
            line = self.lines[i]
            if not line.get_data():
                line.set_data(range(len(tran)), tran)
            else:
                line.set_ydata(tran)

        # Set appropriate plot limits if needed
        # You can modify this based on your requirements
        self.axes.set_xlim(0, len(tran) - 1)
        self.axes.set_ylim(-1.0, 1.0)  # Modify the y-axis limits if needed

        self.figure.canvas.draw()

    def animate(self, frame_data):
        # Plot the human frame
        self.plot_human_frame(frame_data)

    def receive_data(self):
        while not self.stop_event.is_set():
            try:
                # Receive data from the queue
                data = self.queue.get(timeout=1)

                # Check if the expected keys are present in the data dictionary
                if "fram" in data:
                    self.plot_human_frame(data["fram"])
                else:
                    print("Key 'fram' not found in data:", data)

            except Queue.empty:  # Update to use Queue.Empty
                # Ignore empty queue exceptions and continue
                pass



    def plot_animation(self):
        # Create the plot animation
        ani = FuncAnimation(self.figure, self.animate, interval=200)

        # Show the plot
        plt.show()

    def start(self):
        # Start the data receiving thread
        receive_thread = threading.Thread(target=self.receive_data)
        receive_thread.start()

        # Create the plot animation
        self.figure = plt.figure()
        self.axes = self.figure.add_subplot(111)
        self.lines = []

        def init_animation():
            for item in self.lines:
                item.set_data([], [])
            return self.lines

        def update_animation(frame):
            self.plot_human_frame(frame)
            return self.lines

        def frame_generator():
            while not self.stop_event.is_set():
                yield self.queue.get()

        ani = FuncAnimation(
            self.figure,
            update_animation,
            init_func=init_animation,
            frames=frame_generator,  # Use the frame generator function
            interval=200
        )

        # Show the plot
        plt.show()

        try:
            # Wait for a keyboard interrupt to stop the thread
            while True:
                pass
        except KeyboardInterrupt:
            # Set the stop event to terminate the thread
            self.stop_event.set()

        # Wait for the threads to finish
        receive_thread.join()



# Usage
receiver = Receiver()
receiver.start()
