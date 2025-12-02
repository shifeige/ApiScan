"""
完整的命令行扫描器 - 协调所有组件工作
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.spider import FixedMainSpider
from core.api_tester import SiteSpecificAPITester
from utils.file_utils import save_results_to_excel, generate_output_filename
from utils.validation_utils import detect_live_sites
from core.url_normalizer import URLNormalizer

class CompleteCommandLineScanner:
    """完整版命令行扫描器 - 支持多请求方法和独立站点API测试"""
    
    def __init__(self, thread_count=10, timeout=15):
        self.thread_count = thread_count
        self.timeout = timeout
        print(f"🚀 初始化完整命令行扫描器: 线程数={thread_count}, 超时={timeout}")

    def run_scan(self, urls, output_file=None, test_methods=None, max_depth=5, max_files=0, enable_live_check=True, enable_api_test=True):
        """运行完整扫描流程 - 修改参数名避免冲突"""
        start_time = time.time()
        
        try:
            # 步骤1: 网站存活检测
            if enable_live_check:
                print("🔍 开始网站存活检测...")
                live_urls = detect_live_sites(urls)
                if not live_urls:
                    print("❌ 没有存活的网站可扫描")
                    return False
                urls = live_urls
            
            # 步骤2: 自动生成输出文件名（如果未提供）
            if not output_file:
                output_file = generate_output_filename(urls, "web_scan")
                print(f"📁 自动生成输出文件: {output_file}")
            
            # 步骤3: 修复文件爬虫
            print("🕷️ 开始修复文件爬虫...")
            spider_results = self._run_complete_spider(urls, max_depth, max_files)
            
            if not spider_results:
                print("❌ 文件爬虫未发现任何资源")
                return False
            
            # 步骤4: 独立站点API测试
            test_results = None
            if enable_api_test and test_methods:
                print("🧪 开始独立站点API测试...")
                test_results = self._run_site_specific_api_tests(urls, spider_results, test_methods)
            
            # 步骤5: 保存结果到Excel
            print("💾 保存结果到Excel文件...")
            saved_file = save_results_to_excel(spider_results, test_results, output_file)
            
            if not saved_file:
                print("❌ 保存结果文件失败")
                return False
            
            # 统计信息
            elapsed_time = time.time() - start_time
            self._print_complete_summary(spider_results, test_results, elapsed_time, saved_file)
            
            return True
            
        except Exception as e:
            print(f"❌ 扫描过程异常: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return False

    def _run_site_specific_api_tests(self, urls, spider_results, test_methods):
        """运行独立站点API测试 - 每个站点只测试自己的API"""
        all_test_results = {}
        
        # 为每个站点创建API测试器
        with ThreadPoolExecutor(max_workers=min(self.thread_count, len(urls))) as executor:
            future_to_url = {}
            
            for url in urls:
                # 获取该站点的API路径
                site_apis = self._get_site_specific_apis(url, spider_results)
                if site_apis:
                    tester = SiteSpecificAPITester(
                        site_url=url,
                        api_paths=site_apis,
                        test_methods=test_methods,
                        timeout=self.timeout,
                        max_workers=3
                    )
                    future = executor.submit(tester.test_apis)
                    future_to_url[future] = url
                else:
                    print(f"⚠️ 站点 {url} 没有发现API路径")
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    results = future.result()
                    all_test_results[url] = results
                    completed += 1
                    print(f"📊 站点API测试进度: {completed}/{len(future_to_url)} - {url}")
                except Exception as e:
                    print(f"❌ 站点 {url} API测试失败: {e}")
                    all_test_results[url] = []
        
        return all_test_results

    def _get_site_specific_apis(self, site_url, spider_results):
        """获取站点特定的API路径"""
        site_domain = URLNormalizer.get_domain(site_url)
        site_apis = set()
        
        # 从爬虫结果中提取该站点的API - 修复：使用字典访问
        all_apis = spider_results.get('api_paths', [])
        for api in all_apis:
            api_domain = URLNormalizer.get_domain(api)
            if api_domain == site_domain:
                site_apis.add(api)
        
        # 从文件内容中提取更多该站点的API
        from analyzers.api_extractor import FixedAPIExtractor
        extractor = FixedAPIExtractor()
        for file_info in spider_results.get('files', []):
            if file_info.get('type') in ['javascript', 'html', 'json']:
                content = file_info.get('content', '')
                additional_apis = extractor.extract_apis_from_content(content, file_info['url'])
                for api in additional_apis:
                    api_domain = URLNormalizer.get_domain(api)
                    if api_domain == site_domain:
                        site_apis.add(api)
        
        print(f"🎯 站点 {site_url} 发现 {len(site_apis)} 个专属API路径")
        return list(site_apis)

    def _run_complete_spider(self, urls, max_depth, max_files):
        """运行完整文件爬虫"""
        try:
            spider = FixedMainSpider(
                urls=urls,
                max_depth=max_depth,
                max_files=max_files,
                thread_count=self.thread_count
            )
            
            results = spider.start_sync()
            
            # 修复：直接检查结果字典
            if results and results.get('files'):
                print(f"✅ 完整文件爬虫完成: 发现 {len(results['files'])} 个文件, {len(results.get('api_paths', []))} 个API路径")
                return results
            else:
                print(f"⚠️ 完整文件爬虫返回空结果: {results}")
                return None
                
        except Exception as e:
            print(f"❌ 完整文件爬虫执行失败: {e}")
            import traceback
            print(f"详细错误: {traceback.format_exc()}")
            return None

    def _print_complete_summary(self, spider_results, test_results, elapsed_time, output_file):
        """打印完整扫描摘要"""
        print("\n" + "="*80)
        print("🎉 完整扫描完成摘要")
        print("="*80)
        
        file_count = len(spider_results.get('files', []))
        api_path_count = len(spider_results.get('api_paths', []))
        visited_count = spider_results.get('visited_count', 0)
        
        print(f"📁 文件发现: {file_count} 个文件")
        print(f"🎯 API路径: {api_path_count} 个路径") 
        print(f"🌐 访问页面: {visited_count} 个页面")
        
        if test_results:
            total_tests = sum(len(tests) for tests in test_results.values())
            success_tests = sum(1 for tests in test_results.values() for test in tests if test.get('success'))
            success_rate = (success_tests / total_tests) * 100 if total_tests > 0 else 0
            tested_sites = len(test_results)
            
            print(f"🧪 API测试: {total_tests} 个测试 ({tested_sites} 个站点)")
            print(f"   ✅ 成功: {success_tests}")
            print(f"   ❌ 失败: {total_tests - success_tests}")
            print(f"   📊 成功率: {success_rate:.1f}%")
            
            print(f"\n🏠 各站点测试详情:")
            for site_url, tests in test_results.items():
                site_tests = len(tests)
                site_success = sum(1 for test in tests if test.get('success'))
                site_rate = (site_success / site_tests) * 100 if site_tests > 0 else 0
                domain = URLNormalizer.get_domain(site_url)
                print(f"   {domain}: {site_tests}测试, {site_success}成功 ({site_rate:.1f}%)")
        
        print(f"\n📄 结果文件: {output_file}")
        print(f"⏱️ 总耗时: {elapsed_time:.2f} 秒")
        print("="*80)