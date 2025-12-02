"""
API测试器 - 负责测试发现的API端点
"""

import time
import re  # 添加 re 导入
import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, urljoin  # 确保 urljoin 已导入

from core.url_normalizer import URLNormalizer

class SiteSpecificAPITester:
    """站点专用API测试器 - 每个站点只测试自己的API"""
    
    def __init__(self, site_url, api_paths, test_methods=None, timeout=10, max_workers=5):
        self.site_url = site_url
        self.api_paths = api_paths
        self.test_methods = test_methods or ['GET', 'POST', 'PUT', 'DELETE']
        self.timeout = timeout
        self.max_workers = max_workers
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
        })
        
        self.test_results = []
        print(f"🚀 初始化站点API测试器: {site_url}, {len(api_paths)}个API路径")

    def test_apis(self):
        """测试该站点的所有API"""
        if not self.api_paths:
            print(f"⚠️ 站点 {self.site_url} 没有API路径可测试")
            return []
        
        print(f"🧪 开始测试站点 {self.site_url} 的 {len(self.api_paths)} 个API")
        
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []
                
                for api_path in self.api_paths:
                    full_url = self._build_full_url(api_path)
                    if not full_url:
                        continue
                    
                    for method in self.test_methods:
                        future = executor.submit(self._test_single_api, full_url, method, api_path)
                        futures.append((future, api_path, method, full_url))
                
                completed = 0
                for future, api_path, method, full_url in futures:
                    try:
                        test_result = future.result(timeout=self.timeout + 5)
                        test_result['api_path'] = api_path
                        test_result['site_url'] = self.site_url
                        test_result['full_url'] = full_url
                        test_result['method'] = method
                        
                        self.test_results.append(test_result)
                        
                        completed += 1
                        if completed % 5 == 0:
                            print(f"📊 {self.site_url} API测试进度: {completed}/{len(futures)}")
                            
                    except Exception as e:
                        print(f"API测试异常: {e}")
                        error_result = {
                            'api_path': api_path,
                            'site_url': self.site_url,
                            'full_url': full_url,
                            'method': method,
                            'error': str(e),
                            'status_code': None,
                            'response_time': 0,
                            'content_length': 0,
                            'title': '测试异常',
                            'success': False
                        }
                        self.test_results.append(error_result)
            
            print(f"✅ 站点 {self.site_url} API测试完成: {len(self.test_results)}个测试")
            return self.test_results
            
        except Exception as e:
            print(f"❌ 站点 {self.site_url} API测试失败: {e}")
            return []

    def _build_full_url(self, api_path):
        """构建完整URL - 只构建同站点的URL"""
        try:
            if api_path.startswith(('http://', 'https://')):
                # 检查是否属于同一站点
                api_domain = urlparse(api_path).netloc
                site_domain = urlparse(self.site_url).netloc
                if api_domain == site_domain:
                    return api_path
                else:
                    print(f"⚠️ 跳过跨域API: {api_path}")
                    return None
            elif api_path.startswith('/'):
                parsed_base = urlparse(self.site_url)
                return f"{parsed_base.scheme}://{parsed_base.netloc}{api_path}"
            else:
                full_url = urljoin(self.site_url, api_path)
                parsed = urlparse(full_url)
                base_domain = urlparse(self.site_url).netloc
                if parsed.netloc == base_domain:
                    return full_url
                else:
                    print(f"⚠️ 跳过跨域API: {api_path}")
                    return None
        except Exception as e:
            print(f"构建URL失败: {e}")
            return None

    def _test_single_api(self, url, method, api_path):
        """测试单个API"""
        start_time = time.time()
        
        try:
            test_data = self._prepare_test_data(method, url)
            
            if method in ['GET', 'HEAD', 'OPTIONS']:
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    allow_redirects=True
                )
            else:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=test_data,
                    timeout=self.timeout,
                    allow_redirects=True
                )
            
            response_time = time.time() - start_time
            
            result = {
                'url': url,
                'method': method,
                'status_code': response.status_code,
                'response_time': response_time,
                'content_length': len(response.content),
                'headers': dict(response.headers),
                'title': self._extract_title(response),
                'success': response.status_code < 400
            }
            
            print(f"✅ {method} {url} - 状态: {response.status_code}, 时间: {response_time:.3f}s")
            
            return result
            
        except requests.exceptions.Timeout:
            response_time = time.time() - start_time
            return {
                'url': url,
                'method': method,
                'error': '请求超时',
                'status_code': None,
                'response_time': response_time,
                'content_length': 0,
                'title': '请求超时',
                'success': False
            }
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'url': url,
                'method': method,
                'error': str(e),
                'status_code': None,
                'response_time': response_time,
                'content_length': 0,
                'title': '测试异常',
                'success': False
            }

    def _prepare_test_data(self, method, url):
        """准备测试数据"""
        if method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            return {
                "test": True,
                "timestamp": int(time.time()),
                "data": "API Scanner Test Data"
            }
        return None

    def _extract_title(self, response):
        """从响应中提取标题"""
        try:
            content_type = response.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        return data.get('title') or data.get('name') or data.get('message') or 'JSON响应'
                    return 'JSON响应'
                except:
                    return 'JSON响应(解析失败)'
            elif 'text/html' in content_type:
                try:
                    text = response.content.decode('utf-8', errors='replace')[:1000]
                    title_match = re.search(r'<title>(.*?)</title>', text, re.IGNORECASE)
                    if title_match:
                        return title_match.group(1).strip()
                    return 'HTML页面'
                except:
                    return 'HTML页面(解码失败)'
            else:
                return f'{content_type}响应'
        except Exception:
            return '未知响应'