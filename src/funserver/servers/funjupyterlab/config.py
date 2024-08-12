# lsof -i tcp:8765
# kill -9 58055
# jupyter-labextension update --all

c = get_config()
c.FileContentsManager.root_dir = "./"
c.InteractiveShell.ast_node_interactivity = "all"
# 每次
c.InteractiveShellApp.exec_lines = [
    "import pandas as pd",
    "import numpy as np",
    "import matplotlib.pyplot as plt",
]

c.IPKernelApp.matplotlib = "inline"
c.NotebookApp.enable_mathjax = True

# “*”代表非本机都可以访问
c.LabApp.ip = "*"
# c.ServerApp.ip = False

# c.ConnectionFileMixin.ip = '172.19.36.38'
c.LabApp.ip = "0.0.0.0"
# c.ServerApp.ip = '0.0.0.0'

# 修改为在启动notebook的时候不启动浏览器
c.LabApp.open_browser = True
# c.ServerApp.open_browser = True

# 指定notebook的服务端口号
c.LabApp.port = 8765
# c.ServerApp.port = 8765

# c.NotebookApp.contents_manager_class = 'notedown.NotedownContentsManager'
# 指定notebook服务的目录（缺省为运行jupyter命令时用户所在的目录，注意此目录不能为隐藏目录）

# 设定password，不如上面介绍的命令行方便，需要用程序生成密码的hash值黏贴于此处
# c.NotebookApp.password = u'123456'
# c.NotebookApp.password = u'sha1:fff5261476d4:425ef465b8ab0172ef0e9c723ff3f5661c0a261f'
