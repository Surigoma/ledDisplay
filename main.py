import json
import sys
import time
from config import Config
from ndi import NDI
import numpy as np


def callback(data: np.ndarray, resolution: tuple):
    print(data.shape, resolution)
    pass


def setupNDI(config: Config):
    ndi: NDI = NDI()
    if config.config["ndi"] is None or config.config["ndi"]["source"] == "":
        sources = ndi.getNDISources()
        for i, source in enumerate(sources):
            print(f"{i}: {source}")
        select = int(input("Choice : "))
        config.config["ndi"]["source"] = f"{sources[select]}"
    print(json.dumps(config.config))
    if not ndi.setSource(config.config["ndi"]["source"]):
        raise Exception("Failed to connect source.")
    ndi.start(callback)


def main():
    config: Config = Config()
    if config.config["source"] == "ndi":
        setupNDI(config)
    else:
        sys.exit(0)
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
    print("STOP")
