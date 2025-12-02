"""
核心爬虫类 - 负责主要的爬取逻辑
"""

import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from urllib.parse import urljoin, urlparse

from core.url_normalizer import URLNormalizer
from analyzers.html_analyzer import HTMLAnalyzer
from analyzers.js_analyzer import JavaScriptAnalyzer
from analyzers.api_extractor import FixedAPIExtractor
from analyzers.hash_discoverer import HashPatternDiscoverer
from utils.validation_utils import is_valid_url

class FixedMainSpider:
    """修复版主爬虫类 - 强制使用UTF-8编码"""
    
    def __init__(self, urls, max_depth=5, max_files=0, thread_count=10):
        self.urls = urls
        self.max_depth = max_depth
        self.max_files = max_files
        self.thread_count = thread_count
        
        self._stop_event = threading.Event()
        self.is_running = False


        
        self.session = requests.Session()
        self.session.verify = False
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 使用URL哈希来避免重复爬取
        self.visited_hashes = set()
        self.found_files = []
        self.found_api_paths = set()
        
        # 初始化所有组件
        self.html_analyzer = HTMLAnalyzer()
        self.js_analyzer = JavaScriptAnalyzer()
        self.hash_discoverer = HashPatternDiscoverer()
        self.api_extractor = FixedAPIExtractor()
        
        print(f"🚀 初始化修复爬虫: {len(urls)}个URL, 深度={max_depth}, 线程数={thread_count}")

    def start_sync(self):
        """同步启动爬虫"""
        print("🔄 开始修复爬取...")
        
        try:
            self._stop_event.clear()
            self.is_running = True
            
            self._fixed_crawl()
            
            results = self._prepare_final_results()
            print(f"✅ 修复爬取完成: {len(self.found_files)}文件, {len(self.found_api_paths)}API")
            return results
            
        except Exception as e:
            print(f"❌ 修复爬取失败: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return self._get_error_results(str(e))
    
    def _fixed_crawl(self):
        """修复爬取过程 - 重点增强API发现"""
        try:
            for url in self.urls:
                if self._stop_event.is_set() or not self.is_running:
                    break
                    
                url = url.strip()
                if url and is_valid_url(url):
                    print(f"🌐 开始深度爬取: {url}")
                    self._crawl_site_fixed(url)
                else:
                    print(f"⚠️ 无效的URL: {url}")
                    
        except Exception as e:
            print(f"❌ 爬虫运行异常: {e}")
        finally:
            self.is_running = False
    
    def _crawl_site_fixed(self, base_url):
        """修复版本站点爬取 - 强制使用UTF-8编码"""
        url_hash = URLNormalizer.get_url_hash(base_url)
        if url_hash in self.visited_hashes:
            print(f"⏭️ 跳过已访问URL: {base_url}")
            return
            
        self.visited_hashes.add(url_hash)
        
        try:
            print(f"📥 请求主页面: {base_url}")
            response = self.session.get(base_url, timeout=15)
            
            if response.status_code != 200:
                print(f"❌ 请求失败: {base_url} - 状态码: {response.status_code}")
                return
            
            # 强制使用UTF-8编码解码内容
            content = self._decode_content_fixed(response.content, response.encoding)
            print(f"✅ 获取成功: {base_url} - 大小: {len(content)} 字节")
            
            self._record_file(base_url, 'html', content)
            
            # 使用所有组件发现资源
            resources = self._discover_fixed_resources(content, base_url)
            print(f"🔍 从 {base_url} 中发现 {len(resources)} 个资源")
            
            # 重点修复：增强API提取
            print(f"🎯 开始从 {base_url} 提取API...")
            apis = self.api_extractor.extract_apis_from_content(content, base_url)
            if apis:
                # 只保留同站点的API
                site_domain = URLNormalizer.get_domain(base_url)
                for api in apis:
                    api_domain = URLNormalizer.get_domain(api)
                    if api_domain == site_domain:
                        self.found_api_paths.add(api)
                
                print(f"✅ 从 {base_url} 中发现 {len(apis)} 个API，保留 {len([a for a in apis if URLNormalizer.get_domain(a) == site_domain])} 个同站点API")
                # 打印前几个API作为示例
                for i, api in enumerate(list(apis)[:3]):
                    print(f"  {i+1}. {api}")
            else:
                print(f"⚠️ 从 {base_url} 中未发现API")
            
            # 并行爬取资源 - 使用URL哈希避免重复
            unique_resources = self._get_unique_resources(resources)
            self._crawl_resources_parallel(list(unique_resources))
                        
        except Exception as e:
            print(f"❌ 爬取站点失败 {base_url}: {e}")
    
    def _decode_content_fixed(self, content, encoding=None):
        """强制使用UTF-8编码解码内容"""
        try:
            # 优先尝试UTF-8
            try:
                return content.decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                pass
            
            # 如果UTF-8失败，尝试检测编码
            import chardet
            detected = chardet.detect(content)
            if detected['encoding'] and detected['encoding'].lower() != 'utf-8':
                try:
                    decoded = content.decode(detected['encoding'], errors='replace')
                    print(f"🔤 使用检测到的编码: {detected['encoding']} (置信度: {detected['confidence']:.2f})")
                    return decoded
                except UnicodeDecodeError:
                    pass
            
            # 最后尝试其他常见编码
            for enc in ['gbk', 'gb2312', 'latin1', 'iso-8859-1']:
                try:
                    return content.decode(enc, errors='replace')
                except UnicodeDecodeError:
                    continue
            
            # 如果所有方法都失败，强制使用UTF-8并替换错误字符
            return content.decode('utf-8', errors='replace')
            
        except Exception as e:
            print(f"内容解码失败，使用强制UTF-8: {e}")
            return content.decode('utf-8', errors='replace')

    def _get_unique_resources(self, resources):
        """获取唯一的资源URL，避免重复爬取"""
        unique_resources = set()
        for resource in resources:
            url_hash = URLNormalizer.get_url_hash(resource)
            if url_hash not in self.visited_hashes:
                unique_resources.add(resource)
        return unique_resources
    
    def _discover_fixed_resources(self, html_content, base_url):
        """使用所有组件发现资源"""
        resources = set()
        
        # HTML分析
        html_resources = self.html_analyzer.extract_resources_from_html(html_content, base_url)
        resources.update(html_resources)
        print(f"  HTML分析发现 {len(html_resources)} 个资源")
        
        # 常见路径生成
        common_resources = self._generate_common_resources(base_url)
        resources.update(common_resources)
        print(f"  常见路径生成 {len(common_resources)} 个资源")
        
        return resources
    
    def _generate_common_resources(self, base_url):
        """生成常见资源路径"""
        resources = set()
        
        # 前端框架常见文件
        framework_files = [
            'app.js', 'main.js', 'index.js', 'bundle.js', 'vendor.js', 'runtime.js',
            'manifest.json', 'package.json', 'webpack.config.js',
            # Vue
            'App.vue', 'app.vue', 'main.vue',
            # React
            'App.js', 'App.jsx', 'index.jsx',
            # Angular
            'main.ts', 'polyfills.ts', 'runtime.ts',
        ]
        
        # 常见目录
        directories = [
            '', '/static/', '/assets/', '/public/', '/dist/', '/build/', '/js/',
            '/static/js/', '/assets/js/'
        ]
        
        for directory in directories:
            for file in framework_files:
                test_url = urljoin(base_url, directory + file)
                resources.add(test_url)
        
        return resources
    
    def _crawl_resources_parallel(self, resources):
        """并行爬取资源"""
        if not resources:
            return
        
        # 限制并发数量
        max_workers = min(self.thread_count, len(resources))
        print(f"🔄 开始并行爬取 {len(resources)} 个资源 (线程数: {max_workers})")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 只提交未访问过的URL
            futures = []
            for url in resources:
                url_hash = URLNormalizer.get_url_hash(url)
                if url_hash not in self.visited_hashes:
                    future = executor.submit(self._crawl_single_resource_fixed, url)
                    futures.append(future)
            
            # 等待所有任务完成
            completed = 0
            for future in as_completed(futures):
                if self._stop_event.is_set() or not self.is_running:
                    break
                try:
                    future.result(timeout=10)
                    completed += 1
                    if completed % 10 == 0:
                        print(f"📊 资源爬取进度: {completed}/{len(futures)}")
                except Exception as e:
                    continue
            
            print(f"✅ 资源爬取完成: {completed}/{len(futures)}")
    
    def _crawl_single_resource_fixed(self, url, depth=1):
        """爬取单个资源 - 修复版本，强制使用UTF-8编码"""
        url_hash = URLNormalizer.get_url_hash(url)
        if url_hash in self.visited_hashes:
            return
            
        self.visited_hashes.add(url_hash)
        
        if self._stop_event.is_set() or not self.is_running or depth > self.max_depth:
            return
        # 获取文件类型并过滤CSS文件
        file_type = self._get_file_type(url)
        if file_type == 'css':
            print(f"⏭️ 跳过CSS文件: {url}")
            return
        try:
            print(f"📥 请求资源: {url}")
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return
            
            # 强制使用UTF-8编码
            content = self._decode_content_fixed(response.content, response.encoding)
            file_type = self._get_file_type(url)
            
            self._record_file(url, file_type, content)
            
            # 重点修复：从资源中提取API
            apis = self.api_extractor.extract_apis_from_content(content, url)
            if apis:
                # 只保留同站点的API
                site_domain = URLNormalizer.get_domain(self.urls[0]) if self.urls else ""
                for api in apis:
                    api_domain = URLNormalizer.get_domain(api)
                    if api_domain == site_domain:
                        self.found_api_paths.add(api)
                print(f"🎯 从资源 {url} 中发现 {len(apis)} 个API")
            
            # 如果是JS文件，深度分析
            if file_type == 'javascript':
                js_resources = self.js_analyzer.analyze_javascript(content, url)
                # 避免重复爬取
                unique_js_resources = self._get_unique_resources(js_resources)
                for resource in list(unique_js_resources)[:10]:  # 限制数量
                    if not self.is_running:
                        continue
                    self._crawl_single_resource_fixed(resource, depth + 1)
                        
        except Exception as e:
            print(f"爬取资源失败 {url}: {e}")
    
    def _get_file_type(self, url):
        """获取文件类型"""
        try:
            path = urlparse(url).path.lower()
            
            if path.endswith(('.js', '.jsx', '.ts', '.tsx', '.mjs')):
                return 'javascript'
            elif path.endswith(('.css', '.scss', '.less', '.sass')):
                return 'css'
            elif path.endswith(('.html', '.htm', '.xhtml', '.php')):
                return 'html'
            elif path.endswith(('.json', '.jsonp')):
                return 'json'
            elif path.endswith(('.vue', '.jsx', '.tsx')):
                return 'framework'
            else:
                return 'other'
        except Exception:
            return 'other'
    
    def _record_file(self, url, file_type, content):
        """记录文件"""
        file_info = {
            'url': url,
            'type': file_type,
            'content': content,
            'size': len(content),
            'status_code': 200
        }
        self.found_files.append(file_info)
        
        print(f"📝 记录文件: {file_type} - {url}")
    
    def _prepare_final_results(self):
        """准备最终结果 - 直接返回字典格式"""
        results = {
            'files': self.found_files.copy(),
            'api_paths': list(self.found_api_paths),
            'visited_count': len(self.visited_hashes),
            'results_set': {
                'files_found': len(self.found_files),
                'apis_found': len(self.found_api_paths),
                'total_visited': len(self.visited_hashes)
            }
        }
        print(f"📊 准备最终结果: {len(results['files'])} 文件, {len(results['api_paths'])} API")
        return results
    
    def _get_error_results(self, error):
        """错误结果 - 直接返回字典格式"""
        return {
            'files': [],
            'api_paths': [],
            'visited_count': 0,
            'results_set': {
                'files_found': 0,
                'apis_found': 0,
                'total_visited': 0
            },
            'error': error
        }