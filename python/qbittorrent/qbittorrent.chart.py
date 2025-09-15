# -*- coding: utf-8 -*-
# Description: qBittorrent netdata python.d module using qbittorrent-api
# Version: v1.1.1
# Author: wujinjun-MC and Gemini

import json
try:
    from qbittorrentapi import Client, APIConnectionError, Unauthorized401Error
except ImportError:
    Client = None
    APIConnectionError = None
    Unauthorized401Error = None

from bases.FrameworkServices.UrlService import UrlService

# charts order (can be overridden if you want less charts, or different order)
ORDER = [
    'speed',
    'total_data',
    'session_data',
    'wasted_data',
    'connections',
    'dht',
    'limits',
    'disk_free',
    'io_cache',
    'io_size',
    'queue_time',
    'buffer_size',
    'share_ratio',
]

CHARTS = {
    'connections': {
        'options': [None, 'Connections', 'connections', 'Connections', 'qbittorrent.connections', 'line'],
        'lines': [
            ['total_peers', 'total connections', 'absolute']
        ]
    },
    'speed': {
        'options': [None, 'Speed', 'B/s', 'Speed', 'qbittorrent.speed', 'line'],
        'lines': [
            ['download_speed', 'download', 'absolute'],
            ['upload_speed', 'upload', 'absolute']
        ]
    },
    'dht': {
        'options': [None, 'DHT Nodes', 'nodes', 'DHT', 'qbittorrent.dht', 'line'],
        'lines': [
            ['dht_nodes', 'nodes', 'absolute']
        ]
    },
    'total_data': {
        'options': [None, 'All Time Data', 'B', 'Data', 'qbittorrent.total_data', 'line'],
        'lines': [
            ['alltime_dl', 'download', 'absolute'],
            ['alltime_ul', 'upload', 'absolute']
        ]
    },
    'session_data': {
        'options': [None, 'Session Data', 'B', 'Data', 'qbittorrent.session_data', 'line'],
        'lines': [
            ['dl_info_data', 'download', 'absolute'],
            ['up_info_data', 'upload', 'absolute']
        ]
    },
    'wasted_data': {
        'options': [None, 'Wasted Session Data', 'B', 'Data', 'qbittorrent.wasted_data', 'line'],
        'lines': [
            ['total_wasted_session', 'wasted data', 'absolute']
        ]
    },
    'limits': {
        'options': [None, 'Speed Limits', 'B/s', 'Limits', 'qbittorrent.limits', 'line'],
        'lines': [
            ['dl_rate_limit', 'download limit', 'absolute'],
            ['up_rate_limit', 'upload limit', 'absolute']
        ]
    },
    'disk_free': {
        'options': [None, 'Free Disk Space', 'B', 'Disk', 'qbittorrent.disk_free', 'line'],
        'lines': [
            ['free_space_on_disk', 'free space', 'absolute']
        ]
    },
    'io_cache': {
        'options': [None, 'I/O Cache', 'percentage', 'Cache', 'qbittorrent.io_cache', 'line'],
        'lines': [
            ['read_cache_hits', 'read hits', 'absolute', 1, 1000],
            ['read_cache_overload', 'read overload', 'absolute', 1, 1000],
            ['write_cache_overload', 'write overload', 'absolute', 1, 1000]
        ]
    },
    'io_size': {
        'options': [None, 'I/O Queue Size', 'jobs', 'IO', 'qbittorrent.io_size', 'line'],
        'lines': [
            ['queued_io_jobs', 'jobs', 'absolute'],
            ['total_queued_size', 'size', 'absolute']
        ]
    },
    'queue_time': {
        'options': [None, 'Average Queue Time', 'ms', 'IO', 'qbittorrent.queue_time', 'line'],
        'lines': [
            ['average_time_queue', 'average queue time', 'absolute']
        ]
    },
    'buffer_size': {
        'options': [None, 'Total Buffer Size', 'B', 'IO', 'qbittorrent.buffer_size', 'line'],
        'lines': [
            ['total_buffers_size', 'buffer size', 'absolute']
        ]
    },
    'share_ratio': {
        'options': [None, 'Global Share Ratio', 'ratio', 'Ratio', 'qbittorrent.share_ratio', 'line'],
        'lines': [
            ['global_ratio', 'share ratio', 'absolute', 1, 1000]
        ]
    },
}

