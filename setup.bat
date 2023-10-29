py -m build 
py -m pip uninstall straders -y
py -m pip install dist/straders-2.0.1-py3-none-any.whl --force-reinstall
explorer "C:\Users\C_tri\AppData\Local\Programs\Python\Python310\Lib\site-packages"