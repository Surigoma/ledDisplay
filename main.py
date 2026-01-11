import json
import sys
import time
from typing import Optional
from config import Config, ConfigBody
from ffmpeg import FFmpeg
from frameProcess import FrameProcessor
from input import ImageArgs, ImageCallback
from ndi import NDI

def callback(image: ImageArgs):
    print(image.image.shape if image.image is not None else None, image.shape)
    # if image.image is not None:
    #     Image.fromarray(image.image).save("./tmp.bmp")


config: ConfigBody = Config().get()
processor: FrameProcessor = FrameProcessor()
ndi: Optional[NDI] = None
ffmpeg: Optional[FFmpeg] = None
is_running: bool = True


def setupNDI(config: ConfigBody, callback: ImageCallback):
    global ndi
    ndi = NDI()
    if config["input"]["ndi"] is None or config["input"]["ndi"]["source"] == "":
        sources = ndi.getNDISources()
        target = ""
        if len(sources) > 1:
            for i, source in enumerate(sources):
                print(f"{i}: {source}")
            select = int(input("Choice : "))
            target = sources[select]
        elif len(sources) == 1:
            target = sources[0]
        else:
            raise Exception("Failed to find NDI source")
        config["input"]["ndi"] = {"source": ""}
        config["input"]["ndi"]["source"] = f"{target}"
    if not ndi.setSource(config["input"]["ndi"]["source"]):
        raise Exception("Failed to connect source.")
    ndi.start(callback)


def setupFFmpeg(config: ConfigBody, callback: ImageCallback):
    global ffmpeg
    ffmpeg = FFmpeg()
    if config["input"]["ffmpeg"] is None or config["input"]["ffmpeg"]["source"] == "":
        raise Exception("Failed to find FFmpeg source")
    if "loop" not in config["input"]["ffmpeg"]:
        config["input"]["ffmpeg"]["loop"] = True
    if not ffmpeg.open(
        config["input"]["ffmpeg"]["source"], 0, config["input"]["ffmpeg"]["loop"]
    ):
        raise Exception("Failed to connect source.")
    ffmpeg.start(callback)

def main():
    global ndi, ffmpeg, is_running
    try:
        processor.start(callback, 1)
        if config["input"]["source"] == "ndi":
            setupNDI(config, processor.process)
        elif config["input"]["source"] == "ffmpeg":
            setupFFmpeg(config, processor.process)
        else:
            sys.exit(0)
        print(json.dumps(config))
        while is_running:
            time.sleep(1)
    except KeyboardInterrupt:
        print("key interrupt")
        if ndi is not None:
            ndi.stop()
        if ffmpeg is not None:
            ffmpeg.stop()
        processor.stop()


if __name__ == "__main__":
    main()
    print("STOP")
