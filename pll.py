from amaranth         import *
from amaranth.build   import *
from amaranth.lib.cdc import ResetSynchronizer


class ClockDomainGeneratorBase():
    NO_PHASE_SHIFT  = 0

    def wire_up_reset(self, m, reset):
        m.submodules.reset_sync_sync = ResetSynchronizer(reset, domain="sync")
        m.submodules.reset_sync_soc = ResetSynchronizer(reset, domain="soc")  
        m.submodules.reset_sync_sdram = ResetSynchronizer(reset, domain="sdram")  

class IntelCycloneVClockDomainGenerator(Elaboratable, ClockDomainGeneratorBase):

    def __init__(self, *, clock_frequencies=None, clock_signal_name=None):
        pass

    def elaborate(self, platform):
        m = Module()

        # Create our domains
        # usb: USB clock: 60MHz
        # adat: ADAT clock = 12.288 MHz = 48 kHz * 256
        # dac: I2S DAC clock 48k = 3.072 MHz = 48 kHz * 32 bit * 2 channels
        # sync: ADAT transmit domain clock = 61.44 MHz = 48 kHz * 256 * 5 output terminals
        # fast: ADAT sampling clock = 98.304 MHz = 48 kHz * 256 * 8 times oversampling
        m.domains.sync = ClockDomain("sync")
        m.domains.soc = ClockDomain("soc")
        m.domains.sdram = ClockDomain("sdram")


        clk = platform.request(platform.default_clk)

        main_clock    = Signal()
        sdram_clocks  = Signal(6)

        sys_locked    = Signal()
        sdram_locked  = Signal()

        reset         = Signal()

        m.submodules.mainpll = Instance("altera_pll",
            p_pll_type="General",
            p_pll_subtype="General",
            p_fractional_vco_multiplier="false",
            p_operation_mode="normal",
            p_reference_clock_frequency="50.0 MHz",
            p_number_of_clocks="1",

            p_output_clock_frequency0="60.000000 MHz",


            # Drive our clock from the internal 50MHz clock
            i_refclk = clk,
            o_outclk = main_clock,
            o_locked = sys_locked
        )

        m.submodules.audiopll = Instance("altera_pll",
            p_pll_type="General",
            p_pll_subtype="General",
            p_fractional_vco_multiplier="true",
            p_operation_mode="normal",
            p_reference_clock_frequency="60.0 MHz",
            p_number_of_clocks="2",

            p_output_clock_frequency0="109.226666 MHz",
            p_output_clock_frequency1="109.226666 MHz",
            p_phase_shift1="253 ps",

            # Drive our clock from the mainpll
            i_refclk=main_clock,
            o_outclk=sdram_clocks,
            o_locked=sdram_locked
        )

        m.d.comb += [
            reset.eq(~(sys_locked & sdram_locked)),
            ClockSignal("sync").eq(main_clock),
            ClockSignal("soc").eq(sdram_clocks[0]),
            ClockSignal("sdram").eq(sdram_clocks[1]),
        ]

        self.wire_up_reset(m, reset)

        return m