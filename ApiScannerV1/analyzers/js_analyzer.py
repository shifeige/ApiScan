"""
JavaScript分析器 - 专门从JS文件中提取资源
"""

import re
from urllib.parse import urljoin
from .hash_discoverer import HashPatternDiscoverer

class JavaScriptAnalyzer:
    """JavaScript分析器 - 深度分析JS文件中的资源"""
    
    def __init__(self):
        self.hash_discoverer = HashPatternDiscoverer()
        
        # Webpack特定的资源引用模式
        self.webpack_patterns = [
            # webpackJsonp格式
            re.compile(r'webpackJsonp\([^[]*\[[^]]*\][^,]*,\s*\{[^}]*"([^"]+)":[^,}]+', re.I),
            # __webpack_require__.e 动态导入
            re.compile(r'__webpack_require__\.e\(["\']([^"\']+)["\']\)', re.I),
            # 模块ID映射
            re.compile(r'["\'](\d+)["\']:\s*function', re.I),
        ]
        
        # 通用JS资源引用模式
        self.general_js_patterns = [
            # import() 动态导入
            re.compile(r'import\(["\']([^"\']+)["\']\)', re.I),
            # require.ensure
            re.compile(r'require\.ensure\([^)]*["\']([^"\']+)["\']', re.I),
            # fetch请求中的JS文件
            re.compile(r'fetch\(["\']([^"\']+\.js)["\']\)', re.I),
            # 创建脚本元素
            re.compile(r'createElement\(["\']script["\']\)[^}]*src\s*=\s*["\']([^"\']+)["\']', re.I),
            # JSONP回调
            re.compile(r'callback=([^&"\']+\.js)', re.I),
        ]
    
    def analyze_javascript(self, content, base_url):
        """分析JavaScript文件中的资源引用"""
        resources = set()
        
        try:
            # 1. 提取哈希文件名
            hash_resources = self.hash_discoverer.extract_hash_files(content, base_url)
            resources.update(hash_resources)
            
            # 2. 提取Webpack特定资源
            webpack_resources = self._extract_webpack_resources(content, base_url)
            resources.update(webpack_resources)
            
            # 3. 提取通用JS资源
            general_resources = self._extract_general_js_resources(content, base_url)
            resources.update(general_resources)
            
        except Exception as e:
            print(f"JS分析失败: {e}")
        
        return resources
    
    def _extract_webpack_resources(self, content, base_url):
        """提取Webpack特定资源"""
        resources = set()
        
        for pattern in self.webpack_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match.isdigit():
                    # 如果是数字模块ID，生成可能的文件名
                    possible_names = [
                        f"{match}.js",
                        f"{match}.chunk.js",
                        f"chunk-{match}.js",
                    ]
                    for name in possible_names:
                        full_url = urljoin(base_url, name)
                        resources.add(full_url)
                else:
                    # 直接使用匹配的字符串
                    full_url = urljoin(base_url, match)
                    resources.add(full_url)
        
        return resources
    
    def _extract_general_js_resources(self, content, base_url):
        """提取通用JS资源"""
        resources = set()
        
        for pattern in self.general_js_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                full_url = urljoin(base_url, match)
                resources.add(full_url)
        
        return resources