# MasterDuel_TextTrans
MasterDuel汉化翻译工具，通过识别卡名比对数据库实现，不读取内存不识别卡图，在安全和性能上具有优势。

主要特点：
1.	支持英文卡名，便于日文界面用不习惯的朋友们。使用日语界面的可使用其他大佬的工具；
2.	自动识别场景，不需要额外操作即可同时识别卡组界面和决斗界面的卡牌信息；
3.	提供源码和打包完成的exe文件，方便大家使用。

使用方法：
需要识别的卡片显示在左侧之后，点击鼠标中键即可识别。
使用源码的朋友请安装完依赖（推荐用conda安装）以后，运行main.py
使用exe文件的朋友直接打开文件夹中main.exe即可

bug修复和功能增加：
1. 修复闪刀系列卡识别时将“-”识别为“—”的bug
2. 修复卡名中带有单引号或者双引号时识别错误的bug
3. 增加识别失败后缩短卡名重新查询的功能
另外请大家注意！本工具只适用英文的卡名！
