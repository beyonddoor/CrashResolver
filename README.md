# CrashResolver

## What is CrashResolver?

CrashResolver tries to manage (fetch, symbolicate, gather statistics) multiple crash reports, crash reports may be from different platforms, such as iOS, Android, Mac OS X, etc.

## How to use it?

This tool need a setting file to configure it, you can checkout in assets directory.


```sh
python3 -m CrashResolver.downloader --setting_file settings.ini dir
python3 -m CrashResolver.ios.main -h
python3 -m CrashResolver.android.main -h
```