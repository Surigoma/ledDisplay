import asyncio
from queue import Queue
from queue import Empty
from queue import Full
import numpy as np
from pyartnet import ArtNetNode, BaseUniverse, Channel  # pyright: ignore[reportPrivateImportUsage]
from threading import Thread

from config import ConfigOutput, ConfigPixel


class Universe:
    id: int
    universe: BaseUniverse
    mappings: list[tuple[int, int, int, int]]
    channelLength: int
    dataMap: Channel


class ArtNet:
    _address: str
    _fps: int
    _thread: Thread | None = None
    _is_running: bool = True
    _send_queue: Queue
    _universes: list[Universe] = []
    _fillEnd: bool = False

    def setup(self, config: ConfigOutput, sampleLen: int):
        self._send_queue = Queue(maxsize=1)
        self._universes = []
        self._fillEnd = False
        self._address = config.address
        self._fps = int(config.fps)
        chanPerUniv = 512
        if config.mapping is not None:
            if not config.mapping.strict:
                chanPerUniv = 510
            if config.mapping.fillEnd:
                self._fillEnd = True
        has_explicit_mapping = any(
            sample.universe is not None for sample in config.sampler
        )
        if has_explicit_mapping and any(
            sample.universe is None for sample in config.sampler
        ):
            raise ValueError(
                "universe and channel must be set for every sampler when using explicit mapping"
            )

        universes: dict[int, Universe] = {}
        source_start = 0
        legacy_destination = 0
        for sample in config.sampler:
            sample_count = 1 if isinstance(sample, ConfigPixel) else sample.count
            remaining = sample_count * 3
            if has_explicit_mapping:
                assert sample.universe is not None and sample.channel is not None
                destination = sample.universe * chanPerUniv + sample.channel - 1
            else:
                destination = legacy_destination

            while remaining > 0:
                universe_id = destination // chanPerUniv
                destination_start = destination % chanPerUniv
                length = min(remaining, chanPerUniv - destination_start)
                source_end = source_start + length
                destination_end = destination_start + length

                if universe_id not in universes:
                    univ = Universe()
                    univ.id = universe_id
                    univ.mappings = []
                    univ.channelLength = 0
                    universes[universe_id] = univ
                univ = universes[universe_id]
                if any(
                    destination_start < existing_end
                    and destination_end > existing_start
                    for _, _, existing_start, existing_end in univ.mappings
                ):
                    raise ValueError(
                        f"sampler output overlaps universe {universe_id} "
                        f"channels {destination_start + 1}-{destination_end}"
                    )
                univ.mappings.append(
                    (source_start, source_end, destination_start, destination_end)
                )
                univ.channelLength = max(univ.channelLength, destination_end)
                source_start = source_end
                destination += length
                remaining -= length

            legacy_destination = destination

        if source_start != sampleLen * 3:
            raise ValueError("sampler length and Art-Net mapping length do not match")
        self._universes = [universes[key] for key in sorted(universes)]
        print([(univ.id, univ.mappings) for univ in self._universes])

    def queue(self, samples: list[tuple[int, int, int]]):
        data = np.array(samples).flatten().tolist()
        while True:
            try:
                self._send_queue.put_nowait(data)
                return
            except Full:
                try:
                    self._send_queue.get_nowait()
                except Empty:
                    pass

    def start(self):
        self._thread = Thread(target=self.process, name="artnet", daemon=True)
        self._thread.start()

    def stop(self):
        self._is_running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)

    async def _async_process(self):
        print("start artnet")
        async with ArtNetNode.create(
            self._address, 6454, name="test", max_fps=self._fps, refresh_every=1
        ) as artnet:
            artnet.set_synchronous_mode(True)
            for univ in self._universes:
                univ.universe = artnet.add_universe(univ.id)
                channel_length = 512 if self._fillEnd else univ.channelLength
                univ.dataMap = univ.universe.add_channel(
                    1, channel_length, f"led{univ.id}"
                )
            while self._is_running:
                try:
                    data: list[int] = await asyncio.to_thread(
                        self._send_queue.get, True, 0.5
                    )
                    for univ in self._universes:
                        channel_length = 512 if self._fillEnd else univ.channelLength
                        split = [0] * channel_length
                        for (
                            source_start,
                            source_end,
                            destination_start,
                            destination_end,
                        ) in univ.mappings:
                            split[destination_start:destination_end] = data[
                                source_start:source_end
                            ]
                        univ.dataMap.set_values(split)
                except Empty:
                    # print("timeout")
                    pass
                except Exception as e:
                    print(e)
                    break
            await artnet.stop_refresh()
        print("stop artnet")

    def process(self):
        asyncio.run(self._async_process())
