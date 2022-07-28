'''
CrashResolver tries to manage (fetch, symbolicate, gather statistics) multiple crash reports.
Crash reports may be from different platforms, such as iOS, Android, Mac OS X, etc.

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
python3 -m CrashResolver.downloader --setting_file settings.ini dir
python3 -m CrashResolver.reporter -h
python3 -m CrashResolver.classifier -h
```

'''

__version__ = '0.1.0'
