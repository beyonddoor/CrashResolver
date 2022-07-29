'''
CrashResolver tries to manage (fetch, symbolicate, gather statistics) multiple crash reports.
Crash reports may be from different platforms, such as iOS, Android, Mac OS X, etc.

This tool need a setting file to configure it, you can checkout in assets directory.

```sh
python3 -m CrashResolver.downloader --setting_file settings.ini dir
python3 -m CrashResolver.ios.main -h
python3 -m CrashResolver.android.main -h
```

'''

__version__ = '1.0.0'
