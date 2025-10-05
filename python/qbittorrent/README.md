# Netdata python.d plugin to collect qBittorrent data

## Installation

1. Install necessary packages
```bash
apt install pip
pip install --break-system-packages requests qbittorrent-api
```
2. Copy [qbittorrent.conf](qbittorrent.conf) to /etc/netdata/python.d/
3. Copy [qbittorrent.chart.py](qbittorrent.chart.py) to /usr/libexec/netdata/python.d/
4. Append the line "qbittorrent: yes" in /usr/lib/netdata/conf.d/python.d.conf
5. Type your web ui url, username and password in qbittorrent.conf
5. Restart netdata (or container)

## Config

File: `qbittorrent.conf`
| **#** | **Config** | **Description** | **Default** |
|---|---|---|---|
| **1** | update_every | int: (Netdata internal)Chart update frequency (second) | 5 |
| **2** | priority | int: (Netdata internal)Where it is shown on dashboard. 1=top, 99999999=button | 20000 |
| **3** | url | string: qBittorrent WebUI url. Without `http://` or `https://` = auto detect | 127.0.0.1 |
| **4** | username | string: qBittorrent WebUI user name | example |
| **5** | password | string: qBittorrent WebUI password | example |
| **6** | verify_ssl | bool(yes/no): Verify SSL certificate if HTTPS | yes |