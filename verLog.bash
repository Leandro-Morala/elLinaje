#!/bin/bash

adb logcat --pid=$(adb shell pidof -s org.leandro.morala.ellinaje )

