

<div align="center">
<img alt="LOGO" src="https://raw.githubusercontent.com/IsEddy/Arknights_account_manager/master/skadi.ico" width="256" height="256" />

# ArknightsAccountManager

</div>

-----------------------------------

- 本程序适用于有多个```官服```账号而且完全不想管的人（因为b服懒得做）
- 本程序有着许多~~潜在的~~迷之bug
- 本程序```（目前）```需要你一直开着模拟器

## 本程序完全离线运行，所有信息保存在本地！！ 

# 使用指南
## 脚本设置：
把```程序文件夹```以及```adb文件夹```解压到maa.exe所在的文件夹，你解压完的文件夹应该长这样：
```shell
maa文件夹
├───maa.exe
├───adb
├───change_account
│   ├───_internal
│   │   ├───asst
│   │   └───......(剩下的文件)
│   ├───recognition_dataset
│   ├───change_account.exe
│   ├───skadi.ico
├───MaaCore.dll
├───MaaDerpLearning.dll
├───MaaIsOff.bat
├───MaaIsOn.bat
├───onnxruntime_maa.dll
├───opencv_world4_maa.dll
└───......(剩下的文件)

```

如果可以正常打开的话，那就没有问题啦！

接下来就是填写你所有的账号密码，以及你希望它启动的时间！（需要注意的是，脚本在切换账号时将会强制结束MAA，所以请预留好足够的任务时间）

### 如果不能的话，提issue的时候记得附上change_account文件夹里边的debug文件夹

-----------------------------------
##  MAA设置：
- 1. 将MAA的开始前脚本框填上MaaIsOn.bat
- 2. MAA的结束后脚本框填上MaaIsOff.bat
- 3. 若是多个账号都使用同一个maa配置：只需再maa中添加“main”配置，并勾选maa的“启动后自动开始任务”选项
  - 若是有账号使用特殊的maa配置：再maa中添加账号相对应的配置，举例：账号1需要使用自定义配置，则在maa中添加名为“account1”的配置，账号2就是“account2”，以此类推。
	
### 注意!!!!!仍旧需要勾选maa的“启动后自动开始任务”选项!!!!! 程序会自动检测已经存在的配置并启动，若是该账号不再使用自定义配置，只需删除对应的配置即可。

-----------------------------------
##  图像识别与动作：
脚本的图像识别基于将模拟器的截图与```recognition_dataset```文件夹内的图片进行对比，找到匹配的图片即执行相应动作。您也可以依照一下的格式修改```recognition_dataset```文件夹内的```recg.json```来自定义动作。
### 格式如下：
```shell
...
  },
{
    "image": "xxx.png",  # 填写程序识别的图片文件名，如 main.png
    "threshold": "0.8",  # 填写识别阈值，越高代表越精确匹配，程序越不容易识别出错，
    #但也有可能无法匹配导致识别不到，越低代表越模糊匹配，但也有可能误判，一般为0.8-0.9
    "taps": "960,800"  # 填写需要做的动作，若是要点击，则格式为    x坐标,y坐标
    # 此外，还支持 open_game(启动明日方舟)，exit(开始输入账号密码) 这两个动作
    # 每个动作之间用“  ;  ”英文分号隔开填写在双引号中，如"1,5;114,514;exit"，支持理论上无限个动作
    # 但是exit动作后会进入输入账号密码的步骤，不再接受任何动作
  },
{
```

## 文件里里所有标点符号都是英文！！！

-----------------------------------
## ！！！！！重要注意！！！！！
- 别设置3：59这种阴间时间，以及15：59也不要，防止数据更新！！！

- 尽量给你的号留出距离4：00或是16：00  40min的任务时长（看你的情况而定）

- 以及，目前程序默认一个号会打两次，一次是你设置的时间，一次是12小时后的时间，以后会有选择的！！（这就是为什么我叫你别设置15：59）

- 延迟时间看你的电脑，感觉性能差的就填大一点，一般是1-5，好电脑可以填0.5-1。可以是整数或者小数。(你填不了114514的)

-----------------------------------
# 致谢
- MAA https://github.com/MaaAssistantArknights/MaaAssistantArknights
- 森空岛签到 By xxyz30 https://github.com/xxyz30/skyland-auto-sign (MIT Licence)
- Logo By QuAn_ https://www.pixiv.net/users/6657532

-----------------------------------
# 更新日志：
## v0.17 :
- 新增对萨卡兹肉鸽的支持
- 自动唤醒还是没搞定


## v0.16 :
- 修复mumu模拟器端口获取问题
- 修复各种闪退问题
- 自动唤醒还是没搞定

## v0.15 :
- 信息储存大改，过去使用过的需要重新填写账号密码（sorry）
- 增加在最早启动时前唤醒电脑的功能（需要输入电脑登陆密码），~~现在你可以放心的让电脑睡眠啦！~~（划掉，这条还未实现）

## v0.14 :
- 增加“一键清全部日常”选项

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
- 增加了账号的开关。由于增加了文件参数，所以需要手动删除原本change_account文件夹内的info.txt（v0.09 不需要了）。

## v0.07 :
- 优化了命令执行策略，现在他不会弹黑窗了。
- 更改了图像文件夹的命名。

## v0.06 :
- 更换了一种打包方式，现在你删除账号他自己会重启了。