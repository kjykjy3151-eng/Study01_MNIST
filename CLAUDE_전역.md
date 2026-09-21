<!-- 작성일: 2026-09-21 17:36 (KST) -->

# CLAUDE.md (전역)

> **이 파일은 사본입니다.** 원본은 이 저장소가 아니라 작업자 PC의
> `~/.claude/CLAUDE.md`(윈도우: `%USERPROFILE%\.claude\CLAUDE.md`)에 있습니다.
>
> Claude Code 가 자동으로 읽는 파일은 `CLAUDE.md`, `CLAUDE.local.md`,
> `.claude/CLAUDE.md`, `AGENTS.md` 뿐이므로 **이 파일은 자동으로 적용되지 않습니다.**
> 전역 설정에 어떤 규칙이 들어 있는지 저장소에서도 확인할 수 있도록 둔 것입니다.
>
> 이 프로젝트에만 적용되는 규칙은 [`CLAUDE.md`](CLAUDE.md) 에 있습니다.
> 전역 설정을 바꾸면 이 사본도 함께 갱신해야 내용이 어긋나지 않습니다.

모든 프로젝트에 적용되는 개인 설정입니다.

## 파일 작성 규칙

새로 만드는 모든 파일은 맨 위에 작성 일시를 주석으로 남긴다.
파이썬처럼 모듈 독스트링이 있는 경우에는 독스트링 바로 아래에 적는다.

형식은 `작성일: YYYY-MM-DD HH:MM (KST)` 이며, 언어별 주석 기호를 쓴다.

```python
# 작성일: 2026-09-21 17:32 (KST)
```

```powershell
# 작성일: 2026-09-21 17:32 (KST)
```

```
rem 작성일: 2026-09-21 17:32 (KST)
```

```markdown
<!-- 작성일: 2026-09-21 17:32 (KST) -->
```

### 시각은 반드시 대한민국 표준시(KST, UTC+9)로 적는다

날짜와 시각은 추측하지 말고 실제로 조회한다. 시스템 프롬프트가 알려 주는
날짜에는 시각이 없기 때문이다.

**`TZ=Asia/Seoul date` 는 쓰지 않는다.** 윈도우의 Git Bash 에는 시간대
데이터베이스가 없어서 이 방식이 조용히 UTC 로 떨어진다. 그러면 실제보다
9시간 이른 시각이 적히는데, 오류가 나지 않으므로 알아차리기 어렵다.

대신 시스템 시간대와 무관하게 동작하는 아래 방법을 쓴다.

```bash
date -u -d "+9 hours" "+%Y-%m-%d %H:%M"
```

```powershell
[System.TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTime]::UtcNow,'Korea Standard Time').ToString('yyyy-MM-dd HH:mm')
```

```bash
python -c "from datetime import datetime,timezone,timedelta; print(datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M'))"
```

한국은 서머타임을 쓰지 않으므로 UTC+9 고정 오프셋이 언제나 정확하다.

### 적용 범위

이 규칙은 **새로 만드는 파일에만** 적용한다. 기존 파일을 수정할 때는
작성일 주석을 새로 붙이지 않으며, 요청이 없는 한 소급 적용하지 않는다.
