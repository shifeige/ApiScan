Web Scanner - 网站文件爬虫和API扫描器
一个功能强大的网站文件爬虫和API扫描工具，专为安全测试和漏洞挖掘设计。

✨ 功能特性
🔍 深度文件爬取：自动发现网站静态资源（JS、CSS、HTML等）

🎯 智能API提取：从JavaScript和HTML中提取API端点

🧪 多方法API测试：支持GET、POST、PUT、DELETE等方法测试

🔒 SSL/TLS处理：自动处理SSL证书错误和TLS版本问题

📊 智能结果保存：自动生成Excel报告，按域名命名

⚡ 高性能并发：多线程并行爬取和测试

🛠️ 模块化架构：易于维护和扩展的代码结构


🚀 快速开始
安装依赖
bash
pip install requests beautifulsoup4 chardet pandas openpyxl
基本使用
扫描单个网站：

python main.py -u https://example.com
从文件读取URL列表：

python main.py -f urls.txt
高级选项

# 跳过SSL验证（针对有证书问题的网站）
python main.py -u https://example.com --no-ssl-verify

# 设置爬虫深度和线程数
python main.py -u https://example.com -d 3 -t 20

# 指定API测试方法
python main.py -u https://example.com --methods GET POST

# 跳过API测试，只进行文件爬取
python main.py -u https://example.com --no-api-test

# 跳过存活检测
python main.py -u https://example.com --no-live-check
⚙️ 命令行参数
输入选项
-u, --url：单个URL扫描

-f, --file：包含URL列表的文件

扫描选项
-d, --depth：爬虫深度（默认：5）

-m, --max-files：最大文件数（0表示无限制，默认：0）

-t, --threads：线程数（默认：10）

--timeout：请求超时时间（默认：15秒）

--no-live-check：跳过网站存活检测

API测试选项
--methods：API测试方法（默认：GET POST PUT DELETE）

--no-api-test：跳过API测试

SSL/TLS选项
--no-ssl-verify：跳过SSL证书验证

输出选项
-o, --output：输出Excel文件（可选，不提供则自动生成）

📊 输出文件
程序会自动生成Excel报告，包含以下工作表：

文件发现：爬取到的所有文件信息

API发现：提取到的所有API路径

API测试：API测试结果详情

扫描摘要：扫描统计信息

文件名格式：

单站点：域名_时间戳.xlsx（如：example.com_20231201_143022.xlsx）

多站点：multi_sites_scan_时间戳.xlsx

🎯 核心功能详解
1. 文件爬取
自动发现HTML中的资源链接

深度分析JavaScript文件

识别Webpack等现代前端框架的哈希文件名

支持常见静态资源路径生成

2. API提取
从HTML、JavaScript中提取API端点

支持多种API模式识别：

RESTful API（/api/v1/, /rest/）

GraphQL端点

AJAX请求

WebSocket连接

配置文件中的API

3. API测试
多请求方法测试（GET、POST、PUT、DELETE等）

自动生成测试数据

每个站点独立测试，避免跨域问题

详细的响应信息记录

4. 错误处理
SSL/TLS错误自动处理

连接超时重试机制

非法字符自动清理

详细的错误日志记录
