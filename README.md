# Windows Physical Drive Tester CLI

A Python-based command-line tool to list physical disk drives on a Windows PC and perform quick random-read health checks.

## Features

- **List Physical Drives**: Enumerates all connected physical disks (e.g., `\\.\PHYSICALDRIVE0`) via WMI.
- **Interactive Menu**: Choose between listing drives, running a random-read test, or exiting.
- **Random-Read Health Test**:
  - Performs a series of random block reads on a selected drive.
  - Configurable number of tests (default: 25).
  - Reports per-read details: block index, approximate location percentage (0%–100%), bytes read, and latency in milliseconds.
  - Calculates and displays:
    - **Success Rate** (number of successful reads vs. total tests).
    - **Average Latency** (ms).
    - **Average Throughput** (MB/s).
- **Input Validation**:
  - Ensures the requested number of tests does not exceed the total blocks on the drive.
  - Re-prompts the user until a valid test count is entered.

## Requirements

See [requirements.txt](requirements.txt) for required Python packages:

- `wmi`
- `pywin32`

## Installation

1. Clone the repository:
   ```powershell
   git clone https://github.com/your-username/windows-drive-tester.git
   cd windows-drive-tester
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```

3. Ensure you run the tool with **Administrator** privileges to allow raw disk access.

## Usage

```powershell
python list_drives.py
```

1. **List drives**: Select option `1` to view all physical disks.
2. **Run health test**: Select option `2`, pick a drive, then enter the number of random-read tests (or press Enter for default 25). The tool will display results and summary.
3. **Exit**: Select option `3`.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

