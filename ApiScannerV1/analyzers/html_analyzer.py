"""
HTML分析器 - 专门从HTML中提取资源
"""

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .hash_discoverer import HashPatternDiscoverer

class HTMLAnalyzer:
    """HTML分析器 - 专门提取JS/CSS资源"""
    
    def __init__(self):
        self.hash_discoverer = HashPatternDiscoverer()
    
    def extract_resources_from_html(self, html_content, base_url):
        """从HTML中提取所有资源"""
        resources = set()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 1. 提取脚本标签
            scripts = soup.find_all('script', src=True)
            for script in scripts:
                src = script.get('src', '').strip()
                if src and not src.startswith(('javascript:', 'data:')):
                    full_url = urljoin(base_url, src)
                    resources.add(full_url)
                    print(f"从script标签发现: {src} -> {full_url}")
            
            # 2. 提取链接标签 (CSS)
            links = soup.find_all('link', rel=True)
            for link in links:
                rel = link.get('rel', [])
                href = link.get('href', '').strip()
                
                if href and ('stylesheet' in rel or 'preload' in rel or 'prefetch' in rel):
                    if not href.startswith(('javascript:', 'data:')):
                        full_url = urljoin(base_url, href)
                        resources.add(full_url)
                        print(f"从link标签发现: {href} -> {full_url}")
            
            # 3. 提取其他可能包含资源链接的属性
            resource_attrs = ['src', 'href', 'data-src', 'data-href', 'data-url']
            for tag in soup.find_all(True):  # 所有标签
                for attr in resource_attrs:
                    attr_value = tag.get(attr, '').strip()
                    if attr_value and self._is_resource_url(attr_value):
                        full_url = urljoin(base_url, attr_value)
                        resources.add(full_url)
                        print(f"从{attr}属性发现: {attr_value} -> {full_url}")
            
            # 4. 从内联脚本中提取资源
            inline_scripts = soup.find_all('script', string=True)
            for script in inline_scripts:
                script_content = script.string
                if script_content:
                    inline_resources = self.hash_discoverer.extract_hash_files(script_content, base_url)
                    resources.update(inline_resources)
            
        except Exception as e:
            print(f"HTML解析失败: {e}")
        
        return resources
    
    def _is_resource_url(self, url):
        """判断是否为资源URL"""
        if not url or url.startswith(('javascript:', 'mailto:', 'tel:', '#')):
            return False
        
        # 检查是否为静态资源
        resource_extensions = ['.js', '.css', '.json', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico']
        if any(url.endswith(ext) for ext in resource_extensions):
            return True
        
        # 检查是否包含静态资源路径
        static_paths = ['/static/', '/assets/', '/public/', '/dist/', '/build/']
        if any(path in url for path in static_paths):
            return True
        
        return False