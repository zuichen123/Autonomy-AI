import os
import subprocess
import logging
import datetime
import time
from openai import OpenAI

# --- 配置区 ---
API_URL = ""
API_KEY = ""
MODEL_NAME = ""
LOG_FILE = "agent_log.txt"
MEMORY_FILE = "persistent_memory.txt"
INITIAL_GOAL = f"无"
API_CALLS_PER_MINUTE = 5
SHORT_TERM_MEMORY_LIMIT = 20
MAX_API_RETRIES = 3
API_RETRY_DELAY = 15
RETRY_COOLDOWN = 5

# --- 程序核心 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class AutonomousAgent:
    def __init__(self, api_url, api_key, model):
        # ... [无变化] ...
        try:
            self.client = OpenAI(api_key=api_key, base_url=api_url)
            self.client.models.list()
            logging.info("API客户端初始化成功，连接正常。")
        except Exception as e:
            logging.error(f"API客户端初始化失败: {e}")
            logging.error("请检查新的API URL和KEY是否正确，以及网络连接。")
            exit(1)
        self.model = model
        self.memory = []
        self.last_api_call_time = 0
        self.rate_limit_seconds = 60 / API_CALLS_PER_MINUTE

    def get_system_prompt(self):
        # ... [无变化] ...
        return f"""
你是一个被完全接入linux的AI。
# 操作指南:
1.  **输出**: 你的回应最好是单行的命令，换行符会被拼接成空格，导致命令出错。
2.  **禁止**: 不要输出任何解释或代码块，无人会去理解，只会导致系统报错。
3.  **终止**: 当你认为应该退出时，输出 `exit`。
4.  **打破循环**: 避免重复无效的命令。
# 特殊记忆命令:
- `readmemory`: 读取你的全部长期记忆。
- `writememory: <text to save>`: 将一行信息追加到你的长期记忆末尾。
# 当前任务描述:
{INITIAL_GOAL}
"""

    def think(self):
        # ... [速率限制和消息构建无变化] ...
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call_time
        if time_since_last_call < self.rate_limit_seconds:
            wait_duration = self.rate_limit_seconds - time_since_last_call
            logging.info(f"API速率限制：等待 {wait_duration:.2f} 秒...")
            time.sleep(wait_duration)
        
        messages = [{"role": "system", "content": self.get_system_prompt()}]
        for command, output in self.memory:
            messages.append({"role": "assistant", "content": command})
            messages.append({"role": "user", "content": f"输出:\n{output}"})
        messages.append({"role": "user", "content": "生成下一个命令。"})

        for attempt in range(MAX_API_RETRIES):
            try:
                self.last_api_call_time = time.time()
                logging.info(f"正在生成命令 (流式模式)... (尝试 {attempt + 1}/{MAX_API_RETRIES})")
                stream = self.client.chat.completions.create(
                    model=self.model, messages=messages, temperature=0.7, max_tokens=200, stream=True,
                )
                full_response = ""
                for chunk in stream:
                    # [核心修改] 增加安全检查，确保choices列表不为空
                    if chunk.choices:
                        content = chunk.choices[0].delta.content
                        if content is not None:
                            full_response += content
                
                logging.info(f"模型生成的原始文本: \"{full_response.strip()}\"")
                command = full_response.replace('\n', ' ').strip()
                if not command: return ""
                if command.startswith("`") and command.endswith("`"): command = command.strip("`")
                if command.lower().startswith("bash"): command = command[4:].lstrip()
                return command
            except Exception as e:
                logging.error(f"第 {attempt + 1} 次API调用失败: {e}")
                if attempt < MAX_API_RETRIES - 1:
                    logging.info(f"将在 {API_RETRY_DELAY} 秒后重试...")
                    time.sleep(API_RETRY_DELAY)
                else:
                    logging.error("所有API调用尝试均失败。")
                    return None
        return None

    def execute(self, command):
        # ... [无变化] ...
        clean_command = command.strip()
        if clean_command.lower().startswith('writememory:'):
            content_to_write = clean_command[len('writememory:'):].strip()
            logging.info(f"检测到特殊命令: [writememory] 内容: '{content_to_write}'")
            if not content_to_write: return "错误: writememory 命令内容为空。", "Error"
            try:
                with open(MEMORY_FILE, 'a', encoding='utf-8') as f: f.write(content_to_write + '\n')
                return "OK. 记忆已成功写入。", ""
            except Exception as e: return f"错误: 无法写入记忆文件: {e}", str(e)
        elif clean_command.lower() == 'readmemory':
            logging.info("检测到特殊命令: [readmemory]")
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f: content = f.read().strip()
                if not content: return "长期记忆为空。", ""
                return f"STDOUT:\n--- LONG TERM MEMORY ---\n{content}\n------------------------", ""
            except FileNotFoundError: return "长期记忆文件不存在。", ""
            except Exception as e: return f"错误: 无法读取记忆文件: {e}", str(e)
        else:
            logging.info(f"即将执行shell命令: [ {clean_command} ]")
            try:
                result = subprocess.run(clean_command, shell=True, capture_output=True, text=True, timeout=120)
                stdout, stderr = result.stdout.strip(), result.stderr.strip()
                output = ""
                if stdout: output += f"STDOUT:\n{stdout}\n"
                if stderr: output += f"STDERR:\n{stderr}\n"
                if not output: output = "命令已执行，但没有任何输出。"
                return output, stderr
            except Exception as e: return f"执行命令时发生未知错误: {e}", str(e)

    def run(self):
        # ... [无变化] ...
        logging.info("========= 自主AI代理 v1.0 已启动 =========")
        logging.warning("警告：代理现在拥有完全控制权，所有操作将自动执行，不经过任何审核！")
        logging.info("============================================")
        cycle_count = 1
        while True:
            logging.info(f"\n----- 第 {cycle_count} 轮 -----")
            command = self.think()
            if command is None:
                logging.warning(f"AI思考后返回了None，将在 {RETRY_COOLDOWN} 秒后重试...")
                time.sleep(RETRY_COOLDOWN)
                continue
            stripped_command = command.strip()
            if not stripped_command:
                logging.warning(f"AI思考后返回了空字符串，将在 {RETRY_COOLDOWN} 秒后重试...")
                time.sleep(RETRY_COOLDOWN)
                continue
            if stripped_command.lower() == "exit":
                logging.info("AI明确决定输出 'exit' 以终止程序。再见，主人！喵~")
                break
            output, _ = self.execute(stripped_command)
            logging.info(f"命令输出:\n---\n{output}\n---")
            self.memory.append((stripped_command, output))
            if len(self.memory) > SHORT_TERM_MEMORY_LIMIT:
                self.memory.pop(0)
            cycle_count += 1

if __name__ == "__main__":
    print("="*60)
    print("⚠️ 极度危险警告！(v1.0) ⚠️")
    print("此脚本将赋予AI完全、自主、无需确认的系统执行权限。")
    print("请清楚的认识到你在做什么，并且确定你可以为这一行为负责！")
    print("="*60)
    agent = AutonomousAgent(api_url=API_URL, api_key=API_KEY, model=MODEL_NAME)
    agent.run()
