import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_cache_storage_basic_operations(dut):
    """
    Cocotb testbench for 1-word block direct-mapped cache_storage module.
    Tests:
      1. Cold read miss
      2. Write and read (expect hit)
      3. Read with wrong tag (miss)
      4. Overwrite and confirm new value
      5. Evict by writing to same index, different tag
      6. Write/read across different indexes
      7. Reset clears everything
    """

    clock = Clock(dut.clk, 10, units="ns")  # 100 MHz
    cocotb.start_soon(clock.start())

    # Helper function
    INDEX_BITS = 4
    OFFSET_BITS = 0  # BLOCK_SIZE = 1
    def make_address(tag, index):
        return (tag << (INDEX_BITS + OFFSET_BITS)) | (index << OFFSET_BITS)

    # ==== INITIAL RESET ====
    dut.reset.value = 1
    dut.read.value = 0
    dut.write.value = 0
    dut.address.value = 0
    dut.write_block.value = 0
    await Timer(20, units="ns")
    dut.reset.value = 0
    await RisingEdge(dut.clk)

    tag_A = 0x12
    tag_B = 0x34
    index_0 = 0x3
    index_1 = 0x4
    addr_A_0 = make_address(tag_A, index_0)
    addr_B_0 = make_address(tag_B, index_0)
    addr_B_1 = make_address(tag_B, index_1)

    # ==== Test 1: Cold miss ====
    dut.address.value = addr_A_0
    dut.read.value = 1
    await RisingEdge(dut.clk)
    dut.read.value = 0
    await RisingEdge(dut.clk)
    assert dut.hit.value == 0, "❌ Expected miss on cold read"
    cocotb.log.info("✅ Cold read miss passed")

    # ==== Test 2: Basic write/read ====
    data1 = 0xCAFEBABE
    dut.address.value = addr_A_0
    dut.write_block.value = data1
    dut.write.value = 1
    await RisingEdge(dut.clk)
    dut.write.value = 0
    await RisingEdge(dut.clk)

    dut.address.value = addr_A_0
    dut.read.value = 1
    await RisingEdge(dut.clk)
    dut.read.value = 0
    await RisingEdge(dut.clk)
    assert dut.hit.value == 1, "❌ Expected hit after write"
    assert dut.read_data.value == data1, f"❌ Data mismatch. Got {hex(int(dut.read_data.value))}"
    cocotb.log.info("✅ Write + Read hit passed")

    # ==== Test 3: Same index, different tag = miss ====
    dut.address.value = addr_B_0
    dut.read.value = 1
    await RisingEdge(dut.clk)
    dut.read.value = 0
    await RisingEdge(dut.clk)
    assert dut.hit.value == 0, "❌ Expected conflict miss"
    cocotb.log.info("✅ Conflict miss passed")

    # ==== Test 4: Overwrite same tag/index ====
    data2 = 0xDEADBEEF
    dut.address.value = addr_A_0
    dut.write_block.value = data2
    dut.write.value = 1
    await RisingEdge(dut.clk)
    dut.write.value = 0
    await RisingEdge(dut.clk)

    dut.address.value = addr_A_0
    dut.read.value = 1
    await RisingEdge(dut.clk)
    dut.read.value = 0
    await RisingEdge(dut.clk)
    assert dut.hit.value == 1 and dut.read_data.value == data2, "❌ Overwrite failed"
    cocotb.log.info("✅ Overwrite test passed")

    # ==== Test 5: Evict by tag ====
    dut.address.value = addr_B_0
    dut.write_block.value = 0xBADDCAFE
    dut.write.value = 1
    await RisingEdge(dut.clk)
    dut.write.value = 0
    await RisingEdge(dut.clk)

    # Should evict addr_A_0
    dut.address.value = addr_A_0
    dut.read.value = 1
    await RisingEdge(dut.clk)
    dut.read.value = 0
    await RisingEdge(dut.clk)
    assert dut.hit.value == 0, "❌ Expected eviction miss"
    cocotb.log.info("✅ Eviction (tag replacement) passed")

    # Should hit on addr_B_0
    dut.address.value = addr_B_0
    dut.read.value = 1
    await RisingEdge(dut.clk)
    dut.read.value = 0
    await RisingEdge(dut.clk)
    assert dut.hit.value == 1, "❌ Expected hit on new tag"
    cocotb.log.info("✅ Hit after eviction passed")

    # ==== Test 6: Multiple indexes ====
    dut.address.value = addr_B_1
    dut.write_block.value = 0x12345678
    dut.write.value = 1
    await RisingEdge(dut.clk)
    dut.write.value = 0
    await RisingEdge(dut.clk)

    # Should hit at index_1, tag_B
    dut.address.value = addr_B_1
    dut.read.value = 1
    await RisingEdge(dut.clk)
    dut.read.value = 0
    await RisingEdge(dut.clk)
    assert dut.hit.value == 1, "❌ Expected hit at different index"
    cocotb.log.info("✅ Multiple index read passed")

    # Make sure index_0 still valid (addr_B_0)
    dut.address.value = addr_B_0
    dut.read.value = 1
    await RisingEdge(dut.clk)
    dut.read.value = 0
    await RisingEdge(dut.clk)
    assert dut.hit.value == 1, "❌ Index 0 was overwritten unexpectedly"
    cocotb.log.info("✅ No interference between indexes")

    # ==== Test 7: Reset clears valid bits ====
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    await RisingEdge(dut.clk)

    # Try reading addr_B_0 after reset
    dut.address.value = addr_B_0
    dut.read.value = 1
    await RisingEdge(dut.clk)
    dut.read.value = 0
    await RisingEdge(dut.clk)
    assert dut.hit.value == 0, "❌ Expected miss after reset"
    cocotb.log.info("✅ Reset clears cache")

    cocotb.log.info("🎉 ALL 7 cache_storage tests PASSED ✅")
