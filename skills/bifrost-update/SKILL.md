---
name: bifrost-update
description: "Update Bifrost Gateway plugins to latest version. Run when user asks to update Bifrost."
version: 1.0.0
author: temga
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [bifrost, update, upgrade, maintenance]
    category: devops
---

# Bifrost Update Skill

Обновляет пак Bifrost Gateway плагинов до последней версии из репозитория
`temga/hermes-plugin-bifrost-gateway`. Запускать когда пользователь просит
обновить/апгрейднуть Bifrost плагины.

## When to Use

Пользователь просит: «обнови bifrost», «апгрейдни bifrost плагины»,
«проверь обновления bifrost».

## Prerequisites

- Плагины уже установлены (`~/.hermes/plugins/*/bifrost/plugin.yaml`).
- Репозиторий клонирован в `~/hermes-plugin-bifrost-gateway` (или
  `~/workspace/hermes-plugin-bifrost-gateway`).

## Procedure

### 1. Найти репозиторий

```bash
# Проверить стандартные пути
ls ~/hermes-plugin-bifrost-gateway/.git 2>/dev/null \
   ~/workspace/hermes-plugin-bifrost-gateway/.git 2>/dev/null
```

Если не найден — клонировать:
```bash
git clone https://github.com/temga/hermes-plugin-bifrost-gateway.git ~/hermes-plugin-bifrost-gateway
```

### 2. Обновить репозиторий и переустановить плагины

```bash
cd ~/hermes-plugin-bifrost-gateway  # или найденный путь
git pull
./install.sh          # Linux/macOS/WSL
.\install.ps1         # Windows (PowerShell)
```

Если `install.sh` падает на macOS (bash 3.2) — скопировать вручную:
```bash
mkdir -p ~/.hermes/plugins/{model-providers,image_gen,web,transcription,tts}
for d in model-providers image_gen web transcription tts; do
  cp -r "$d/bifrost" ~/.hermes/plugins/"$d/bifrost"
  cp _keyresolver.py ~/.hermes/plugins/"$d/bifrost/_keyresolver.py"
done
```

### 3. Проверить и применить изменения из UPDATES.md

Прочитать `UPDATES.md` в репозитории — там инструкции для каждой версии.
Выполнить действия из всех записей новее текущей установленной версии.

Ключевые проверки (на случай если что-то не настроено):

```bash
# STT language — должен быть ru для русской речи
hermes config get stt.bifrost.language
# Если пусто:
hermes config set stt.bifrost.language ru

# Vision модель
hermes config get auxiliary.vision.model
# Если пусто:
hermes config set auxiliary.vision.provider bifrost
hermes config set auxiliary.vision.model neuraldeep/qwen3.8-27b
```

### 4. Проверить ключ

```bash
# Плагины находят ключ автоматически через _keyresolver.
# Проверить, что ключ доступен:
python3 -c "
import sys; sys.path.insert(0, '$HOME/.hermes/plugins/model-providers/bifrost')
from _keyresolver import resolve_bifrost_key
k = resolve_bifrost_key()
print('Key found' if k else 'KEY NOT FOUND')
"
```

Если ключ не найден — см. SETUP.md Шаг 3.

### 5. Перезапустить Hermes

Изменения в плагинах применяются только при новом запуске. Попроси
пользователя перезапустить Hermes, либо начни новый сеанс.

## Verification

```bash
# Плагины на месте
ls ~/.hermes/plugins/*/bifrost/_keyresolver.py

# Версия — проверить что git pull прошёл
cd ~/hermes-plugin-bifrost-gateway && git log --oneline -1
```

## Pitfalls

- **Не запускай `hermes gateway restart` из терминала внутри агента** —
  это убьёт текущий процесс.
- **`install.sh` на macOS bash 3.2** — может падать на `declare -A`,
  хотя текущая версия исправлена. Fallback — ручное копирование.
- **Дубликат ключа** — если в `.env` есть и `BIFROST_API_KEY` и
  `HERMES_CUSTOM_*_API_KEY` с одинаковым `sk-bf-*` значением, можно
  удалить `BIFROST_API_KEY` — плагины найдут ключ через config.
