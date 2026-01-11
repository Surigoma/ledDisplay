import json
import sys
import time
from config import Config, ConfigBody
from ndi import NDI
import numpy as np


def callback(data: np.ndarray, resolution: tuple):
    print(data.shape, resolution)
    pass


def setupNDI(config: ConfigBody):
    ndi: NDI = NDI()
    if config["input"]["ndi"] is None or config["input"]["ndi"]["source"] == "":
        sources = ndi.getNDISources()
        for i, source in enumerate(sources):
            print(f"{i}: {source}")
        select = int(input("Choice : "))
        config["input"]["ndi"]["source"] = f"{sources[select]}"
    print(json.dumps(config))
    if not ndi.setSource(config["input"]["ndi"]["source"]):
        raise Exception("Failed to connect source.")
    ndi.start(callback)


def main():
    config: ConfigBody = Config().get()
    if config["input"]["source"] == "ndi":
        setupNDI(config)
    else:
        sys.exit(0)
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
    print("STOP")
