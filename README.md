# hermes-plugin-bifrost-gateway

Пак плагинов для Hermes Agent, который маршрутизирует все запросы (LLM, image gen, web search) через единый **Bifrost AI Gateway**. Один ключ `sk-bf-*` — всё работает.

## Что входит

| Плагин | Тип | Endpoint | Что даёт |
|--------|-----|----------|----------|
| `bifrost-provider` | model-provider | `/v1/chat/completions` | 24+ моделей (neuraldeep, tropass, turbocloud) через один ключ |
| `bifrost` (image) | backend | `/v1/images/generations` | Image gen (GPT Image, Flux, Seedream) через gateway |
| `bifrost-web` | backend | `/mcp` (MCP protocol) | Web search, TG search, crawl через NeuralDeep |

## Зачем

Без этого пака: 3+ разных API-ключа (routerai, neuraldeep, …), 3 точки отказа, никакой централизации.

С этим паком: один `sk-bf-*` ключ Bifrost → LLM + картинки + поиск. Лимиты, бюджет, логирование — всё в Bifrost.

## Установка

```bash
# Клонировать и запустить install-скрипт
git clone https://github.com/temga/hermes-plugin-bifrost-gateway.git
cd hermes-plugin-bifrost-gateway
./install.sh
```

Или вручную: скопировать каталоги `model-providers/bifrost`, `image_gen/bifrost`, `web/bifrost` в `~/.hermes/plugins/`.

## Настройка

### 1. Ключ

В `~/.hermes/.env`:

```bash
BIFROST_API_KEY=sk-bf-...
# Опционально (default: http://127.0.0.1:8082/v1):
# BIFROST_BASE_URL=https://router.rove-ai.ru/v1
```

### 2. Включить плагины

В `~/.hermes/config.yaml`:

```yaml
plugins:
  enabled:
    - bifrost-provider    # LLM
    - bifrost             # image gen
    - bifrost-web         # web search
```

### 3. Активировать провайдеры

```yaml
# LLM — выбрать через hermes model или в config:
model:
  provider: bifrost
  default: neuraldeep/gpt-oss-120b

# Image gen:
image_gen:
  provider: bifrost
  model: openai/gpt-image-1

# Web search:
web:
  search_backend: bifrost
  extract_backend: bifrost
```

### 4. Перезапуск

```bash
hermes gateway restart   # если gateway
# или новый сеанс в CLI
```

## Проверка

```bash
hermes plugins list       # все три должны быть enabled
hermes model              # bifrost должен появиться в списке
```

## Bifrost MCP (web search)

Web search идёт через Bifrost `/mcp` endpoint (MCP Streamable HTTP). Для работы:

1. В Bifrost UI: Virtual Keys → ваш ключ → MCP Client Configurations → добавить `neuraldeep-search` с **Allow All Tools**.
2. MCP клиент `neuraldeep-search` должен быть активен (Bifrost UI → MCP).

Без привязки MCP tools к virtual key, web search вернёт пустые результаты.

## Удаление

```bash
./install.sh --uninstall
```

## Структура

```
hermes-plugin-bifrost-gateway/
├── install.sh                          # инсталлер (раскладывает 3 плагина)
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
└── README.md
```
