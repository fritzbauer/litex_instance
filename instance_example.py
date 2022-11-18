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

        leds     = [res.o for res in get_all_resources(platform, "led")]
        buttons  = [res.i for res in get_all_resources(platform, "button")]
        self.blinkLED(m, platform, leds, buttons)

        # get the litex SoC
        m.submodules.litex_soc = litex_soc = LiteXSoC()
        m.d.comb += leds[0].eq(litex_soc.led)

        return m


    def blinkLED(self, m, platform, leds, buttons):        

        inverts  = [0 for _ in leds]
        for index, button in zip(itertools.cycle(range(len(inverts))), buttons):
            inverts[index] ^= button

        clk_freq = platform.default_clk_frequency
        timer = Signal(range(int(clk_freq//2)), reset=int(clk_freq//2) - 1)
        flops = Signal(len(leds))

        m.d.comb += Cat(leds[1]).eq(flops ^ Cat(inverts))
        with m.If(timer == 0):
            m.d.sync += timer.eq(timer.reset)
            m.d.sync += flops.eq(~flops)
        with m.Else():
            m.d.sync += timer.eq(timer - 1)

        return


def get_all_resources(platform, name):
            resources = []
            for number in itertools.count():
                try:
                    resources.append(platform.request(name, number))
                except ResourceError:
                    break
            return resources