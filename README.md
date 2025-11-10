# 欢迎使用Autonomy-AI

## **注意**:<span style="color: red;">这个程序将给予被配置的AI 完全的 不受控的 命令行操作权限，这将带来极高的安全风险，在使用之前请确保你明确的知道自己在做什么</span>

## 安装

- 安装好`python3`环境和`pip`
- 使用`pip`安装openai库 `pip3 install openai`
- 克隆项目到本地或者从release下载单独的Autonomy-AI.py

## 使用

- 进入项目目录
- 使用编辑器编辑`Autonomy-AI.py`，添加自己的`token`和`api`地址，模型名称，默认为空
- 输入`python3 Autonomy-AI.py`启动程序

## 功能

- 将AI**直接接入**linux系统命令行，它可以**直接执行**所有linux命令
- AI的权限继承自`启动AI的用户`
- AI拥有自己的长期记忆文件，它可以自行写入长期记忆并读取
- 拥有log功能，ai的操作可以在`Autonomy-AI.py`同目录下的`agent.log`查看