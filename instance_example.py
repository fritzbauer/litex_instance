import itertools

from amaranth import Elaboratable, Module, Signal, Cat
from amaranth.build import ResourceError

from litex_soc import LiteXSoC
from pll import IntelCycloneVClockDomainGenerator

__all__ = ["InstanceExample"]


class InstanceExample(Elaboratable):
    def elaborate(self, platform):
        m = Module()

        m.submodules.pll = pll = IntelCycloneVClockDomainGenerator()

        def get_all_resources(name):
            resources = []
            for number in itertools.count():
                try:
                    resources.append(platform.request(name, number))
                except ResourceError:
                    break
            return resources

        leds     = [res.o for res in get_all_resources("led")]
        buttons  = [res.i for res in get_all_resources("button")]

        inverts  = [0 for _ in leds]
        for index, button in zip(itertools.cycle(range(len(inverts))), buttons):
            inverts[index] ^= button

        clk_freq = platform.default_clk_frequency
        timer = Signal(range(int(clk_freq//2)), reset=int(clk_freq//2) - 1)
        flops = Signal(len(leds))

        m.d.comb += Cat(leds).eq(flops ^ Cat(inverts))
        with m.If(timer == 0):
            m.d.sync += timer.eq(timer.reset)
            m.d.sync += flops.eq(~flops)
        with m.Else():
            m.d.sync += timer.eq(timer - 1)

        m.submodules.litex_soc = litex_soc = LiteXSoC()

        return m
