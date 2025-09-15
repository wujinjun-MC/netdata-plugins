# -*- coding: utf-8 -*-
# Description: qBittorrent netdata python.d module using qbittorrent-api
# Version: v1.0
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
    'connections',
    'total_data',
    'session_data',
    'limits',
    'dht',
    'io_cache',
    'io_size',
    'misc'
]

CHARTS = {
    'connections': {
        'options': [None, 'Connections', 'connections', 'connections', 'qbittorrent.connections', 'line'],
        'lines': [
            ['total_peers', 'total_connections', 'absolute']
        ]
    },
    'speed': {
        'options': [None, 'Speed', 'KB/s', 'speed', 'qbittorrent.speed', 'line'],
        'lines': [
            ['download_speed', 'download', 'incremental', 1, 1024],
            ['upload_speed', 'upload', 'incremental', 1, 1024]
        ]
    },
    'total_data': {
        'options': [None, 'All Time Data', 'GB', 'data', 'qbittorrent.total_data', 'line'],
        'lines': [
            ['alltime_dl', 'download', 'absolute', 1, 1073741824],
            ['alltime_ul', 'upload', 'absolute', 1, 1073741824]
        ]
    },
    'session_data': {
        'options': [None, 'Session Data', 'MB', 'data', 'qbittorrent.session_data', 'line'],
        'lines': [
            ['dl_info_data', 'download', 'absolute', 1, 1048576],
            ['up_info_data', 'upload', 'absolute', 1, 1048576],
            ['total_wasted_session', 'wasted', 'absolute', 1, 1048576]
        ]
    },
    'limits': {
        'options': [None, 'Speed Limits', 'KB/s', 'limits', 'qbittorrent.limits', 'line'],
        'lines': [
            ['dl_rate_limit', 'download_limit', 'absolute', 1, 1024],
            ['up_rate_limit', 'upload_limit', 'absolute', 1, 1024]
        ]
    },
    'dht': {
        'options': [None, 'DHT Nodes', 'nodes', 'dht', 'qbittorrent.dht', 'line'],
        'lines': [
            ['dht_nodes', 'nodes', 'absolute']
        ]
    },
    'io_cache': {
        'options': [None, 'I/O Cache', 'percentage', 'cache', 'qbittorrent.io_cache', 'line'],
        'lines': [
            ['read_cache_hits', 'read_hits', 'absolute'],
            ['read_cache_overload', 'read_overload', 'absolute'],
            ['write_cache_overload', 'write_overload', 'absolute']
        ]
    },
    'io_size': {
        'options': [None, 'I/O Queue Size', 'jobs', 'io', 'qbittorrent.io_size', 'line'],
        'lines': [
            ['queued_io_jobs', 'jobs', 'absolute'],
            ['total_queued_size', 'size', 'absolute']
        ]
    },
    'misc': {
        'options': [None, 'Miscellaneous Stats', 'value', 'stats', 'qbittorrent.misc', 'line'],
        'lines': [
            ['average_time_queue', 'avg_queue_time', 'absolute'],
            ['total_buffers_size', 'buffer_size', 'absolute'],
            ['global_ratio', 'share_ratio', 'absolute']
        ]
    }
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
                'global_ratio': float(server_state.global_ratio), # convert to float
                'read_cache_hits': float(server_state.read_cache_hits), # convert to float
                'read_cache_overload': float(server_state.read_cache_overload), # convert to float
                'total_buffers_size': server_state.total_buffers_size,
                'total_queued_size': server_state.total_queued_size,
                'total_wasted_session': server_state.total_wasted_session,
                'up_info_data': server_state.up_info_data,
                'up_rate_limit': server_state.up_rate_limit,
                'write_cache_overload': float(server_state.write_cache_overload) # convert to float
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
                    'global_ratio': float(server_state.global_ratio),
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
