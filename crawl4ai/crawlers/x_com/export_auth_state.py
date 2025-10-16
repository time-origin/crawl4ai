
import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

# [CHG] Save the auth file next to the script itself.
SCRIPT_DIR = Path(__file__).parent
AUTH_STATE_PATH = SCRIPT_DIR / "auth_state.json"
CDP_URL = "http://localhost:9222"

async def main():
    print("="*60)
    print("X.com 认证文件导出工具")
    print("="*60)
    print("本工具将连接到您手动打开的 Chrome 浏览器并导出登录状态。")
    print("\n在运行本脚本前，请务必完成以下【手动操作】:")
    print("1. 【重要】彻底关闭所有正在运行的 Chrome 浏览器窗口。")
    print("2. 打开 Windows 命令提示符 (CMD)。")
    print("3. 运行命令: \"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe\" --remote-debugging-port=9222 --user-data-dir=\"C:\\temp\"")
    print("4. 在新打开的浏览器中，手动登录 X.com。")
    print("5. 【登录成功后】，保持浏览器和 CMD 窗口都不要关闭。")
    print("6. 回到这里，按回车键继续执行导出操作...")
    input() # Wait for user confirmation

    try:
        async with async_playwright() as p:
            print(f"\n正在连接到 {CDP_URL} ...")
            browser = await p.chromium.connect_over_cdp(CDP_URL)
            print("✅ 连接成功!")

            context = browser.contexts[0]

            print(f"\n正在导出认证状态...")
            await context.storage_state(path=AUTH_STATE_PATH)
            # [CHG] Print the full, absolute path to the file.
            print(f"✅ 成功! 认证文件已保存为: '{AUTH_STATE_PATH.resolve()}'")
            print("\n操作完成，您现在可以关闭所有相关的浏览器和命令行窗口了。")

    except Exception:
        print("\n❌ 导出失败! 无法连接到浏览器。")
        print("请重新检查并严格按照上述手动步骤操作，然后再次运行本脚本。")

if __name__ == "__main__":
    asyncio.run(main())
