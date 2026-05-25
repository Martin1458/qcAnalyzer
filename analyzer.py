import time
import json

class Analyzer:
    def __init__(self):
        # Hats history: hats_history = [[time.time(), hats], ...]
        self.hats_history = [[0, (0, 0)], [0, (0, 0)]]
        self.UP = (0, 1)
        self.DOWN = (0, -1)
        self.LEFT = (-1, 0)
        self.RIGHT = (1, 0)
        self.recorded = []
        self.DIR_NAMES = {0: "down", 1: "up", 2: "right", 3: "left"}

        with open("image_filled.json") as f:
            self.image_filled = json.load(f)
        with open("qc_options.json") as f:
            self.qc_options = json.load(f)

    def add(self, hats):
        self.hats_history.append([time.time(), hats[0]])
        if self.get_delay(self.hats_history[-2], self.hats_history[-1]) < 1.8:
            print("Delay:", self.get_delay(self.hats_history[-2], self.hats_history[-1]))
            print("Hats:", hats)
            self.analyze(self.hats_history[-2][1], self.hats_history[-1][1])
            self.hats_history = [[0, (0, 0)], [0, (0, 0)]]


    def get_delay(self, hats_a, hats_b):
        return hats_b[0] - hats_a[0]
    
    def analyze(self, hats_a, hats_b):
        # Hats_a/b = (x, y)
        # 0 = Down, 1 = Up, 2 = Right, 3 = Left
        a = self.get_dir(hats_a)
        b = self.get_dir(hats_b)

        a_name = self.DIR_NAMES.get(a)
        b_name = self.DIR_NAMES.get(b)
        if a_name and b_name:
            qc_id = self.image_filled.get(a_name, {}).get(b_name)
            message = self.qc_options.get(qc_id, "Unknown")
            print(f"Quick chat: {message}")
            self.record((a_name, b_name))

    def get_dir(self, hat):
        # 0 = Down, 1 = Up, 2 = Right, 3 = Left
        if hat == self.DOWN:
            return 0
        elif hat == self.UP:
            return 1
        elif hat == self.RIGHT:
            return 2
        elif hat == self.LEFT:
            return 3
        else:
            return -1
        
    def record(self, chat):
        self.recorded.append(chat)

    def save_recorded(self, filename):
        with open(filename, "a") as f:
            for chat in self.recorded:
                f.write(f"{chat[0]},{chat[1]}\n")
        print("Recorded data saved to:", filename)
        print("Recorded data:", self.recorded)
        self.recorded = []

    def decode_recorded(self, filename):
        with open(filename) as f:
            lines = f.read().splitlines()
        for line in lines:
            if not line.strip():
                continue
            a_name, b_name = line.split(",")
            qc_id = self.image_filled.get(a_name, {}).get(b_name)
            message = self.qc_options.get(qc_id, "Unknown")
            print(f"{line} -> {message}")

