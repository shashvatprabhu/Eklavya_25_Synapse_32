import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
from cocotb.result import TestFailure
import random

CACHESIZE = 1024
BLOCKSIZE = 4
ASSOCIATIVITY = 2

def mem_read(addr):
    return (0xAA << 24) | (addr & 0xFFFFFF)

@cocotb.test()
async def test_icache_behavior(dut):
  
    clock = Clock(dut.clk, 10, units="ns") 
    cocotb.start_soon(clock.start())

    dut.reset.value = 1
    dut.iready.value = 0
    dut.ifetch.value = 0
    dut.instraddress.value = 0

    await Timer(20, units="ns")
    dut.reset.value = 0
    await RisingEdge(dut.clk)

    testaddresses = [
        0x00000010,  # Compulsory miss
        0xAA000010,  # Compulsory miss, same set, different tag
        0x00000010,  # Hit
        0xAA000010,  # Hit
        0xBB000010,  # Miss (eviction)
        0xBB000010,  # Hit
        0x00000010,  # Miss (evicted earlier)
    ]

    hitcount = 0
    misscount = 0
    accesses = 0

    for i, addr in enumerate(testaddresses):
        dut.instraddress.value = addr
        accesses += 1
        dut._log.info(f"---------------------------------------------------")
        dut._log.info(f"Access {accesses}: Address = 0x{addr:08X}")

        await RisingEdge(dut.clk)
        await RisingEdge(dut.clk)

        if dut.hit.value:
            hitcount += 1
            dut._log.info(f"Hit! Instruction = 0x{int(dut.instruction.value):08X}")
        else:
            misscount += 1
            fetchaddr = int(dut.fetchaddr.value)
            dut._log.info(f"Miss. Fetching from memory @ 0x{fetchaddr:08X}")

            await RisingEdge(dut.clk) 
            dut.ifetch.value = mem_read(fetchaddr)
            dut.iready.value = 1

            await RisingEdge(dut.clk)
            dut.iready.value = 0

            await RisingEdge(dut.clk)
            dut._log.info(f"Memory returned: 0x{int(dut.ifetch.value):08X}")

    dut._log.info(f"Total Accesses : {accesses}")
    dut._log.info(f"Total Hits : {hitcount}")
    dut._log.info(f"Total Misses : {misscount}")
    hit_rate = (hitcount * 100.0) / accesses
    miss_rate = (misscount * 100.0) / accesses
    dut._log.info(f"Hit Rate : {hit_rate:.2f}%")
    dut._log.info(f"Miss Rate : {miss_rate:.2f}%")
