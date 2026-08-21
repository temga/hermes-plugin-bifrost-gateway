# hermes-plugin-bifrost-gateway

Пак плагинов для Hermes Agent, который маршрутизирует все запросы (LLM, image gen, web search, STT, TTS) через единый **Bifrost AI Gateway** + NeuralDeep API. Один ключ `sk-bf-*` для всех пяти сервисов.

## Что входит

| Плагин | Тип | Endpoint | Ключ | Что даёт |
|--------|-----|----------|------|----------|
| `model-providers/bifrost` | model-provider | `/v1/chat/completions` | `BIFROST_API_KEY` | 24+ моделей (neuraldeep, tropass, turbocloud) |
| `image_gen/bifrost` | backend | `/v1/images/generations` | `BIFROST_API_KEY` | Image gen (GPT Image, Flux, Seedream) |
| `web/bifrost` | backend | `/mcp` (MCP) | `BIFROST_API_KEY` | Web search, TG search, crawl |
| `transcription/bifrost` | transcription | `/v1/audio/transcriptions` | `BIFROST_API_KEY` | STT: whisper, whisper-podlodka-turbo, gigaam-v3 |
| `tts/bifrost` | backend | `/v1/audio/speech` | `BIFROST_API_KEY` | TTS: espeech-tts (RU+ударения), qwen3-tts (8 голосов) |

> **TTS** идёт через Bifrost `/v1/audio/speech` (OpenAI-совместимый endpoint).

> **v1.1.1** (2026-08-21) — фикс контракта WebSearchProvider в `web/bifrost`.
> `search()` теперь возвращает `{"success": True, "data": {"web": [...]}}`,
> `extract()` возвращает список. Если `web_search` падал с
> `'list' object has no attribute 'get'` — обновитесь: `git pull && ./install.sh`.

## Установка

### Быстрая (инсталлер)

**Linux / macOS / WSL:**

```bash
git clone https://github.com/temga/hermes-plugin-bifrost-gateway.git
cd hermes-plugin-bifrost-gateway
./install.sh
```

**Windows (PowerShell):**

```powershell
git clone https://github.com/temga/hermes-plugin-bifrost-gateway.git
cd hermes-plugin-bifrost-gateway
.\install.ps1
```

Инсталлер раскладывает пять плагинов в `~/.hermes/plugins/`
(на Windows — `%USERPROFILE%\.hermes\plugins\`).

### Ручная (для агента)

См. [SETUP.md](SETUP.md) — пошаговая инструкция, по которой подключённый Hermes-агент может установить и настроить всё автоматически.

### Удаление

**Linux / macOS / WSL:**

```bash
./install.sh --uninstall
```

**Windows (PowerShell):**

```powershell
.\install.ps1 -Uninstall
```

## Настройка

### 1. Ключи

В `~/.hermes/.env`:

```bash
BIFROST_API_KEY=sk-bf-...          # Bifrost gateway — единый ключ на все 5 сервисов
# Опционально:
# BIFROST_BASE_URL=https://router.rove-ai.ru/v1
```

> Раньше TTS требовал отдельный `NEURALDEEP_API_KEY` — больше не нужно. TTS теперь идёт через Bifrost, используя тот же `BIFROST_API_KEY`.

### 2. Включить плагины

В `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - model-providers/bifrost       # LLM
    - image_gen/bifrost             # image gen
    - web/bifrost                   # web search
    - transcription/bifrost         # STT
    - tts/bifrost                   # TTS
```

### 3. Активировать провайдеры

```yaml
model:
  provider: bifrost
  default: turbocloud/GLM-5.2

image_gen:
  provider: bifrost
  model: routerai/openai/gpt-image-1

web:
  search_backend: bifrost
  extract_backend: bifrost

stt:
  provider: bifrost
  bifrost:
    model: neuraldeep/whisper-podlodka-turbo

tts:
  provider: bifrost
  bifrost:
    model: espeech-tts
    voice: alloy
    language: Russian
```

### 4. Перезапуск

```bash
hermes gateway restart   # если gateway
# или новый сеанс в CLI
```

## STT модели

| Модель | Язык | Описание |
|--------|------|----------|
| `neuraldeep/whisper-podlodka-turbo` | RU/EN | Whisper форк, заточенный под русский (по умолчанию) |
| `neuraldeep/whisper-1` | multi | Стандартный OpenAI Whisper |
| `neuraldeep/gigaam-v3` | RU | GigaAM v3 от Сбера |

## TTS модели

| Модель | Язык | Описание |
|--------|------|----------|
| `espeech-tts` | RU | ESpeech (F5 + RUAccent) — русский с корректными ударениями. Резолвит омографы: за́мок / замо́к. Ручное ударение: «+» перед гласной (зам+ок). По умолчанию. |
| `qwen3-tts` | multi | Qwen3-TTS (vLLM-Omni) — 8 голосов, 10 языков, эмоции. |

TTS голоса: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`, `coral`, `sage`.

## Структура

```
hermes-plugin-bifrost-gateway/
├── install.sh                          # инсталлер Linux/macOS/WSL
├── install.ps1                         # инсталлер Windows (PowerShell)
├── SETUP.md                            # пошаговая инструкция для агента
├── UPDATES.md                          # лента обновлений (мониторится cronjob)
├── skills/                             # скиллы (через hermes skills tap add)
│   └── bifrost-setup/
│       └── SKILL.md
├── model-providers/bifrost/            # LLM provider (ProviderProfile)
│   ├── plugin.yaml
│   └── __init__.py
├── image_gen/bifrost/                  # image gen backend
│   ├── plugin.yaml
│   └── __init__.py
├── web/bifrost/                        # web search backend (MCP client)
│   ├── plugin.yaml
│   ├── __init__.py
│   └── provider.py
├── transcription/bifrost/              # STT backend
│   ├── plugin.yaml
│   └── __init__.py
├── tts/bifrost/                        # TTS backend (Bifrost /v1/audio/speech)
│   ├── plugin.yaml
│   └── __init__.py
└── README.md
```
