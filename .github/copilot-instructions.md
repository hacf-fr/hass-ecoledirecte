# GitHub Copilot Instructions

> **Note:** For comprehensive documentation including validation, testing, error recovery, and detailed Home Assistant patterns, see [`AGENTS.md`](../AGENTS.md) at the repository root.
>
> **Why two files?** This file is optimized for GitHub Copilot's quick reference (~200 lines, actionable patterns). `AGENTS.md` is comprehensive documentation for all AI agents (551 lines, detailed context, troubleshooting).

This file provides specific guidance for GitHub Copilot when generating code for this Home Assistant integration.

## Critical Reminders

### Project Information

This integration:

- **Domain:** `ecole_directe`
- **Title:** Ecole Directe
- **Class prefix:** `ED`

Use these exact identifiers throughout the codebase. Never hardcode different values.

### Code Quality Baseline

- **Python:** 4 spaces, 120 char lines, full type hints, async for all I/O
- **YAML:** 2 spaces, modern Home Assistant syntax (no legacy `platform:` style)
- **JSON:** 2 spaces, no trailing commas, no comments

### Validation Before Completion

Before considering any coding task complete, the following must pass:

```bash
script/check      # Runs type-check + lint-check + spell-check
```

Generate code that passes these checks on first run.

## Architecture Overview

**Data Flow:** Entities → Coordinator → API Client (never skip layers)

**Package Structure (DO NOT create other packages):**

- `coordinator/` - DataUpdateCoordinator (base.py + data_processing.py + error_handling.py + listeners.py)
- `api/` - External API client with async aiohttp
- `entity/` - Base entity class (`EDEntity`)
- `entity_utils/` - Entity-specific helpers (device_info, state formatting)
- `config_flow_handler/` - Config flow with schemas/ and validators/ subdirs
  - `validators/*.py` - Config flow validation functions
  - `schemas/*.py` - Data schemas for config flow steps
- `[platform]/` - One directory per platform (sensor, switch, etc.), one class per file
- `services/` - Service implementations
- `utils/` - Integration-wide utilities (string helpers, general validators)

**Do NOT create:**

- `helpers/`, `ha_helpers/`, or similar packages - use `utils/` or `entity_utils/` instead
- `common/`, `shared/`, `lib/` - use existing packages above
- New top-level packages without explicit approval

**Key Patterns:**

- All entities inherit: `(PlatformEntity, EDEntity)` - order matters for MRO
- Unique ID format: `{entry_id}_{description.key}` (set in base entity)
- Services registered in `async_setup()`, NOT `async_setup_entry()` (Quality Scale requirement)
- Config entry data accessed via `entry.runtime_data.client` and `entry.runtime_data.coordinator`

## Workflow Approach

1. **Small, focused changes** - Avoid large refactorings unless explicitly requested
2. **Focus on functionality** - Implement features and fix bugs
3. **Documentation updates** - Update docstrings if behavior changes
4. **Validation** - Run `script/check` to ensure code quality
5. **File organization** - Keep files manageable (~200-400 lines). Split large files into smaller modules.

**Scope Management:**

**Single logical feature or fix:**

- Implement completely even if it spans 5-8 files
- Example: New sensor needs entity class + platform init + code → implement all together
- Example: Bug fix requires changes in coordinator + entity + error handling → do all at once

**Multiple independent features:**

- Implement one at a time
- After completing each feature, suggest committing before proceeding to the next

**Large refactoring (>10 files or architectural changes):**

- Propose a plan first before starting implementation
- Get explicit confirmation from developer

**Important: Do NOT write tests unless explicitly requested.** Focus on implementing functionality. The developer decides when and if tests are needed.

**Translation strategy:**

- Use placeholders in code (e.g., `"config.step.user.title"`) - functionality works without translations
- Update `en.json` only when asked or at major feature completion
- NEVER update other language files automatically - extremely time-consuming
- Ask before updating multiple translation files
- Priority: Business logic first, translations later

## When Uncertain - Research First

**Don't guess - look it up!**

If context is insufficient or requirements are ambiguous:

1. **Search [Home Assistant docs](https://developers.home-assistant.io/)** for current patterns
2. Check the [developer blog](https://developers.home-assistant.io/blog/) for recent changes
3. Look at existing patterns in similar files (e.g., existing sensor implementations)
4. Search: `site:developers.home-assistant.io [your question]` for official guidance
5. Run `script/check` early and often - catch issues before they compound
6. Consult [Ruff rules](https://docs.astral.sh/ruff/rules/) or [Pyright docs](https://microsoft.github.io/pyright/) when validation fails
7. Ask for clarification rather than implementing based on assumptions

**Home Assistant evolves rapidly** - verify current best practices rather than relying on outdated knowledge.

Focus on maintainable, testable code that follows established patterns in the integration.

## Local Development & Debugging

**Start Home Assistant:**

```bash
./script/develop  # Kills existing instances, starts HA on port 8123
```

**Force restart (when needed):**

```bash
pkill -f "hass --config" || true && pkill -f "debugpy.*5678" || true && ./script/develop
```

**When to restart:** After modifying Python files, `manifest.json`, `services.yaml`, translations, or config flow changes

**Reading logs:**

- Live: Terminal where `./script/develop` runs
- File: `config/home-assistant.log` (most recent), `config/home-assistant.log.1` (previous)
- Adjust log level: `custom_components.ecole_directe: debug` in `config/configuration.yaml`

## Working With the Developer

**When requests conflict with these instructions:**

1. Clarify if deviation is intentional
2. Confirm you understood correctly
3. Suggest updating instructions if this is a permanent change
4. Proceed after confirmation

**Maintaining instructions:**

- This project is evolving - instructions should too
- Suggest updates when patterns change
- Keep this file under ~100 lines
- Remove outdated rules, don't just add new ones

**Documentation Strategy:**

**Three types of content with clear separation:**

1. **Developer docs:** Use `docs/development/` (architecture, decisions, internal design) - **ASK FIRST**
2. **User docs:** Use `docs/user/` (installation, configuration, examples for end-users) - **ASK FIRST**
3. **Temporary planning:** Use `.ai-scratch/` (never committed, AI-only scratch files) - OK without asking

**Rules for creating documentation:**

- ❌ **NEVER** create markdown files without explicit permission
- ❌ **NEVER** create "helpful" READMEs, GUIDE.md, NOTES.md, etc.
- ❌ **NEVER** create documentation in `.github/` unless it's a GitHub-specified file
- ✅ **ALWAYS ask first** "Should I create documentation for this?"
- ✅ **Prefer module/class/function docstrings** over separate markdown files
- ✅ **Prefer extending** existing docs over creating new files
- ✅ **Use `.ai-scratch/`** for all temporary planning and notes

**Session management:**

- When a task is complete and developer moves to new topic: suggest committing changes and offer commit message
- Monitor context size - warn if getting large and new topic starts
- Offer to create summary for fresh session if context is strained
- Suggest once, don't nag if declined

**Commit message format:**

Follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

```text
type(scope): short summary (max 72 chars)

- Optional detailed points
- Reference issues if applicable
```

**Always check git diff first** - don't rely on session memory. Include all changes in your message.

**Common types:**

- `feat:` - User-facing functionality (new sensor, service, config option)
- `fix:` - Bug fixes (user-facing issues)
- `chore:` - Dev tools, dependencies, devcontainer (NOT user-facing)
- `refactor:` - Code restructuring (no functional change)
- `docs:` - Documentation changes
