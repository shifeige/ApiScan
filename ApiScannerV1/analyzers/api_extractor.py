"""
API提取器 - 专门从各种内容中提取API端点
"""

import re
from urllib.parse import urljoin, urlparse

class FixedAPIExtractor:
    """修复版API提取器 - 重点修复API发现问题"""
    
    def __init__(self):
        # 大幅扩展和修复的API模式
        self.api_patterns = [
            # RESTful API - 基础模式（修复分组问题）
            r'["\'](/api/v\d+/[a-zA-Z0-9_\-\.\/]+)["\']',
            r'["\'](/api/[a-zA-Z0-9_\-\.\/]+)["\']',
            r'["\'](/v\d+/[a-zA-Z0-9_\-\.\/]+)["\']',
            r'["\'](/rest/[a-zA-Z0-9_\-\.\/]+)["\']',
            r'["\'](/graphql)["\']',
            r'["\'](/graphql/[a-zA-Z0-9_\-\.\/]*)["\']',
            
            # 通用API路径（修复分组问题）
            r'["\'](/(?:[a-zA-Z0-9_\-\.\/]{3,}\.(?:json|xml|yaml|yml)))["\']',
            r'["\'](/(?:[a-zA-Z0-9_\-\.\/]{3,}))["\']',
            
            # HTTP请求函数 - 修复匹配问题
            r'fetch\(["\']([^"\']*?)["\']',
            r'axios\.(?:get|post|put|delete|patch)\(["\']([^"\']*?)["\']',
            r'\.ajax\([^)]*?url\s*:\s*["\']([^"\']*?)["\']',
            r'\.get\(["\']([^"\']*?)["\']',
            r'\.post\(["\']([^"\']*?)["\']',
            r'\.put\(["\']([^"\']*?)["\']',
            r'\.delete\(["\']([^"\']*?)["\']',
            
            # 配置中的API - 修复匹配问题
            r'["\'](?:apiUrl|baseUrl|endpoint|url)["\']\s*:\s*["\']([^"\']*?)["\']',
            r'["\'](?:API_URL|BASE_URL|ENDPOINT)["\']\s*:\s*["\']([^"\']*?)["\']',
            
            # HTML表单 - 修复匹配问题
            r'action\s*=\s*["\']([^"\']*?)["\']',
            
            # WebSocket - 修复匹配问题
            r'new\s+WebSocket\(["\']([^"\']*?)["\']',
            
            # 常见API端点（新增）
            r'["\'](/user(?:s)?/[a-zA-Z0-9_\-\.\/]*)["\']',
            r'["\'](/auth(?:entication)?/[a-zA-Z0-9_\-\.\/]*)["\']',
            r'["\'](/login)["\']',
            r'["\'](/logout)["\']',
            r'["\'](/register)["\']',
            r'["\'](/profile)["\']',
            r'["\'](/admin/[a-zA-Z0-9_\-\.\/]*)["\']',
            r'["\'](/dashboard/[a-zA-Z0-9_\-\.\/]*)["\']',
            r'["\'](/product(?:s)?/[a-zA-Z0-9_\-\.\/]*)["\']',
            r'["\'](/order(?:s)?/[a-zA-Z0-9_\-\.\/]*)["\']',
            r'["\'](/cart)["\']',
            r'["\'](/checkout)["\']',
            r'["\'](/payment)["\']',
            r'["\'](/config)["\']',
            r'["\'](/settings)["\']',
            
            # 更宽松的路径匹配（新增）
            r'["\'](/(?:[a-z0-9\-]{3,})(?:/[a-z0-9\-]*)*)["\']',
            
            # 模板字符串中的API（新增）
            r'`(/(?:api|v\d+)/[^`\s]+)`',
            
            # 变量中的URL（新增）
            r'(?:const|let|var)\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*=\s*["\']([^"\']+?)["\']',
        ]
        
        # 编译所有模式
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.api_patterns]
        
        print(f"🔧 初始化API提取器，包含 {len(self.compiled_patterns)} 个模式")

    def extract_apis_from_content(self, content, source_url):
        """从内容中提取API路径 - 修复版本"""
        apis = set()
        
        if not content or not isinstance(content, str):
            return apis
            
        print(f"🔍 开始从内容中提取API (长度: {len(content)} 字符)")
        
        for i, pattern in enumerate(self.compiled_patterns):
            try:
                matches = pattern.findall(content)
                for match in matches:
                    if match and isinstance(match, str) and match.strip():
                        api_path = self._normalize_api_path(match.strip(), source_url)
                        if api_path and self._is_valid_api(api_path):
                            apis.add(api_path)
                            print(f"🎯 发现API [{i}]: {match} -> {api_path}")
                            
            except Exception as e:
                print(f"API模式 {i} 匹配失败: {e}")
        
        print(f"✅ 从内容中发现 {len(apis)} 个API路径")
        return apis
    
    def _normalize_api_path(self, path, base_url):
        """规范化API路径 - 修复版本"""
        try:
            if not path or len(path) < 2:
                return None
                
            path = path.strip('"\'').strip()
            
            # 跳过明显无效的路径
            if self._should_skip_path(path):
                return None
            
            # 处理相对路径
            if path.startswith('/'):
                parsed_base = urlparse(base_url)
                normalized = f"{parsed_base.scheme}://{parsed_base.netloc}{path}"
                print(f"🔗 相对路径转换: {path} -> {normalized}")
                return normalized
                
            elif not path.startswith(('http://', 'https://')):
                # 相对路径，需要拼接
                full_url = urljoin(base_url, path)
                parsed = urlparse(full_url)
                # 确保是同一个域名
                base_domain = urlparse(base_url).netloc
                if parsed.netloc == base_domain:
                    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    print(f"🔗 相对路径拼接: {path} -> {normalized}")
                    return normalized
                else:
                    print(f"⚠️ 跳过跨域URL: {path}")
                    return None
            else:
                # 已经是完整URL
                parsed = urlparse(path)
                normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                print(f"🔗 完整URL规范化: {path} -> {normalized}")
                return normalized
                
        except Exception as e:
            print(f"API路径规范化失败 {path}: {e}")
            return None
    
    def _should_skip_path(self, path):
        """判断是否应该跳过该路径"""
        if not path:
            return True
            
        # 跳过协议和特殊协议
        skip_patterns = [
            r'^javascript:', r'^mailto:', r'^tel:', r'^#', r'^data:', r'^blob:',
            r'^about:', r'^file:', r'^ftp:'
        ]
        
        for pattern in skip_patterns:
            try:
                if re.match(pattern, path, re.IGNORECASE):
                    return True
            except:
                continue
        
        # 跳过静态资源扩展名
        static_extensions = [
            '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp', '.svg',
            '.css', '.scss', '.less', '.sass', '.styl',
            '.woff', '.woff2', '.ttf', '.eot', '.otf',
            '.mp4', '.avi', '.mov', '.wmv', '.flv',
            '.mp3', '.wav', '.ogg', '.m4a',
            '.zip', '.rar', '.7z', '.tar', '.gz',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.js', '.jsx', '.ts', '.tsx', '.vue', '.json'  # 也跳过JS文件
        ]
        if any(path.lower().endswith(ext) for ext in static_extensions):
            return True
        
        # 跳过常见静态路径
        static_paths = [
            '/static/', '/assets/', '/public/', '/dist/', '/build/', 
            '/img/', '/images/', '/css/', '/js/', '/fonts/', '/font/',
            '/vendor/', '/lib/', '/node_modules/', '/wp-content/', '/wp-includes/',
            '/_next/', '/_nuxt/', '/.next/', '/.nuxt/'
        ]
        if any(static_path in path.lower() for static_path in static_paths):
            return True
            
        # 跳过过短的路径（可能只是路径片段）
        if len(path) < 3:
            return True
            
        # 跳过只有单个字符的路径段
        if re.match(r'^/[a-zA-Z0-9]$', path):
            return True
            
        return False
    
    def _is_valid_api(self, path):
        """验证是否为有效的API路径"""
        if not path:
            return False
            
        # 这里已经通过_should_skip_path过滤了，主要做额外验证
        parsed = urlparse(path)
        
        # 确保有路径部分
        if not parsed.path or parsed.path == '/':
            return False
            
        # 确保路径长度合理
        if len(parsed.path) < 2:
            return False
            
        return True