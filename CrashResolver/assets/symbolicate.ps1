# windows上的符号化wrapper，输出符号化信息到stdout

$env:Path += ';D:\apps\android-ndk-r13b\toolchains\x86_64-4.9\prebuilt\windows\bin;D:\apps\android-ndk-r13b;'
ndk-stack -sym $args[0] -dump $args[1]
