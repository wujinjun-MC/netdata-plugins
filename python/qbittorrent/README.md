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