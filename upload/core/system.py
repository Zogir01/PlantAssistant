import os
import sys
import gc
import esp
import machine

def chip_info():
    """ Returns chip info as an tuple: (platform, uP_ver, machine_id, cpu_freq) """
    return sys.platform, os.uname().release, os.uname().machine, machine.freq()

def mem_info():
    """ Returns memory info as an tuple: (ram_alloc[B], ram_free[B], flash_size[B]) """
    return gc.mem_alloc(), gc.mem_free(), esp.flash_size()

def fs_info():
    """ Returns filesystem info as an tuple: (block_size, total_blocks, free_blocks, total[KB], free[KB]) """
    fs_stats = os.statvfs("/")
    block_size = fs_stats[0]
    total_blocks = fs_stats[2]
    free_blocks = fs_stats[3]
    total = (block_size * total_blocks) // 1024 # KB
    free = (block_size * free_blocks) // 1024   # KB
    return block_size, total_blocks, free_blocks, total, free
    