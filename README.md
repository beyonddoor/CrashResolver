# CrashResolver

## What is CrashResolver?

CrashResolver tries to manage (fetch, symbolicate, gather statistics) multiple crash reports, crash reports may be from different platforms, such as iOS, Android, Mac OS X, etc.

## How to use it?

This tool need a setting file to configure it, the format as following:

```ini
[global]
LogConfigFile = log.yaml
CrashExt = .txt
SymbolExt = .sym
IosSymbolicateArgs = ./symbolicate.sh
IosCrashRepoUrl = <the url to fetch crashes>
```

```sh
# download crashes from the url
python3 -m CrashResolver.downloader -h
# generate a report
python3 -m CrashResolver.reporter -h
# classify the crashes
python3 -m CrashResolver.classifier -h
```
