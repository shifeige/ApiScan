"""
内容分析器 - 负责协调各种分析器的工作
"""

from analyzers.html_analyzer import HTMLAnalyzer
from analyzers.js_analyzer import JavaScriptAnalyzer
from analyzers.api_extractor import FixedAPIExtractor

class ContentAnalyzer:
    """内容分析器 - 协调各种分析组件"""
    
    def __init__(self):
        self.html_analyzer = HTMLAnalyzer()
        self.js_analyzer = JavaScriptAnalyzer()
        self.api_extractor = FixedAPIExtractor()
    
    def analyze_content(self, content, content_type, base_url):
        """根据内容类型分析内容"""
        resources = set()
        apis = set()
        
        try:
            # HTML内容分析
            if content_type == 'html':
                html_resources = self.html_analyzer.extract_resources_from_html(content, base_url)
                resources.update(html_resources)
                
            # JavaScript内容分析
            elif content_type == 'javascript':
                js_resources = self.js_analyzer.analyze_javascript(content, base_url)
                resources.update(js_resources)
            
            # 所有内容类型都提取API
            content_apis = self.api_extractor.extract_apis_from_content(content, base_url)
            apis.update(content_apis)
            
        except Exception as e:
            print(f"内容分析失败: {e}")
        
        return resources, apis