# Bifrost Gateway — Updates

Этот файл — лента обновлений пак плагинов. Cronjob читает его и
уведомляет, когда нужно что-то изменить в конфиге Hermes.

Формат: каждая запись — блок с датой в начале. Cronjob сравнивает
хеш содержимого — если файл изменился, агент получает diff и
инструкцию что делать.

---

## 2026-08-21 — v1.1.0

### Vision-модель

Добавлен `default_vision_model()` в ProviderProfile → `neuraldeep/qwen3.8-27b`.
Если `auxiliary.vision.model` не задан явно, vision auto-detect теперь
работает корректно (раньше брал text-only chat-модель).

**Действие:** проверить, что vision настроен:
```bash
hermes config get auxiliary.vision.model
```
Если пусто — задать:
```bash
hermes config set auxiliary.vision.model neuraldeep/qwen3.8-27b
```

### TTS через Bifrost

TTS теперь идёт через Bifrost (`tts/bifrost`), а не напрямую в NeuralDeep.
`NEURALDEEP_API_KEY` больше не нужен — всё через `BIFROST_API_KEY`.

**Действие:** если в config.yaml ещё `tts.provider: neuraldeep` — переключить:
```bash
hermes config set tts.provider bifrost
hermes config set tts.bifrost.model espeech-tts
```

### install.sh фикс

Путь TTS-плагина исправлен: `tts/neuraldeep` → `tts/bifrost`. Если
инсталлер падал на TTS — обновиться: `git pull && ./install.sh`.

### Windows installer

Добавлен `install.ps1` — PowerShell-версия для Windows.

### Skills tap

Добавлена папка `skills/` и шаг 7 в SETUP.md:
```bash
hermes skills tap add temga/hermes-plugin-bifrost-gateway
```

---

## 2026-08-21 — v1.1.1

### Web search: фикс контракта WebSearchProvider

Плагин `web/bifrost` возвращал данные в неправильном формате:
- `search()` отдавал `List[Dict]` вместо `{"success": True, "data": {"web": [...]}}`
- `extract()` отдавал `Dict[str, Dict]` (по URL как ключу) вместо `List[Dict]`
- Не было `supports_extract()` → Hermes не вызывал extract вообще

Симптом: `web_search` падал с `'list' object has no attribute 'get'`.

**Действие:** обновить плагин:
```bash
cd ~/.hermes/plugins/web/bifrost
git pull   # если клонировали из репо
# или переустановить:
cd ~/workspace/hermes-plugin-bifrost-gateway && git pull && ./install.sh
```

Параметр `num_results` переименован в `limit` (так Hermes передаёт).
Добавлены `supports_search()` и `supports_extract()` → True.
Добавлено поле `position` в результаты поиска.

### NeuralDeep MCP server: совместимость с mcp 2.0

Скрипт `bifrost/mcp-servers/neuraldeep_search.py` (на стороне сервера Bifrost)
переписан под mcp 2.0 API — старый декоратор `@server.list_tools()` больше
не существует. Также исправлен путь запуска: системный `python3` → venv Hermes.

Это влияет только на тех, кто сам поднимал Bifrost. Для пользователей плагина
изменений не требуется — плагин говорит с Bifrost по MCP, ему неважно
какая версия mcp под капотом.

---

## 2026-08-21 — v1.2.0

### Unified key resolver + STT language fix + image gen model

Три изменения:

1. **Key resolver.** Плагины теперь находят Bifrost-ключ автоматически —
   через `BIFROST_API_KEY`, через `providers.*.key_env` в config.yaml,
   или через любой `HERMES_CUSTOM_*_API_KEY` со значением `sk-bf-*`.
   Дублировать ключ больше не нужно.

2. **STT language.** Без `stt.bifrost.language: ru` Whisper получает
   английский хинт (`stt.language: "en"` из дефолтов) и плохо
   распознаёт русскую речь.

3. **Image gen model.** `routerai/openai/gpt-image-1` заменён на
   `routerai/openai/gpt-image-2` (gpt-image-1 deprecated).

**Действие:**

```bash
# 1. Обновить плагины (получат _keyresolver.py + новую модель)
cd ~/hermes-plugin-bifrost-gateway
git pull
./install.sh

# 2. Фикс STT языка
hermes config set stt.bifrost.language ru

# 3. Новая модель image gen
hermes config set image_gen.model routerai/openai/gpt-image-2

# 4. (Опционально) Убрать дубликат ключа, если он есть
hermes config unset BIFROST_API_KEY

# 5. Перезапустить Hermes
```

---

<!-- Новые записи добавляй ниже в формате:
## YYYY-MM-DD — vX.Y.Z

### Что изменилось

**Действие:** что нужно сделать пользователю.
-->
