import os
import shutil
import PyInstaller.__main__

# 清理之前的构建文件
if os.path.exists("dist"):
    shutil.rmtree("dist")
if os.path.exists("build"):
    shutil.rmtree("build")

# 准备参数列表
args = [
    'ui.py',
    '--name=交叉线游戏',
    '--onefile',
    '--windowed',
    '--noupx',
    '--clean',
    '--hidden-import=numpy',
    '--hidden-import=utils',
    '--hidden-import=tkinter',
    '--hidden-import=colorsys',
]

# 有条件地添加图标参数
icon = "icon.ico"
if os.path.exists(icon):
    args.append(f'--icon={icon}')

# 执行打包
PyInstaller.__main__.run(args)

print("打包完成! 可执行文件位于 'dist' 文件夹中")