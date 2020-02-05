“文泉学堂”PDF下载
====================

[文泉学堂](https://lib-nuanxin.wqxuetang.com/)

1. 安装 requirements.txt 里的依赖
2. 找到你要的书，看地址栏的数字为 id
3. 运行 `python3 crawl_wqxt.py <id>`

服务器生成图片需要时间，可能出现 not loaded，会稍候重试。若一直出现 not loaded（第二遍还是），请尝试重新运行，已下载的图片不会重新下载。

若需要清理缓存，请删除 wqxt.db 或自行更改其内容（SQLite 数据库）。

请自行在 `crawl_wqxt.py` 的59行里加自己注册的账号和密码。

已知存在bug：批量下载书籍可能会出错终止，可能是某些书籍的处理出错导致的。

请合理使用服务器资源。版权问题概不负责。
