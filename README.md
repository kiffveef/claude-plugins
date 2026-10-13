# claude-plugins

Personal [Claude Code](https://code.claude.com/docs) plugins, served as a plugin marketplace named `kiffveef-plugins`
(marketplace names may not contain "claude", so it differs from the repository name).

## Install

```sh
claude plugin marketplace add kiffveef/claude-plugins
claude plugin install pebble-time2@kiffveef-plugins
```

For local development, register the clone instead so edits apply on the next session or `/reload-plugins`:

```sh
claude plugin marketplace add /path/to/claude-plugins
```

## Plugins

| Plugin | What it adds |
|---|---|
| `pebble-time2` | Skill for Pebble Time 2 (emery) watchface development in C: Health API, custom TTF fonts built from variable fonts, emulator and cloudpebble workflow from WSL2, implementation rules. Complements the official [pebble-watchface](https://github.com/coredevices/pebble-watchface-agent-skill) skill. |

## License

MIT
