# -*- coding: utf-8 -*-
# Description: qBittorrent netdata python.d module using qbittorrent-api
# Version: v1.2
# Author: wujinjun-MC and Gemini

import json
try:
    from qbittorrentapi import Client, APIConnectionError, Unauthorized401Error
except ImportError:
    Client = None
    APIConnectionError = None
    Unauthorized401Error = None

# Import for URL parsing
try:
    from urllib.parse import urlparse, urlunparse
except ImportError:
    # Fallback for older Python versions if needed
    from urlparse import urlparse, urlunparse

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
        
        # 从配置中获取 URL, 用户名和密码
        self.url = self.configuration.get('url', 'http://127.0.0.1:8080')
        self.username = self.configuration.get('username')
        self.password = self.configuration.get('password')
        
        # 新增可选开关: 是否忽略SSL证书 (verify_ssl: yes/no)
        # 修正: 确保配置值在调用 lower() 之前是字符串类型
        verify_ssl_config = str(self.configuration.get('verify_ssl', 'yes')).lower()
        self.verify_ssl = verify_ssl_config in ['yes', 'true', '1']
        
        self.qbt_client = None

    def _try_connect_with_scheme(self, full_url, log_on_fail=False):
        """尝试使用指定的完整 URL 连接并认证 qBittorrent 客户端。"""
        
        try:
            # qbittorrent-api Client 接受完整的 URL 字符串作为 host 参数
            client = Client(
                host=full_url,
                username=self.username,
                password=self.password,
                # Pass the boolean flag for SSL verification
                VERIFY_WEBUI_CERTIFICATE=self.verify_ssl 
            )
            client.auth_log_in()
            self.info(f'成功连接并认证: {full_url}')
            return client
        
        except Unauthorized401Error:
            if log_on_fail:
                self.error(f'认证失败: {full_url}')
        except APIConnectionError as e:
            if log_on_fail:
                # 区分连接错误和证书错误
                cert_error = 'certificate verify failed'
                if cert_error in str(e) and self.verify_ssl:
                    self.error(f'连接失败 (SSL证书验证失败): {full_url}。请检查证书或在配置中设置 verify_ssl: no')
                else:
                    self.error(f'连接失败: {full_url}。错误: {e}')
        except Exception as e:
            if log_on_fail:
                self.error(f'尝试连接时发生意外错误: {full_url}, 错误: {e}')
        
        return None

    def _initialize_client(self, log_on_fail=False):
        """
        处理 URL 格式，并尝试使用自动检测的协议连接 qBittorrent。
        如果配置中未指定协议 (e.g., '127.0.0.1:8080')，则先尝试 HTTPS 后尝试 HTTP。
        """
        
        if Client is None:
            self.error("qbittorrent-api 库未安装。请运行 'pip install qbittorrent-api'")
            return None
        
        parsed_url = urlparse(self.url)
        
        # 提取 hostname 和 port (netloc)
        netloc = parsed_url.netloc
        if not netloc and parsed_url.path:
            # 兼容用户只输入 host:port 的情况
            netloc = parsed_url.path
        
        if not netloc:
            if log_on_fail:
                self.error(f"无效的 URL 配置: {self.url}")
            return None

        # 确定要尝试的协议列表
        if parsed_url.scheme in ('http', 'https'):
            # 如果指定了协议，只尝试指定的协议
            schemes_to_try = [parsed_url.scheme]
        else:
            # 如果未指定协议 (e.g., '127.0.0.1:8080')，则先尝试 HTTPS 后尝试 HTTP
            schemes_to_try = ['https', 'http']
        
        for scheme in schemes_to_try:
            # 构造完整的 URL (使用空路径、参数等)
            full_url = urlunparse((scheme, netloc, '', '', '', ''))
            client = self._try_connect_with_scheme(full_url, log_on_fail)
            if client:
                return client
            
        # 所有尝试失败
        if log_on_fail and not parsed_url.scheme:
            self.error(f"无法连接到 qBittorrent。所有协议尝试 ({netloc} + {schemes_to_try}) 均失败。")
        return None

    def _get_data(self):
        """
        Get data from qBittorrent Web API using qbittorrent-api.
        :return: dict or None
        """
        
        # 1. 尝试初始化或重用客户端
        try:
            # 客户端未初始化
            if self.qbt_client is None:
                self.qbt_client = self._initialize_client(log_on_fail=True)
                if not self.qbt_client:
                    return None
        except Exception as e:
            self.error(f'客户端初始化失败: {e}')
            self.qbt_client = None
            return None
            
        # 2. 获取数据
        try:
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
            # 会话过期或令牌失效
            self.error('会话过期，尝试重新认证...')
            self.qbt_client = None # 强制重新初始化
            
            # 重新初始化客户端
            self.qbt_client = self._initialize_client(log_on_fail=True)
            if not self.qbt_client:
                return None
            
            # 如果重新认证成功，重试获取数据
            try:
                main_data = self.qbt_client.sync_maindata()
                server_state = main_data.server_state
                # 重新构造数据字典 (使用与上方相同的逻辑)
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
            except Exception as e:
                self.error(f'重新认证后获取数据失败: {e}')
                self.qbt_client = None
                return None

        except APIConnectionError as e:
            self.error(f'API 连接错误: {e}')
            self.qbt_client = None
            return None
        except Exception as e:
            self.error(f'获取数据失败: {e}')
            return None

    def check(self):
        """
        检查服务是否可用。
        :return: bool
        """
        # 使用统一的初始化方法进行检查
        self.qbt_client = self._initialize_client(log_on_fail=True)
        
        if self.qbt_client:
            self.info('服务检查成功，已连接并认证。')
            return True
        else:
            self.error('服务检查失败。无法连接或认证。')
            return False

    def get_urls(self):
        """
        Override get_urls to not include a default url.
        """
        return {}
