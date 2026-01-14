import asyncio
from multiprocessing import Queue
from queue import Empty
import numpy as np
from pyartnet import ArtNetNode, BaseUniverse, Channel # pyright: ignore[reportPrivateImportUsage]
from threading import Thread

from config import ConfigOutput

class Universe:
    universe: BaseUniverse
    mapping: tuple[int, int]
    dataMap: Channel

class ArtNet:
    _address: str
    _fps: int
    _thread: Thread | None = None
    _is_running: bool = True
    _send_queue: Queue
    _universes: list[Universe] = []

    def setup(self, config: ConfigOutput, sampleLen: int):
        self._send_queue = Queue()
        self._address = config.address
        self._fps = int(config.fps)
        chanPerUniv = 512
        if config.mapping is not None and not config.mapping.strict:
            chanPerUniv = 510
        full = sampleLen * 3
        for i in range(0, full, chanPerUniv):
            univ = Universe()
            univ.mapping = (i, i + min(chanPerUniv, full - i))
            self._universes.append(univ)
        print([k.mapping for k in self._universes])

    def queue(self, samples: list[tuple[int, int, int]]):
        self._send_queue.put(np.array(samples).flatten().tolist())

    def start(self):
        self._thread = Thread(target=self.process)
        self._thread.start()

    def stop(self):
        self._is_running = False
        if self._thread is not None:
            self._thread.join()

    async def _async_process(self):
        print("start artnet")
        async with ArtNetNode.create(self._address, 6454, name="test", max_fps=self._fps, refresh_every=1) as artnet:
            artnet.set_synchronous_mode(False)
            for i, univ in enumerate(self._universes):
                univ.universe = artnet.add_universe(i)
                length = univ.mapping[1] - univ.mapping[0]
                univ.dataMap = univ.universe.add_channel(1, length, "led")
                univ.universe.send_data()
            while self._is_running:
                try:
                    data: list[int] = self._send_queue.get(True, timeout=0.5)
                    for univ in self._universes:
                        # print(univ.mapping, data[univ.mapping[0]:univ.mapping[1]])
                        univ.dataMap.set_values(data[univ.mapping[0]:univ.mapping[1]])
                        univ.universe.send_data()
                except Empty:
                    print("timeout")
                except Exception as e:
                    print(e)
                    break
        print("stop artnet")

    def process(self):
        asyncio.run(self._async_process())