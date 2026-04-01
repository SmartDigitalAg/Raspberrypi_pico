import json
import sys
import urllib.request
import urllib.parse

# LCD API 설정
LCD_API_URL = "http://113.198.63.26:19320"


def send_to_lcd(line1: str, line2: str = "") -> str:
    """LCD에 텍스트 전송"""
    try:
        params = urllib.parse.urlencode({"line1": line1, "line2": line2})
        url = f"{LCD_API_URL}/send?{params}"
        with urllib.request.urlopen(url, timeout=5) as response:
            return "LCD에 표시 완료"
    except Exception as e:
        return f"오류: {e}"


def clear_lcd() -> str:
    """LCD 화면 지우기"""
    try:
        url = f"{LCD_API_URL}/clear"
        with urllib.request.urlopen(url, timeout=5) as response:
            return "LCD 화면 지움"
    except Exception as e:
        return f"오류: {e}"


def get_lcd_status() -> str:
    """LCD 현재 상태 확인"""
    try:
        url = f"{LCD_API_URL}/status"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return f"Line1: {data['line1']}\nLine2: {data['line2']}"
    except Exception as e:
        return f"오류: {e}"


# MCP 도구 정의
TOOLS = [
    {
        "name": "lcd_display",
        "description": "라즈베리파이 피코에 연결된 LCD에 텍스트를 표시합니다. 영문/숫자만 지원되며 각 줄 최대 16자입니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "line1": {
                    "type": "string",
                    "description": "첫 번째 줄에 표시할 텍스트 (최대 16자, 영문/숫자만)"
                },
                "line2": {
                    "type": "string",
                    "description": "두 번째 줄에 표시할 텍스트 (최대 16자, 영문/숫자만, 선택사항)"
                }
            },
            "required": ["line1"]
        }
    },
    {
        "name": "lcd_clear",
        "description": "LCD 화면을 지웁니다.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "lcd_status",
        "description": "LCD에 현재 표시된 텍스트를 확인합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


def handle_request(request: dict) -> dict:
    """MCP 요청 처리"""
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "lcd-server", "version": "1.0.0"}
            }
        }

    elif method == "notifications/initialized":
        return None

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS}
        }

    elif method == "tools/call":
        tool_name = request["params"]["name"]
        args = request["params"].get("arguments", {})

        if tool_name == "lcd_display":
            result = send_to_lcd(args.get("line1", ""), args.get("line2", ""))
        elif tool_name == "lcd_clear":
            result = clear_lcd()
        elif tool_name == "lcd_status":
            result = get_lcd_status()
        else:
            result = f"알 수 없는 도구: {tool_name}"

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": result}]
            }
        }

    return None


def main():
    """메인 루프 - stdin/stdout으로 MCP 통신"""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            response = handle_request(request)

            if response:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()


if __name__ == "__main__":
    main()
