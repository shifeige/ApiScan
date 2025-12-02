"""
URL规范化工具 - 负责URL的标准化和去重
"""

import hashlib
from urllib.parse import urlparse

class URLNormalizer:
    """URL规范化工具，避免重复爬取"""
    
    @staticmethod
    def normalize_url(url):
        """规范化URL，去除查询参数和片段"""
        try:
            parsed = urlparse(url)
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            # 去除末尾的斜杠
            if normalized.endswith('/'):
                normalized = normalized[:-1]
            return normalized
        except:
            return url
    
    @staticmethod
    def get_url_hash(url):
        """获取URL的哈希值，用于去重"""
        normalized = URLNormalizer.normalize_url(url)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    @staticmethod
    def get_domain(url):
        """获取URL的域名"""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ""