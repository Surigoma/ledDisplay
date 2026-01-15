import sys
import time
from typing import Optional
from config import Config, ConfigBody, ConfigNDI
from ffmpeg import FFmpeg
from frameProcess import FrameProcessor
from imageSampler import ImageSampler
from input import ImageArgs, ImageCallback
from ndi import NDI
from output import ArtNet

config: ConfigBody = Config().get()
processor: FrameProcessor = FrameProcessor()
imageSampler: ImageSampler = ImageSampler()
ndi: Optional[NDI] = None
ffmpeg: Optional[FFmpeg] = None
is_running: bool = True
artnet: ArtNet = ArtNet()


def callback(image: ImageArgs):
    global imageSampler, artnet
    samples = imageSampler.sample(image)
    artnet.queue(samples)


def setupNDI(config: ConfigBody, callback: ImageCallback):
    global ndi
    ndi = NDI()
    if config.input.ndi is None or config.input.ndi.source == "":
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
        config.input.ndi = ConfigNDI(source="")
        config.input.ndi.source = f"{target}"
    if not ndi.setSource(config.input.ndi.source):
        raise Exception("Failed to connect source.")
    ndi.start(callback)


def setupFFmpeg(config: ConfigBody, callback: ImageCallback):
    global ffmpeg
    ffmpeg = FFmpeg()
    if config.input.ffmpeg is None or config.input.ffmpeg.source == "":
        raise Exception("Failed to find FFmpeg source")
    if not ffmpeg.open(config.input.ffmpeg.source, 0, config.input.ffmpeg.loop):
        raise Exception("Failed to connect source.")
    ffmpeg.start(callback)


def main():
    global ndi, ffmpeg, is_running, imageSampler, artnet
    try:
        processor.setup(config.output)
        imageSampler.setup(config.output)
        artnet.setup(config.output, imageSampler.sampleLen())
        artnet.start()
        processor.start(callback, config.output.fps)
        if config.input.source == "ndi":
            setupNDI(config, processor.update)
        elif config.input.source == "ffmpeg":
            setupFFmpeg(config, processor.update)
        else:
            return
        print(config.model_dump_json())
        while is_running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("key interrupt")
        if ndi is not None:
            ndi.stop()
        if ffmpeg is not None:
            ffmpeg.stop()
        is_running = False
    return


if __name__ == "__main__":
    main()
    processor.stop()
    artnet.stop()
    print("STOP")
    # for t in threading.enumerate():
    #     print("thread", t.name, t.is_alive)
    # for k, f in sys._current_frames().items():
    #     traceback.print_stack()
    sys.exit(0)