class Service(UrlService):
    def __init__(self, configuration=None, name=None):
        UrlService.__init__(self, configuration=configuration, name=name)
        self.order = ORDER
        self.definitions = CHARTS
        self.url = self.configuration.get('url', 'http://127.0.0.1:8080')
        self.username = self.configuration.get('username')
        self.password = self.configuration.get('password')
        self.qbt_client = None

    def _get_data(self):
        """
        Get data from qBittorrent Web API using qbittorrent-api.
        :return: dict or None
        """
        if Client is None:
            self.error("qbittorrent-api library is not installed. Please run 'pip install qbittorrent-api'")
            return None

        try:
            # Initialize client if it's not set
            if self.qbt_client is None:
                host_parts = self.url.split(':')
                host = host_parts[0] + ':' + host_parts[1]
                port = host_parts[2]
                self.qbt_client = Client(
                    host=host,
                    port=port,
                    username=self.username,
                    password=self.password
                )
                self.qbt_client.auth_log_in()
                self.info('Successfully authenticated with qBittorrent.')

            # Get main data
            main_data = self.qbt_client.sync_maindata()
            server_state = main_data.server_state

            # Collect data from server_state
            data = {
                'download_speed': server_state.dl_info_speed,
                'upload_speed': server_state.up_info_speed,
                'total_peers': server_state.total_peer_connections,
                'alltime_dl': server_state.alltime_dl,
                'alltime_ul': server_state.alltime_ul,
                'average_time_queue': server_state.average_time_queue,
                'dht_nodes': server_state.dht_nodes,
                'dl_info_data': server_state.dl_info_data,
                'dl_rate_limit': server_state.dl_rate_limit,
                'free_space_on_disk': server_state.free_space_on_disk,
                'global_ratio': float(server_state.global_ratio) * 1000,
                'read_cache_hits': float(server_state.read_cache_hits) * 1000,
                'read_cache_overload': float(server_state.read_cache_overload) * 1000,
                'total_buffers_size': server_state.total_buffers_size,
                'total_queued_size': server_state.total_queued_size,
                'total_wasted_session': server_state.total_wasted_session,
                'up_info_data': server_state.up_info_data,
                'up_rate_limit': server_state.up_rate_limit,
                'write_cache_overload': float(server_state.write_cache_overload) * 1000
            }

            return data

        except Unauthorized401Error:
            self.error('Authentication failed. Re-authenticating...')
            try:
                self.qbt_client.auth_log_in()
                self.info('Successfully re-authenticated with qBittorrent.')
                # Retry fetching data after re-authentication
                main_data = self.qbt_client.sync_maindata()
                server_state = main_data.server_state
                data = {
                    'download_speed': server_state.dl_info_speed,
                    'upload_speed': server_state.up_info_speed,
                    'total_peers': server_state.total_peer_connections,
                    'alltime_dl': server_state.alltime_dl,
                    'alltime_ul': server_state.alltime_ul,
                    'average_time_queue': server_state.average_time_queue,
                    'dht_nodes': server_state.dht_nodes,
                    'dl_info_data': server_state.dl_info_data,
                    'dl_rate_limit': server_state.dl_rate_limit,
                    'free_space_on_disk': server_state.free_space_on_disk,
                    'global_ratio': float(server_state.global_ratio) * 1000,
                    'read_cache_hits': float(server_state.read_cache_hits),
                    'read_cache_overload': float(server_state.read_cache_overload),
                    'total_buffers_size': server_state.total_buffers_size,
                    'total_queued_size': server_state.total_queued_size,
                    'total_wasted_session': server_state.total_wasted_session,
                    'up_info_data': server_state.up_info_data,
                    'up_rate_limit': server_state.up_rate_limit,
                    'write_cache_overload': float(server_state.write_cache_overload)
                }
                return data
            except Exception as e:
                self.error(f'Failed to re-authenticate: {e}')
                return None
        except APIConnectionError as e:
            self.error(f'API Connection Error: {e}')
            self.qbt_client = None
            return None
        except Exception as e:
            self.error(f'Failed to get data from qBittorrent: {e}')
            return None

    def check(self):
        """
        Check if the service is available.
        :return: bool
        """
        if Client is None:
            self.error("qbittorrent-api library is not installed.")
            return False

        try:
            host_parts = self.url.split(':')
            host = host_parts[0] + ':' + host_parts[1]
            port = host_parts[2]
            self.qbt_client = Client(
                host=host,
                port=port,
                username=self.username,
                password=self.password
            )
            self.qbt_client.auth_log_in()
            self.info('Authentication successful, service is available.')
            return True
        except APIConnectionError as e:
            self.error(f'qBittorrent service not available or authentication failed: {e}')
            return False
        except Exception as e:
            self.error(f'An unexpected error occurred during check: {e}')
            return False

    def get_urls(self):
        """
        Override get_urls to not include a default url.
        """
        return {}
