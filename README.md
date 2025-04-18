# Pivot Track
**Pivot Track is a CLI tool and library that helps Threat Intelligence analysts to pivot on IoCs and to track their research results.**
Right now, Pivot Track is focussed on infrastructure tracking. It uses [Nils Kuhnert's "Common OSINT Model"](https://github.com/3c7/common-osint-model) for a common representation of several OSINT source results.

The current feature set of PivotTrack is:
- **Query Sources:** Use Pivot Track to interact with different OSINT sources (for now Censys and Shodan)
- **Store Results:** Store the results of your queries, so that you do not have to repeat them all the time
- **Track Infrastructure:** Run Querys at a pre-defined interval and store results to a predefined output (for now OpenSearch)

> [!NOTE]  
> Pivot Track is still work in progress and has been implemented during my personal experiments with automation of OSINT research.

## Usage

```
 Usage: pivottrack [OPTIONS] COMMAND [ARGS]...                                  
                                                                                
 Pivot Track helps TI analysts to pivot on IoC and to track their research.     
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.      │
│ --show-completion             Show completion for the current shell, to copy │
│                               it or customize the installation.              │
│ --help                        Show this message and exit.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ query     This module helps to query different sources of OSINT platforms    │
│           and databases.                                                     │
│ service   This module provides capabilities for running tracking definitions │
│           automatically.                                                     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### Run Queries:
```
 Usage: pivottrack query [OPTIONS] COMMAND [ARGS]...

 This module helps to query different sources of OSINT platforms and databases.

╭─ Options ──────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                        │
╰────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────╮
│ generic   This command executes a "generic" search on a given OSINT source.        │
│ host      This command searches for a host on a given OSINT source.                │
╰────────────────────────────────────────────────────────────────────────────────────╯
```

A "generic" search is a search, that uses the query language of a given OSINT source (i.E. [Shodan](https://www.shodan.io/search/examples) or [Censys](https://support.censys.io/hc/en-us/articles/360059608451-Writing-Queries-in-Censys-Search-Language)).

#### Run Host Queries
```
 Usage: pivottrack query host [OPTIONS] SERVICE HOST

 This command searches for a host on a given OSINT source.

╭─ Arguments ────────────────────────────────────────────────────────────────────────╮
│ *    service      TEXT  [default: None] [required]                                 │
│ *    host         TEXT  [default: None] [required]                                 │
╰────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────╮
│ --raw            --no-raw          [default: no-raw]                               │
│ --output                     TEXT  [default: cli]                                  │
│ --config-path                TEXT  [env var: PIVOTTRACK_CONFIG] [default: None]    │
│ --help                             Show this message and exit.                     │
╰────────────────────────────────────────────────────────────────────────────────────╯
```

#### Run "Generic" Queries
```
 Usage: pivottrack query generic [OPTIONS] SERVICE SEARCH

 This command executes a "generic" search on a given OSINT source.

╭─ Arguments ────────────────────────────────────────────────────────────────────────╮
│ *    service      TEXT  [default: None] [required]                                 │
│ *    search       TEXT  [default: None] [required]                                 │
╰────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ──────────────────────────────────────────────────────────────────────────╮
│ --raw            --no-raw             [default: no-raw]                            │
│ --expand         --no-expand          [default: expand]                            │
│ --output                        TEXT  [default: cli]                               │
│ --config-path                   TEXT  [env var: PIVOTTRACK_CONFIG] [default: None] │
│ --help                                Show this message and exit.                  │
╰────────────────────────────────────────────────────────────────────────────────────╯
```

### Track Infrastructure:
```
 Usage: pivottrack service [OPTIONS] COMMAND [ARGS]...                                
                                                                                      
 This module provides capabilities for running tracking definitions automatically.    
                                                                                      
╭─ Options ──────────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                        │
╰────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ─────────────────────────────────────────────────────────────────────────╮
│ publish-definitions     Search for definitions and publish them to task queue.     │
│ subscribe-definitions   Consume tracking definitions from task queue and execute   │
│                         them.                                                      │
╰────────────────────────────────────────────────────────────────────────────────────╯
```
The definitions, used for automatic tracking, have to follow a certain format. You can find an example [here](https://github.com/lo-chr/pivot-track/blob/main/example/tracking-cobaltstrike.example.yml).

## Setup
### Setup for CLI
1. Create folder for setup: `mkdir pivottrack && cd pivottrack`
1. Clone this repository: `git clone https://github.com/lo-chr/pivot-track.git`
1. Copy example configuration file: `cp pivot-track/example/config.example.yaml config.cli.yaml`
1. Change settings in configuration: Provide required API keys for OSINT services. You can disable connectors with `enabled: False` (see Censys connector configuration in example file)
1. Install CLI application: `pipx install https://github.com/lo-chr/pivot-track` (If you get warnings by pipx, you have to solve them)
1. Set `PIVOTTRACK_CONFIG` environment variable: `export PIVOTTRACK_CONFIG="$(pwd)/config.cli.yaml"`
1. Use Pivot Track, Example: `pivottrack query host shodan 1.1.1.1`