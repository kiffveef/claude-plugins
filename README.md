# claude-plugins

Personal Claude Code plugin marketplace.

| | Name |
|---|---|
| Repository | `kiffveef/claude-plugins` |
| Marketplace | `kiffveef-plugins` |

The two differ because a marketplace name may not contain "claude".
Use the repository name to add, and the marketplace name to install.

## Install

```sh
claude plugin marketplace add kiffveef/claude-plugins
claude plugin install pebble-time2@kiffveef-plugins
```

## Update

```sh
claude plugin update pebble-time2@kiffveef-plugins
```

## Develop

Register the local clone instead of GitHub. Edits apply on the next session or `/reload-plugins`.

```sh
claude plugin marketplace add /path/to/claude-plugins
claude plugin install pebble-time2@kiffveef-plugins
```

## License

MIT
