# DBWatcher

DBWatcher is a plugin to help you monitor selected database(s) on both iOS and Android devices. This module provides a graphical user interface (GUI) to interactively watch and scan for databases.

## Installation

### Android
- Install the `objection` framework from the official GitHub repository: https://github.com/sensepost/objection
- Install `Android Debug Bridge (adb)` via this guide from XDA: https://www.xda-developers.com/install-adb-windows-macos-linux/#how-to-set-up-adb
- Download, install and run `Frida` on a `rooted Android` by following the tutorial: https://frida.re/docs/home/
    - On the `rooted Adroid`, the `frida-server` is located at `/data/local/tmp/frida-server-16.1.2-android-arm64`

### iPhone
- Create a Linux virtual machine
- Add the `jailbroken iPhone` as a USB Device to the Linux virtual machine: https://www.makeuseof.com/windows-virtualbox-add-usb/    
- Install the required modules
    ```
    sudo apt install python-tk && pip install pysimplegui
    ```
- Install the `objection` framework from the official GitHub repository: https://github.com/sensepost/objection
    - A restart might be required for Linux to add `Frida-tools` to PATH
- Install `libimobiledevice`:
    ```
    sudo apt-get install usbmuxd libimobiledevice6 libimobiledevice-utils
    ```
- run `frida-ls-devices` to ensure that the `frida-server` is running on the `jailbroken iPhone`.
- If `frida-server` is not running:
    - Enable `SSH over USB` by using iproxy
        ```
        iproxy 2222 22 
        ```
    - In a new terminal, connect to the `jailbroken iPhone` via SSH. The root password is `alpine` and the `frida-server` is located at `/usr/sbin/frida-server`
        ```
        ssh root@127.0.0.1 -p 2222    
        ```


## Usage

1. List the names and identifiers for the installed applications.
    ```
    frida-ps -Uai
    ```
2. Start the application on the `rooted Adroid`/`jailbroken iPhone`

3. Launch the `objection` tool from this directory. The application Snapchat is used as an example.
    ```
    objection -g snapchat explore -P .\objection_plugins\
    ```

4. Start the plugin inside the objection Agent.
    ```
    plugin dbwatcher run
    ```

The GUI will display a list of found database directories. Select the directory you want to monitor, click "Next", then select the databases you wish to watch, click "Next" again and then select the tables you want to include.

- <span style="color:yellow">[^] Modified values will be shown in yellow</span>
- <span style="color:green">[+] Added rows will be shown in green</span>
- <span style="color:red">[-] Removed rows will be shown in red</span>

## Restrictions
- You can only choose one directory to monitor
- iOS applications have a greater risk of crashing when using this plugin. Just restart objection
- On iOS, only the Document Directory is available. This is due to the point above.