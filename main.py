import json
import time
from config import Config
from ndi import NDI
import numpy as np


def callback(data: np.ndarray, resolution: tuple):
    print(data.shape, resolution)
    pass

def main():
    config: Config = Config()
    ndi: NDI = NDI()
    if config.config["source"] == "":
        sources = ndi.getNDISources()
        for i, source in enumerate(sources):
            print(f"{i}: {source}")
        select = int(input("Choice : "))
        config.config["source"] = f"{sources[select]}"
    print(json.dumps(config.config))
    if not ndi.setSource(config.config["source"]):
        raise Exception("Failed to connect source.")
    ndi.start(callback)

if __name__ == "__main__":
    main()
    print("STOP")