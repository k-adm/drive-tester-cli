#!/usr/bin/env python3
"""
CLI tool to list and perform quick random-read checks on physical drives connected to a Windows PC.
"""

import sys
import random
import time
import struct

# Check required modules
try:
    import wmi
except ImportError:
    print("Error: The 'wmi' module is required. Install it with 'pip install wmi'.", file=sys.stderr)
    sys.exit(1)

try:
    import win32file
    import win32con
    import winioctlcon
except ImportError:
    print("Error: The 'pywin32' module is required. Install it with 'pip install pywin32'.", file=sys.stderr)
    sys.exit(1)


def check_windows():
    """
    Ensure the script is running on Windows.
    """
    if sys.platform != 'win32':
        print('Error: This tool only runs on Windows.', file=sys.stderr)
        sys.exit(1)


def get_physical_drives():
    """
    Uses WMI to list all physical disk drives and their properties.
    Returns a list of dicts.
    """
    c = wmi.WMI()
    drives = []
    for disk in c.Win32_DiskDrive():
        size_bytes = int(disk.Size) if disk.Size else 0
        drives.append({
            'DeviceID': disk.DeviceID.strip(),
            'Model': (disk.Model or '').strip(),
            'SizeGB': size_bytes / (1024 ** 3),
            'InterfaceType': disk.InterfaceType or 'Unknown'
        })
    return drives


def quick_read_test(device_id, num_reads=25, block_size=4096):
    """
    Perform random read of `num_reads` blocks of `block_size` on the given device.
    Uses Win32 APIs via pywin32 for raw access.
    Measures and reports average latency, throughput, and success rate.
    Requires administrative privileges.
    """
    try:
        handle = win32file.CreateFile(
            device_id,
            win32con.GENERIC_READ,
            win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
            None,
            win32con.OPEN_EXISTING,
            win32con.FILE_ATTRIBUTE_NORMAL,
            None
        )
    except Exception as e:
        print(f"Error opening device: {e}", file=sys.stderr)
        return

    try:
        length_info = win32file.DeviceIoControl(
            handle,
            winioctlcon.IOCTL_DISK_GET_LENGTH_INFO,
            None,
            struct.calcsize('Q')
        )
        (drive_size,) = struct.unpack('Q', length_info)
        max_blocks = drive_size // block_size
        if max_blocks < 1:
            print("Drive is too small for the specified block size.", file=sys.stderr)
            return

        total_bytes = 0
        total_time = 0.0
        successes = 0
        failures = 0

        for i in range(num_reads):
            block_index = random.randint(0, max_blocks - 1)
            offset = block_index * block_size
            percent = (offset / drive_size) * 100
            try:
                win32file.SetFilePointer(handle, offset, win32con.FILE_BEGIN)
                start = time.time()
                _, data = win32file.ReadFile(handle, block_size)
                elapsed = time.time() - start
                read_len = len(data)
                total_bytes += read_len
                total_time += elapsed
                successes += 1
                print(f"[{i+1}/{num_reads}] Block {block_index} (~{percent:.1f}%): Read {read_len} bytes in {elapsed*1000:.2f} ms")
            except win32file.error as e:
                failures += 1
                print(f"[{i+1}/{num_reads}] Block {block_index} (~{percent:.1f}%): Error reading block: {e}")

        print(f"\nSuccess rate: {successes}/{num_reads} ({(successes/num_reads)*100:.1f}%)")
        if successes > 0:
            avg_latency = (total_time / successes) * 1000
            throughput_mb = (total_bytes / (1024**2)) / total_time
            print(f"Average latency: {avg_latency:.2f} ms")
            print(f"Average throughput: {throughput_mb:.2f} MB/s")

    except win32file.error as e:
        print(f"Error during read test setup: {e}", file=sys.stderr)
    finally:
        win32file.CloseHandle(handle)


def interactive_menu():
    """
    Provides an interactive menu for user to select listing or read-test.
    """
    drives = get_physical_drives()
    if not drives:
        print('No physical drives found.')
        return

    while True:
        print("\nSelect an option:")
        print("1) List physical drives")
        print("2) Quick random-read test on a drive")
        print("3) Exit")
        choice = input("Enter choice [1-3]: ")

        if choice == '1':
            for idx, d in enumerate(drives):
                print(f"{idx+1}) {d['DeviceID']} - {d['Model']} - {d['SizeGB']:.2f} GB - {d['InterfaceType']}")

        elif choice == '2':
            for idx, d in enumerate(drives):
                print(f"{idx+1}) {d['DeviceID']} - {d['Model']}")
            sel = input(f"Select drive [1-{len(drives)}]: ")
            try:
                sel_idx = int(sel) - 1
                if 0 <= sel_idx < len(drives):
                    dev = drives[sel_idx]['DeviceID']
                    # Determine total blocks
                    handle = win32file.CreateFile(
                        dev,
                        win32con.GENERIC_READ,
                        win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                        None,
                        win32con.OPEN_EXISTING,
                        win32con.FILE_ATTRIBUTE_NORMAL,
                        None
                    )
                    length_info = win32file.DeviceIoControl(
                        handle,
                        winioctlcon.IOCTL_DISK_GET_LENGTH_INFO,
                        None,
                        struct.calcsize('Q')
                    )
                    win32file.CloseHandle(handle)
                    (drive_size,) = struct.unpack('Q', length_info)
                    block_size = 4096
                    total_blocks = drive_size // block_size
                    print(f"Drive total blocks available: {total_blocks}")

                    # Prompt for number of tests, validate within range
                    default_tests = 25
                    while True:
                        count_input = input(f"Enter number of random-read tests [default {default_tests}, max {total_blocks}]: ")
                        if not count_input.strip():
                            num_tests = default_tests
                        else:
                            try:
                                num_tests = int(count_input)
                            except ValueError:
                                print("Invalid number. Please enter an integer.")
                                continue
                        if num_tests < 1 or num_tests > total_blocks:
                            print(f"Please enter a number between 1 and {total_blocks}.")
                            continue
                        break

                    quick_read_test(dev, num_reads=num_tests)
                else:
                    print("Invalid selection.")
            except Exception:
                print("Invalid input or error retrieving drive info.")

        elif choice == '3':
            print('Exiting.')
            break
        else:
            print("Invalid option, try again.")


def main():
    check_windows()
    interactive_menu()


if __name__ == '__main__':
    main()
