---
name: bifrost-setup
description: "Install and configure Bifrost Gateway plugins for Hermes Agent."
version: 1.0.0
author: temga
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [bifrost, setup, llm, image-gen, web-search, stt, tts]
    category: devops
---

# Bifrost Setup Skill

Устанавливает и настраивает пак плагинов Bifrost Gateway для Hermes Agent.
Все запросы (LLM, image gen, web search, STT, TTS) идут через единый
Bifrost-ключ `sk-bf-*`.

## When to Use

Когда нужно настроить Hermes для работы через Bifrost AI Gateway —
установка 5 плагинов, ключ, config, проверка.

## How to Run

Выполни шаги из SETUP.md в репозитории:

```bash
hermes skills tap add temga/hermes-plugin-bifrost-gateway
hermes skills inspect temga/hermes-plugin-bifrost-gateway/skills/bifrost-setup
```

Полная инструкция: https://github.com/temga/hermes-plugin-bifrost-gateway/blob/main/SETUP.md

## Quick Reference

```bash
# Установка плагинов
git clone https://github.com/temga/hermes-plugin-bifrost-gateway.git
cd hermes-plugin-bifrost-gateway
./install.sh        # Linux/macOS/WSL
.\install.ps1       # Windows

# Ключ
hermes config get BIFROST_API_KEY          # проверить, есть ли уже
hermes config set BIFROST_API_KEY sk-bf-... # записать если нет

# Провайдеры
hermes config set model.provider bifrost
hermes config set model.default neuraldeep/gpt-oss-120b
hermes config set auxiliary.vision.provider bifrost
hermes config set auxiliary.vision.model neuraldeep/qwen3.8-27b
hermes config set image_gen.provider bifrost
hermes config set web.search_backend bifrost
hermes config set web.extract_backend bifrost
hermes config set stt.provider bifrost
hermes config set tts.provider bifrost
```
