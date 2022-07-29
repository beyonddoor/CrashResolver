#! /bin/bash

# mac系统上的wrapper文件，符号化txt，输出sym文件

export DEVELOPER_DIR="/Applications/XCode.app/Contents/Developer"
curDir="$(dirname "$0")"

echo processing "$1"
"$curDir"/symbolicatecrash "$1" -d UnityFramework.framework.dSYM -d ProductName.app.dSYM -o "${1%.txt}.sym" 2>>symbol.log
