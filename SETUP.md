# Bifrost Gateway — runbook для агента

Эта инструкция предназначена для Hermes-агента. Прочитай её, выполни шаги
по порядку, проверяй каждый шаг командой из блока «Проверка». Если проверка
не прошла — не переходи к следующему шагу, исправь и повтори.

**Цель:** установить пак из 5 плагинов, чтобы LLM, image gen, web search, STT
и TTS работали через единый Bifrost-ключ `sk-bf-*`.

**Предусловия:**
- Hermes Agent установлен и работает (`hermes --version`).
- Есть ключ Bifrost `sk-bf-...` (пользователь передаёт его в чате).

> **Уже установлено ранее?** Если плагины уже стоят — обнови:
> ```bash
> cd ~/hermes-plugin-bifrost-gateway && git pull && ./install.sh
> hermes config set stt.bifrost.language ru
> ```
> Затем перезапусти Hermes. Подробности — в `UPDATES.md`, запись v1.2.0.
> Проверить, установлены ли плагины: `ls ~/.hermes/plugins/*/bifrost/plugin.yaml`

---

## Шаг 1. Клонировать репозиторий

```bash
git clone https://github.com/temga/hermes-plugin-bifrost-gateway.git ~/hermes-plugin-bifrost-gateway
cd ~/hermes-plugin-bifrost-gateway
```

Если репозиторий уже склонирован — обновить:

```bash
cd ~/hermes-plugin-bifrost-gateway
git pull
```

## Шаг 2. Запустить инсталлер

Определи платформу и запусти нужный инсталлер:

**Linux / macOS / WSL:**

```bash
./install.sh
```

**Windows (PowerShell):**

```powershell
.\install.ps1
```

