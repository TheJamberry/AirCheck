# AirCheck

CLI broadcast confidence monitor for Linux.

Captures two live audio inputs — an off-air FM receiver and a program feed — and compares them in real time to verify the transmitter is carrying the correct audio. Status is printed to stdout every few seconds, making it easy to integrate with systemd/journalctl.

```
[09:42:15] MATCH           score=0.921 delay=+2341ms
[09:42:17] MATCH           score=0.918 delay=+2344ms
[09:42:19] SILENCE_ON_OFF_AIR
[09:42:21] NOT_MATCHING    score=0.041 delay=+0ms
```

---

## Requirements

- Linux
- Python 3.10 or newer
- A stereo audio input device with both feeds wired in:
  - Channel 1 (left)  — off-air FM receiver
  - Channel 2 (right) — program feed / audio sent to transmitter

---

## Installation

Clone the repo and run the installer:

```bash
git clone https://github.com/TheJamberry/AirCheck.git /opt/aircheck
cd /opt/aircheck
bash scripts/install.sh
```

The installer:
- Creates a Python virtual environment at `.venv/`
- Installs AirCheck and all dependencies (`sounddevice`, `numpy`, `scipy`, `pyyaml`)
- Copies `config.example.yaml` → `config.yaml` if `config.yaml` does not already exist

---

## Listing audio devices

```bash
cd /opt/aircheck
.venv/bin/python -m aircheck.main --list-devices
```

Note the index or name of your 2-channel interface and set `device:` in `config.yaml`.

---

## Editing the config

```bash
nano /opt/aircheck/config.yaml
```

Key settings:

| Setting | Default | Description |
|---|---|---|
| `device` | `0` | Audio device index or name (`--list-devices`) |
| `off_air_channel` | `0` | 0-based channel index for the off-air receiver |
| `program_channel` | `1` | 0-based channel index for the program feed |
| `sample_rate` | `44100` | Sample rate in Hz |
| `chunk_duration` | `8.0` | Seconds of rolling audio held for comparison |
| `check_interval` | `2.0` | Seconds between comparisons |
| `min_rms` | `0.001` | RMS below this is treated as silence |
| `match_threshold` | `0.85` | Similarity score [0–1] required to report MATCH |
| `max_delay_ms` | `5000.0` | Maximum acceptable delay before reporting UNCERTAIN |

`config.yaml` is excluded from git and will never be overwritten by `git pull`.

---

## Running manually

```bash
bash /opt/aircheck/scripts/run-dev.sh
```

Or directly:

```bash
cd /opt/aircheck
.venv/bin/python -m aircheck.main --config config.yaml
```

Stop with `Ctrl+C`.

---

## Installing and running as a systemd service

```bash
sudo cp /opt/aircheck/systemd/aircheck.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable aircheck
sudo systemctl start aircheck
```

Check status:

```bash
sudo systemctl status aircheck
```

Follow live output:

```bash
journalctl -u aircheck -f
```

---

## Updating with git pull

```bash
cd /opt/aircheck
git pull
.venv/bin/pip install -e .
sudo systemctl restart aircheck
```

`config.yaml` is ignored by git and will not be touched.

---

## Status codes

| Status | Meaning |
|---|---|
| `MATCH` | Both feeds carry the same audio within the configured delay limit |
| `NOT_MATCHING` | Similarity score below threshold — feeds may have diverged |
| `SILENCE_ON_OFF_AIR` | Off-air receiver is silent (transmitter may be off-air) |
| `SILENCE_ON_PROGRAM` | Program feed is silent (playout system may have failed) |
| `SILENCE_ON_BOTH` | Both feeds are silent |
| `UNCERTAIN` | Not enough data yet, comparison error, or delay exceeds limit |

---

## How it works

1. A rolling buffer of `chunk_duration` seconds of stereo audio is captured from the configured device.
2. Every `check_interval` seconds the buffer is sampled.
3. Each channel is RMS-normalised so level differences do not affect the result.
4. `scipy.signal.correlate` computes the normalised cross-correlation between the two channels.
5. The peak of the correlation function gives a similarity score [0–1] and the lag (in ms) between the two feeds.
6. The result is mapped to one of the status codes above and printed to stdout.

## Disclaimer

This project was built with AI assistance by a non-programmer to solve a specific real-world need. No existing tool did what was required, so this one was created.

The code has been reviewed and researched, but you should evaluate it yourself before using it in a broadcast environment.