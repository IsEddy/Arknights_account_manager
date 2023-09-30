

<div align="center">
<img alt="LOGO" src="https://raw.githubusercontent.com/IsEddy/Arknights_account_manager/master/skadi.ico" width="256" height="256" />

# ArknightsAccountManager

</div>

-----------------------------------

- 本程序适用于有多个```官服```账号而且完全不想管的人
- 本程序有着许多QianZaiDe迷之bug
- 本程序（目前）需要你一直开着模拟器

# 使用指南
## 脚本设置：
把```程序文件夹```以及```adb文件夹```解压到maa.exe所在的文件夹，你解压完的文件夹应该长这样：
```shell
maa文件夹
├───maa.exe
├───adb
├───change_account
│   ├───asst
│   ├───recognition_dataset
│   ├───change_account.exe
│   ├───......(剩下的文件)
├───MaaCore.dll
├───MaaDerpLearning.dll
├───MaaIsOff.bat
├───MaaIsOn.bat
├───onnxruntime_maa.dll
└───opencv_world4_maa.dll
```

如果可以正常打开的话，那就没有问题啦！

接下来就是填写你所有的账号密码，以及你希望它启动的时间！（需要注意的是，脚本在切换账号时将会强制结束MAA，所以请预留好足够的任务时间）

-----------------------------------
##  MAA设置：
- 1. 将MAA的开始前脚本框填上MaaIsOn.bat
- 2. MAA的结束后脚本框填上MaaIsOff.bat
- 3. 若是多个账号都使用同一个maa配置：只需再maa中添加“main”配置，并勾选maa的“启动后自动开始任务”选项
- 若是有账号使用特殊的maa配置：再maa中添加账号相对应的配置，举例：账号1需要使用自定义配置，则在maa中添加名为“account1”的配置，账号2就是“account2”，以此类推。
	
## 注意!!!!!仍旧需要勾选maa的“启动后自动开始任务”选项!!!!! 程序会自动检测已经存在的配置并启动，若是该账号不再使用自定义配置，只需删除对应的配置即可。

-----------------------------------
## ！！！！！重要注意！！！！！
- 别设置3：59这种阴间时间，以及15：59也不要，防止数据更新！！！

- 尽量给你的号留出距离4：00或是16：00  40min的任务时长（看你的情况而定）

- 以及，目前程序默认一个号会打两次，一次是你设置的时间，一次是12小时后的时间，以后会有选择的！！（这就是为什么我叫你别设置15：59）

- 延迟时间看你的电脑，感觉性能差的就填大一点，一般是1-5，好电脑可以填0.5-1。可以是整数或者小数。(你填不了114514的)

-----------------------------------
# 致谢
- 森空岛签到 By xxyz30 https://github.com/xxyz30/skyland-auto-sign (MIT Licence)

-----------------------------------
# 更新日志：
## v0.14 :
- 增加“一键清全部日常”选项
- 增加在最早启动时前唤醒电脑的功能

## v0.13 :
- 修复多线程无法调起肉鸽的bug
- （再次）规范了日志格式
- 将GUI界面的错误输出设置为红色

## v0.12 :
- 添加了多线程，现在切换账号时脚本不会卡住了
- 修复了重启游戏时有几率启动失败的问题

## v0.11 :
- 更改进程结束逻辑，现在不需要管理员启动也可以正常结束进程了。（但是还是要管理员启动来调起maa）
- 找到了让maa启动后有几率卡在 “连接模拟器” 任务的东西！！！并修复了这个问题

## v0.10 :
- 规范了日志格式，但不多。
- 优化保存机制及账号开关机制，现在点击开关账号会直接重启计时器啦！
- 增加自动检测maa中账号对应的配置功能，支持自定义配置启动，详情见说明
- 增加任务结束后自动重启maa和adb功能，最大限度上减少错误的发生。
- 修了一些bug。

## v0.09 :
- 增加json键检测功能防止莫名其妙的问题(
- 重构图像识别逻辑，增加自定义图像识别功能。
- 在日志中增加了日期，这样会好看一点（bushi）

## v0.08 :
- 增加了账号的开关。由于增加了文件参数，所以需要手动删除原本change_account文件夹内的info.txt（v0.009 现在不需要了）。

## v0.07 :
- 优化了命令执行策略，现在他不会弹黑窗了。
- 更改了图像文件夹的命名。

## v0.06 :
- 更换了一种打包方式，现在你删除账号他自己会重启了。