# MCP LCD Server

Claude에서 라즈베리파이 피코 LCD를 제어하는 MCP 서버

## 구조

```
라즈베리파이 피코 (LCD) <--WiFi--> 공유기 <--인터넷--> MCP 서버 <---> Claude
```

## 요구사항

- Python 3.x
- 라즈베리파이 피코 W (WiFi 지원)
- I2C LCD (16x2)
- 피코에서 `lcd_web.py` 실행 중

## 설정

### 1. API 주소 확인

`server.py`에서 LCD API 주소 설정:

```python
LCD_API_URL = "http://공인IP:포트번호"
```

### 2. Claude Desktop 설정

`%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lcd": {
      "command": "python",
      "args": ["C:\\code\\Raspberrypi_pico\\mcp_lcd_server\\server.py"]
    }
  }
}
```

### 3. Claude Code 설정

프로젝트 폴더에 `.mcp.json` 생성:

```json
{
  "mcpServers": {
    "lcd": {
      "command": "python",
      "args": ["C:\\code\\Raspberrypi_pico\\mcp_lcd_server\\server.py"]
    }
  }
}
```

또는 CLI에서:

```bash
claude mcp add lcd python "C:\code\Raspberrypi_pico\mcp_lcd_server\server.py"
```

## 사용 가능한 도구

| 도구 | 설명 |
|------|------|
| `lcd_display` | LCD에 텍스트 표시 (line1, line2) |
| `lcd_clear` | LCD 화면 지우기 |
| `lcd_status` | 현재 LCD 표시 내용 확인 |

## 사용 예시

Claude에게 이렇게 말하면 됩니다:

- "LCD에 Hello World 표시해줘"
- "LCD 첫 번째 줄에 Temperature, 두 번째 줄에 25.5C 표시해"
- "LCD 화면 지워줘"
- "LCD에 뭐라고 써있어?"

## 제한사항

- 영문/숫자/특수문자만 지원 (한글 불가 - LCD 하드웨어 한계)
- 각 줄 최대 16자

## API 직접 호출

```bash
# 텍스트 표시
curl "http://공인IP:포트/send?line1=Hello&line2=World"

# 화면 지우기
curl "http://공인IP:포트/clear"

# 상태 확인
curl "http://공인IP:포트/status"
```
