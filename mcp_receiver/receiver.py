import socket
import struct
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
        self.queue = Queue()
        self.stop_event = threading.Event()

    def receive_data(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.bind((self.addr, self.port))
            while not self.stop_event.is_set():
                try:
                    data, _ = sock.recvfrom(4096)
                    self.queue.put(data)
                    processed_data = _process_packet(data)
                    # Check if the expected keys are present in the data dictionary
                    if "fram" in processed_data:
                        # Process the received data
                        

                        # Print bone translations for specific bone IDs
                        bone_ids_to_print = [10, 14, 18, 19, 23, 0]  # Bone IDs to print: Head, RightHand, LeftHand, RightLeg, LeftLeg, Hips
                        btrs = processed_data["fram"]["btrs"]
                        for btr in btrs:
                            bnid = btr['bnid']
                            if bnid not in bone_ids_to_print:
                                continue
                            tran = btr['tran']
                            tran_rounded = tuple(round(num, 5) for num in tran)
                            head = bone_map[bnid] if bnid < len(bone_map) else "Unknown"
                            print(f" {head}, Translation: [x: {tran_rounded[0]}, y: {tran_rounded[1]}, z: {tran_rounded[2]}] ; [rx: {tran_rounded[3]}, ry: {tran_rounded[4]}, rz: {tran_rounded[5]}]")
                            print("----------------------------------------------")
                    else:
                        print("Key 'fram' not found in data:", data)
                except socket.error as e:
                    print("Socket error:", str(e))

    def start(self):
        # Start the data receiving thread
        receive_thread = threading.Thread(target=self.receive_data)
        receive_thread.start()

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
