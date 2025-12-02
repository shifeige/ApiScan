"""
哈希文件发现器 - 专门发现哈希命名的前端资源文件
"""

import re
from urllib.parse import urljoin

class HashPatternDiscoverer:
    """哈希文件名模式发现器"""
    
    def __init__(self):
        # 增强的哈希文件名模式
        self.hash_patterns = [
            # 短哈希: user.1974bcaa.js
            re.compile(r'["\']([a-zA-Z0-9_-]+\.[a-f0-9]{8}\.js)["\']', re.I),
            # 中等哈希: user.1974bcaa1234.js
            re.compile(r'["\']([a-zA-Z0-9_-]+\.[a-f0-9]{8,12}\.js)["\']', re.I),
            # 长哈希: user.1974bcaa12345678.js
            re.compile(r'["\']([a-zA-Z0-9_-]+\.[a-f0-9]{12,16}\.js)["\']', re.I),
            # 纯哈希: 1974bcaa.js
            re.compile(r'["\']([a-f0-9]{8}\.js)["\']', re.I),
            # 纯长哈希: 1974bcaa12345678.js
            re.compile(r'["\']([a-f0-9]{12,16}\.js)["\']', re.I),
            # 带chunk的哈希: user.1974bcaa.chunk.js
            re.compile(r'["\']([a-zA-Z0-9_-]+\.[a-f0-9]{8,12}\.chunk\.js)["\']', re.I),
            # Webpack 5格式: user-1974bcaa.js
            re.compile(r'["\']([a-zA-Z0-9_-]+-[a-f0-9]{8,12}\.js)["\']', re.I),
            # Vite格式: user-1974bcaa.js
            re.compile(r'["\']([a-zA-Z0-9_-]+-[a-f0-9]{8}\.js)["\']', re.I),
            # 通用哈希模式: 任何包含8-16位十六进制字符的.js文件
            re.compile(r'["\']([^"\']*[a-f0-9]{8,16}[^"\']*\.js)["\']', re.I),
        ]
        
        # CSS哈希模式
        self.css_hash_patterns = [
            re.compile(r'["\']([a-zA-Z0-9_-]+\.[a-f0-9]{8,12}\.css)["\']', re.I),
            re.compile(r'["\']([a-f0-9]{8,12}\.css)["\']', re.I),
        ]
        
        # 常见的前端文件命名模式
        self.common_patterns = [
            # 主入口文件
            re.compile(r'["\'](main\.[a-f0-9]+\.js)["\']', re.I),
            re.compile(r'["\'](app\.[a-f0-9]+\.js)["\']', re.I),
            re.compile(r'["\'](bundle\.[a-f0-9]+\.js)["\']', re.I),
            # 运行时文件
            re.compile(r'["\'](runtime~[a-f0-9]+\.js)["\']', re.I),
            re.compile(r'["\'](runtime\.[a-f0-9]+\.js)["\']', re.I),
            # Vendor文件
            re.compile(r'["\'](vendor\.[a-f0-9]+\.js)["\']', re.I),
            re.compile(r'["\'](chunk-vendors\.[a-f0-9]+\.js)["\']', re.I),
            # 数字chunk
            re.compile(r'["\'](\d+\.[a-f0-9]+\.js)["\']', re.I),
            re.compile(r'["\'](\d+\.chunk\.js)["\']', re.I),
        ]
    
    def extract_hash_files(self, content, base_url):
        """提取所有哈希命名的文件"""
        resources = set()
        
        # 提取JS哈希文件
        for pattern in self.hash_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if self._is_valid_hash_file(match):
                    full_url = urljoin(base_url, match)
                    resources.add(full_url)
                    print(f"发现哈希JS文件: {match} -> {full_url}")
        
        # 提取CSS哈希文件
        for pattern in self.css_hash_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if self._is_valid_hash_file(match):
                    full_url = urljoin(base_url, match)
                    resources.add(full_url)
                    print(f"发现哈希CSS文件: {match} -> {full_url}")
        
        # 提取常见模式文件
        for pattern in self.common_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                full_url = urljoin(base_url, match)
                resources.add(full_url)
                print(f"发现常见模式文件: {match} -> {full_url}")
        
        return resources
    
    def _is_valid_hash_file(self, filename):
        """验证是否为有效的哈希文件名"""
        if not filename or '.' not in filename:
            return False
        
        # 检查文件扩展名
        valid_extensions = ['.js', '.css', '.jsx', '.ts', '.tsx', '.vue']
        if not any(filename.endswith(ext) for ext in valid_extensions):
            return False
        
        # 检查是否包含哈希（8-16位十六进制字符）
        hash_match = re.search(r'[a-f0-9]{8,16}', filename.lower())
        if not hash_match:
            return False
        
        return True