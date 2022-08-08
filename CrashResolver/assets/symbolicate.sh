export DEVELOPER_DIR="/Applications/XCode.app/Contents/Developer"
curDir="$(dirname "$0")"

echo processing "$1"
"$curDir"/symbolicatecrash "$1" -d UnityFramework.framework.dSYM -d ProductName.app.dSYM -o "${1%.txt}.sym" 2>> symbol.log

# ./symbolicatecrash -o "$1".txt "$1" ./

# mdfind 'com_apple_xcode_dsym_uuids = *'
# '/Applications/Xcode.app/Contents/Developer/usr/bin/symbols' -uuid 'ProductName.app.dSYM/Contents/Resources/DWARF/ProductName'
# dwarfdump --uuid ProductName.app.dSYM 
