<h1 align="center">
  palera1n
</h1>

<p align="center">
  <a href="#">
    <img src="https://img.shields.io/badge/made%20with-love-E760A4.svg" alt="Made with love">
  </a>
  <a href="https://github.com/palera1n/palera1n/blob/main/LICENSE" target="_blank">
    <img src="https://img.shields.io/github/license/palera1n/palera1n.svg" alt="License">
  </a>
  <a href="https://github.com/palera1n/palera1n/graphs/contributors" target="_blank">
    <img src="https://img.shields.io/github/contributors/palera1n/palera1n.svg" alt="Contributors">
  </a>
  <a href="https://github.com/palera1n/palera1n/commits/main" target="_blank">
    <img src="https://img.shields.io/github/commit-activity/w/palera1n/palera1n.svg" alt="Commits">
  </a>
  <a href="https://dsc.gg/palera1n" target="_blank">
    <img src="https://img.shields.io/discord/1028398973452570725?label=discord" alt="Discord">
  </a>
</p>

<p align="center">
iOS 15.0-16.3 work in progress, (semi-)tethered checkm8 jailbreak
</p>

# This is a work in progress.

Read this throughly, feel free to ask questions, know the risks. If you want to ask questions, either:

1. Ask in the [palera1n Discord](https://discord.gg/4S3yUMxuQH)
2. Ask in the r/jailbreak Discord #palera1n channel

Please, please, please, provide necessary info:

- iOS version and device (eg. iPhone 7+ 15.1, iPhone 6s 15.3.1)
- Computer's OS and version (eg. Ubuntu 22.04, macOS 13.0)
- The command you ran

**DO NOT** harass tweak devs if tweaks don't work. Refer to [here](https://github.com/itsnebulalol/ios15-tweaks) for compatiblity.

# What does this do?

It boots the device with patches for the jailbreak.

**WARNING**: I am NOT responsible for any data loss. The user of this program accepts responsibility should something happen to their device. While nothing should happen, jailbreaking has risks in itself. If your device is stuck in recovery, please run `futurerestore --exit-recovery`, or use `irecovery -n`.

On A11, you **must disable your passcode while in the jailbroken state**. We don't have an A11 SEP exploit yet.

# Prerequisites

1. checkm8 vulnerable iOS device on iOS 15 (A8X-A11)
    - You must install the Tips app from the App Store before running the script
2. Linux or macOS computer
    - Python 3 is required
3. iOS 15.0-16.3
4. A brain
    - Remember, this is mainly for developers.

# How to use

## Install pip package (stable)

1. Install palera1n with `pip install -U palera1n`
2. Run `palera1n`
    - \[A11\] Before running, you **must** disable your passcode
3. Follow the on-screen steps carefully

## Install latest (possibly unstable)

1. Install palera1n with `pip install -U git+https://github.com/palera1n/palera1n`
2. Run `palera1n`
    - \[A11\] Before running, you **must** disable your passcode
3. Follow the on-screen steps carefully

# Credits

- [Nathan](https://github.com/verygenericname)
    - The ramdisk that dumps blobs is a slimmed down version of SSHRD_Script
    - Also helped Mineek getting the kernel up and running and with the patches
    - Helping with adding multiple device support
- [Mineek](https://github.com/mineek)
    - For the patching and booting commands
    - Adding tweak support
- [Amy](https://github.com/elihwyma) for the Pogo app
- [nyuszika7h](https://github.com/nyuszika7h) for the script to help get into DFU
- [the Procursus Team](https://github.com/ProcursusTeam) for the amazing bootstrap
- [F121](https://github.com/F121Live) for helping test
- [tihmstar](https://github.com/tihmstar) for original iBoot64Patcher/img4tool
- [xerub](https://github.com/xerub) for img4lib and restored_external in the ramdisk
- [Cryptic](https://github.com/Cryptiiiic) for iBoot64Patcher fork
- [m1sta](https://github.com/m1stadev) for pyimg4