Инсталлер копирует 5 плагинов в `~/.hermes/plugins/` (на Windows —
`%USERPROFILE%\.hermes\plugins\`):

| Что | Куда |
|-----|------|
| `model-providers/bifrost/` | `~/.hermes/plugins/model-providers/bifrost/` |
| `image_gen/bifrost/` | `~/.hermes/plugins/image_gen/bifrost/` |
| `web/bifrost/` | `~/.hermes/plugins/web/bifrost/` |
| `transcription/bifrost/` | `~/.hermes/plugins/transcription/bifrost/` |
| `tts/bifrost/` | `~/.hermes/plugins/tts/bifrost/` |

### Если инсталлер упал

На macOS с bash 3.2 инсталлер может упасть на `declare -A`. Версия в репо
уже исправлена (plain array), но если всё равно падает — скопируй плагины
вручную:

```bash
# Linux / macOS / WSL:
mkdir -p ~/.hermes/plugins/{model-providers,image_gen,web,transcription,tts}
for d in model-providers image_gen web transcription tts; do
  cp -r "$d/bifrost" ~/.hermes/plugins/"$d/bifrost"
done
```

### Проверка

```bash
# Linux / macOS / WSL:
ls ~/.hermes/plugins/model-providers/bifrost/plugin.yaml \
   ~/.hermes/plugins/image_gen/bifrost/plugin.yaml \
   ~/.hermes/plugins/web/bifrost/plugin.yaml \
   ~/.hermes/plugins/transcription/bifrost/plugin.yaml \
   ~/.hermes/plugins/tts/bifrost/plugin.yaml
```

```powershell
# Windows (PowerShell):
Test-Path "$env:USERPROFILE\.hermes\plugins\model-providers\bifrost\plugin.yaml",
"$env:USERPROFILE\.hermes\plugins\image_gen\bifrost\plugin.yaml",
"$env:USERPROFILE\.hermes\plugins\web\bifrost\plugin.yaml",
"$env:USERPROFILE\.hermes\plugins\transcription\bifrost\plugin.yaml",
"$env:USERPROFILE\.hermes\plugins\tts\bifrost\plugin.yaml"
```

Все пять должны существовать.

## Шаг 3. Ключ

Плагины находят Bifrost-ключ автоматически в следующем порядке:

1. **`BIFROST_API_KEY`** в `.env` — каноничное имя.
2. **`providers.<name>.key_env`** в `config.yaml` — если пользователь уже
   добавил Bifrost как custom provider (через Desktop UI или `hermes config set`),
   плагины найдут ключ через его `key_env` (например
   `HERMES_CUSTOM_ROVE_API_KEY`). Условие: `base_url` провайдера содержит
   `router.rove-ai.ru`.
3. **Любой `HERMES_CUSTOM_*_API_KEY`** в `.env` со значением `sk-bf-*` —
   last-resort fallback.

### Проверь, есть ли уже ключ

Сначала проверь каноничное имя:

```bash
hermes config get BIFROST_API_KEY
```

Если вернулось непустое значение — **ключ уже есть, пропусти этот шаг**.

Если пусто — проверь, нет ли уже Bifrost как custom provider в config.yaml:

```bash
hermes config get providers
```

Или эквивалент:

```bash
python3 -c "
import os, sys
sys.path.insert(0, os.path.expanduser('~/.hermes/plugins/model-providers/bifrost'))
from _keyresolver import resolve_bifrost_key
key = resolve_bifrost_key()
print('FOUND' if key else 'NOT FOUND', 'via config/custom provider' if key else '')
"
```

Если скрипт вернул `FOUND` — **ключ уже доступен плагинам через config**,
пропусти запись. Дублировать ключ как `BIFROST_API_KEY` не нужно.

### Если ключа нет нигде

Пользователь передаёт ключ в чате. Запиши его:

```bash
hermes config set BIFROST_API_KEY <КЛЮЧ_ОТ_ПОЛЬЗОВАТЕЛЯ>
```

> Один ключ покрывает все пять сервисов. Не создавай дубликат под другим
> именем — плагины найдут его автоматически.

### Проверка

```bash
hermes config get BIFROST_API_KEY
```

Должно вернуться значение ключа — либо это значение, либо ключ уже
доступен через `providers.<name>.key_env` (проверь скриптом выше).

## Шаг 4. Включить плагины

Сначала прочитай текущий список включённых плагинов:

```bash
hermes config get plugins.enabled
```

Если список пуст или отсутствует — установи все пять путей:

```bash
hermes config set plugins.enabled '["model-providers/bifrost", "image_gen/bifrost", "web/bifrost", "transcription/bifrost", "tts/bifrost"]'
```

Если в списке уже есть другие плагины — **добавь пять bifrost-путей к
существующему массиву**, не затирая то, что уже там. Собери новый массив
вручную и запиши:

```bash
# Пример: если текущий список ["platforms/max"], то новый:
hermes config set plugins.enabled '["platforms/max", "model-providers/bifrost", "image_gen/bifrost", "web/bifrost", "transcription/bifrost", "tts/bifrost"]'
```

### Проверка

```bash
hermes config get plugins.enabled
```

В массиве должны быть все пять bifrost-путей плюс всё, что было раньше.

## Шаг 5. Активировать провайдеры

Выполни команды по очереди:

```bash
hermes config set model.provider bifrost
hermes config set model.default turbocloud/GLM-5.2

hermes config set web.search_backend bifrost
hermes config set web.extract_backend bifrost

hermes config set stt.enabled true
hermes config set stt.provider bifrost
hermes config set stt.bifrost.model neuraldeep/whisper-podlodka-turbo
hermes config set stt.bifrost.language ru

hermes config set tts.provider bifrost
hermes config set tts.bifrost.model espeech-tts
hermes config set tts.bifrost.voice alloy
hermes config set tts.bifrost.language Russian
```

### Vision-модель (важно!)

Основная chat-модель (по умолчанию `turbocloud/GLM-5.2`) — text-only.
Если её не переопределить, vision auto-detect возьмёт её для анализа
изображений и получит ошибку от upstream. Нужно явно указать
vision-модель:

```bash
hermes config set auxiliary.vision.provider bifrost
hermes config set auxiliary.vision.model neuraldeep/qwen3.8-27b
```

> Плагин `model-providers/bifrost` также объявляет `default_vision_model()`
> → `neuraldeep/qwen3.8-27b`, так что при `auxiliary.vision.provider: auto`
> vision подхватится автоматически. Но явная настройка надёжнее — не
> зависит от того, знает ли models.dev о модели.

### Image gen (может быть недоступен)

Image gen требует, чтобы в Bifrost-ключе был подключён upstream `routerai`.
Проверь доступность перед настройкой:

```bash
# Проверить, есть ли image-модели в ключе:
hermes config get BIFROST_API_KEY >/dev/null 2>&1 && \
  python3 -c "
import urllib.request, json, os
key = os.popen('hermes config get BIFROST_API_KEY').read().strip()
req = urllib.request.Request('https://router.rove-ai.ru/v1/models',
      headers={'Authorization': f'Bearer {key}'})
data = json.loads(urllib.request.urlopen(req, timeout=10).read())
models = [m['id'] for m in data.get('data', [])]
image = [m for m in models if 'image' in m.lower() or 'gpt-image' in m.lower() or 'flux' in m.lower()]
print('Image models:', image if image else 'NONE')
" 2>/dev/null || echo "Cannot check"
```

Если image-модели есть — настрой:

```bash
hermes config set image_gen.provider bifrost
hermes config set image_gen.model routerai/openai/gpt-image-2
```

Если image-моделей нет — **пропусти image gen**. Это означает, что
`routerai` upstream недоступен. Обратись к администратору Bifrost.

### Альтернативные модели

**LLM** (полный список доступных моделей можно получить командой ниже):

| Модель | Описание |
|--------|----------|
| `turbocloud/GLM-5.2` | GLM-5.2 (по умолчанию) |
| `neuraldeep/gpt-oss-120b` | GPT-OSS 120B |
| `tropass/GLM-5.2` | GLM-5.2 (tropass) |

**STT:**

| Модель | Язык |
|--------|------|
| `neuraldeep/whisper-podlodka-turbo` | RU/EN (по умолчанию) |
| `neuraldeep/whisper-1` | мультиязык |
| `neuraldeep/gigaam-v3` | только RU |

> `stt.bifrost.language: ru` критичен для русской речи. Без него Hermes
> использует глобальный дефолт `stt.language: en`, и Whisper будет
> транскрибировать с английским хинтом — русская речь распознаётся хуже.

**TTS:**

| Модель | Язык | Особенность |
|--------|------|-------------|
| `espeech-tts` | RU | Ударения, омографы (по умолчанию) |
| `qwen3-tts` | multi | 8 голосов, эмоции |

TTS голоса: `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer`, `coral`, `sage`.

## Шаг 6. Подключить скиллы из репозитория

В репозитории `hermes-plugin-bifrost-gateway` есть папка `skills/` с
готовыми скиллами (например, `bifrost-setup`). Подключи репозиторий как
источник скиллов:

```bash
hermes skills tap add temga/hermes-plugin-bifrost-gateway
```

После этого скиллы из репозитория доступны для поиска и установки:

```bash
hermes skills search bifrost
hermes skills install temga/hermes-plugin-bifrost-gateway/skills/bifrost-setup
```

### Проверка

```bash
hermes skills tap list
```

В списке должен быть `temga/hermes-plugin-bifrost-gateway`.

## Шаг 7. Перезапустить Hermes

Изменения в config.yaml и .env применяются только при новом запуске.

```bash
# Если работает gateway — перезапусти из отдельного shell (не из агента):
# hermes gateway restart

# В CLI — начни новый сеанс.
```

> Не запускай `hermes gateway restart` из терминала внутри агента —
> это убьёт текущий процесс. Либо попроси пользователя, либо используй
> новый сеанс.

## Шаг 8. Проверить работу

### 8.1. Плагины загружены

```bash
hermes plugins list
```

В списке должны быть: `bifrost-provider`, `bifrost` (image), `bifrost-web`,
`bifrost-stt`, `bifrost-tts`.

### 8.2. LLM

Отправь любой запрос в новом сеансе. Если модель отвечает — LLM работает
через Bifrost.

### 8.3. TTS

```bash
hermes chat -q "произнеси: привет, это тест"
```

Если TTS возвращает ошибку — обратись к администратору Bifrost.

### 8.4. Vision

```bash
hermes chat -q "опиши изображение: https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Cat03.jpg/240px-Cat03.jpg"
```

Если Hermes описывает изображение — vision работает через Bifrost.
Если ошибка про `image_url` или `text` variant — основная модель
text-only и vision не настроен (см. «Vision-модель» в Шаге 5).

### 8.5. Web search (только если Шаг 6 выполнен)

```bash
hermes chat -q "найди новости про SpaceX"
```

Если возвращаются результаты — web search через Bifrost MCP работает.
Если ошибка `'list' object has no attribute 'get'` — плагин устарел,
обнови: `cd ~/hermes-plugin-bifrost-gateway && git pull && ./install.sh`.
Если ошибка MCP / 0 tools — обратись к администратору Bifrost.

### 8.6. Image gen (только если настроен в Шаге 5)

```bash
hermes chat -q "сгенерируй изображение: кот в космосе"
```

### 8.7. STT (gateway)

Если к Hermes подключён мессенджер — отправь голосовое сообщение. Если
Hermes распознаёт речь — STT работает.

## Шаг 9. Настроить мониторинг обновлений

Создай cronjob, который раз в день проверяет файл `UPDATES.md` в репозитории.
Если файл изменился — агент получит diff и инструкции, что обновить в конфиге.

Используй `cronjob` tool с `monitor_url`:

```
cronjob(
    action="create",
    name="bifrost-updates",
    schedule="every 24h",
    monitor_url="https://raw.githubusercontent.com/temga/hermes-plugin-bifrost-gateway/main/UPDATES.md",
    prompt="Проверь изменения в UPDATES.md от Bifrost Gateway. Если есть новые записи — выполни инструкции из них: обнови config, переустанови плагины, сообщи пользователю что изменилось. Если изменений нет — ничего не делай.",
    deliver="origin"
)
```

> `monitor_url` хеширует содержимое файла. Пока хеш не меняется — cron
> молчит. Когда файл обновляется (новая версия плагина, изменение API,
> новая модель) — агент получает diff и выполняет инструкции из файла.

### Проверка

```bash
hermes cron list
```

В списке должен быть `bifrost-updates`.

## Откат

```bash
# Linux / macOS / WSL:
cd ~/hermes-plugin-bifrost-gateway
./install.sh --uninstall
```

```powershell
# Windows (PowerShell):
cd $env:USERPROFILE\hermes-plugin-bifrost-gateway
.\install.ps1 -Uninstall
```

Затем убери bifrost-пути из `plugins.enabled` и верни прежних провайдеров
через `hermes config set`. Перезапусти Hermes.

## Частые проблемы

### `web_search` возвращает ошибку MCP

Обратись к администратору Bifrost.

### TTS ошибка / пустой ответ

Обратись к администратору Bifrost.

### Модель не найдена / 403

Имя модели должно быть в формате `provider/model` (например
`turbocloud/GLM-5.2`). Проверь, какие модели доступны в ключе:

```bash
hermes config get BIFROST_API_KEY >/dev/null 2>&1 && \
  python3 -c "
import urllib.request, json, os
key = os.popen('hermes config get BIFROST_API_KEY').read().strip()
req = urllib.request.Request('https://router.rove-ai.ru/v1/models',
      headers={'Authorization': f'Bearer {key}'})
data = json.loads(urllib.request.urlopen(req, timeout=10).read())
for m in data.get('data', []):
    print(m['id'])
"
```

Если модели нет в списке — она недоступна для ключа.
Обратись к администратору Bifrost.

### `BIFROST_API_KEY not set` / `Bifrost key not found`

Плагины ищут ключ в трёх местах (по порядку):

1. `BIFROST_API_KEY` в `.env`
2. `providers.<name>.key_env` в `config.yaml` (custom provider с Bifrost URL)
3. Любой `HERMES_CUSTOM_*_API_KEY` со значением `sk-bf-*`

Проверь все три:

```bash
# 1. Каноничное имя
hermes config get BIFROST_API_KEY

# 2. Custom providers в config
hermes config get providers

# 3. HERMES_CUSTOM_*_API_KEY в .env
grep 'HERMES_CUSTOM.*API_KEY' ~/.hermes/.env
```

Если ключ найден в любом из них — плагины должны работать. Если нет —

```bash
hermes config set BIFROST_API_KEY <КЛЮЧ_ОТ_ПОЛЬЗОВАТЕЛЯ>
```

### Плагины не появляются в `hermes plugins list`

1. Проверь пути в `plugins.enabled` — должны быть
   `model-providers/bifrost` (а не просто `bifrost`).
2. Перезапусти Hermes (изменения apply только при новом запуске).
3. Проверь, что файлы на месте:
   ```bash
   # Linux / macOS / WSL:
   ls ~/.hermes/plugins/*/bifrost/plugin.yaml
   ```
   ```powershell
   # Windows (PowerShell):
   Get-ChildItem "$env:USERPROFILE\.hermes\plugins\*\bifrost\plugin.yaml"
   ```
