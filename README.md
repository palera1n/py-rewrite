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
iOS 15.0-16.3 work in progress, semi-tethered checkm8 jailbreak
</p>

# BEFORE YOU USE

This is ROOTLESS, and is NOT READY. It was made public so you can contribute and explore the code. This is not the final product.

Loader app does not appear, you'll need to use `deploy.sh` from [this repo](https://github.com/mineek/kok3shi16-rootless).

# This is a work in progress.

Read this throughly, feel free to ask questions, know the risks. If you want to ask questions, either:

1. Ask in the [palera1n Discord](https://discord.gg/4S3yUMxuQH)
2. Ask in the r/jailbreak Discord #palera1n channel

Please, please, please, provide necessary info:

- iOS version and device (eg. iPhone 7+ 15.1, iPhone 6s 15.3.1)
- Computer's OS and version (eg. Ubuntu 22.04, macOS 13.0)
- The command you ran

**DO NOT** harass tweak devs if tweaks don't work. Refer to [here](https://github.com/itsnebulalol/ios15-tweaks) for compatiblity.

# Patreons

Thank you so much to our Patreons that make the future development possible! You may sub [here](https://patreon.com/palera1n), if you'd like to. If you subscribe, please message [Nebula](https://twitter.com/itsnebulalol) in any way preferred to have you put here.

<a href="https://github.com/samh06"><img width=64 src="https://user-images.githubusercontent.com/18669106/206333607-881d7ca1-f3bf-4e18-b620-25de0c527315.png"></img></a>
<a href="https://havoc.app"><img width=64 src="https://docs.havoc.app/img/standard_icon.png"></img></a>
<a href="https://twitter.com/yyyyyy_public"><img width=64 src="https://pbs.twimg.com/profile_images/1429332550112079876/dQQgsURc_400x400.jpg"></img></a>
<a href="https://twitter.com/0xSp00kyb0t"><img width=64 src="https://pbs.twimg.com/profile_images/1603601553226620935/1t4yD1bD_400x400.jpg"></img></a>
<a href="https://chariz.com"><img width=64 src="https://chariz.com/img/favicon.png"></img></a>
<a href="https://twitter.com/stars6220"><img width=64 src="https://pbs.twimg.com/profile_images/1606990218925670400/Y4JBl6OS_400x400.jpg"></img></a>
<a href="https://github.com/beast9265"><img width=64 src="https://avatars.githubusercontent.com/u/79794946?v=4"></img></a>

# What does this do?

It boots the device with patches for the jailbreak. 

**WARNING**: I am NOT responsible for any data loss. The user of this program accepts responsibility should something happen to their device. While nothing should happen, jailbreaking has risks in itself. If your device is stuck in recovery, please run `futurerestore --exit-recovery`, or use `irecovery -n`.

On A11, you **must disable your passcode while in the jailbroken state**. We don't have an A11 SEP exploit yet.

# Prerequisites

1. checkm8 vulnerable iOS device on iOS 15.0-16.3 (A8X-A11)
2. Linux or macOS computer
    - Python 3 is required
3. iOS 15.0-16.3
4. A brain
    - Remember, this is mainly for developers.
5. Passcode disabled on A11
    - On iOS 16, if you EVER enabled a passcode on 16, you have to reset through the settings app/restore with a computer
    - The device **will not** boot jailbroken if it's enabled

# How to use

## Install pip package (stable)

1. Install palera1n with `pip install -U palera1n`
2. Run `palera1n`
3. Follow the on-screen steps carefully

## Install latest (possibly unstable)

1. Install palera1n with `pip install -U git+https://github.com/palera1n/py-rewrite`
2. Run `palera1n`
3. Follow the on-screen steps carefully

## Install with Poetry

1. Install Poetry with `pip install poetry`
2. Clone this repo with `git clone https://github.com/palera1n/py-rewrite && cd py-rewrite`
3. Install dependencies with `poetry install`
4. Run `poetry run palera1n`
5. Follow the on-screen steps carefully

# Credits

- [Nebula](https://github.com/itsnebulalol), palera1n owner and Python rewrite lead developer
- [Nathan](https://github.com/verygenericname)
- [Mineek](https://github.com/mineek)
    - Work on jbinit, together with [Nick Chan](https://github.com/asdfugil)
- [Amy](https://github.com/elihwyma) for the [Pogo](https://github.com/elihwyma/Pogo) app
- [checkra1n](https://github.com/checkra1n) for the base of the kpf
- [nyuszika7h](https://github.com/nyuszika7h) for the script to help get into DFU
- [the Procursus Team](https://github.com/ProcursusTeam) for the amazing [bootstrap](https://github.com/ProcursusTeam/Procursus)
- [F121](https://github.com/F121Live) for helping test
- [Tom](https://github.com/guacaplushy) for a couple patches and bugfixes
- [libimobiledevice](https://github.com/libimobiledevice) for irecovery, and [nikias](https://github.com/nikias) for keeping it up to date
- [Nick Chan](https://github.com/asdfugil) general help with patches and jbinit
- [Serena](https://github.com/SerenaKit) for helping with boot ramdisk
- [Évelyne](https://github.com/evelyneee) for ElleKit, rootless tweak injection
