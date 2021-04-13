#!/usr/bin/env bash

cat hosts | sudo tee -a /etc/hosts

# change background image to blank
DISPLAY=:0 xfconf-query -n -t int -c xfce4-desktop -p /backdrop/screen0/monitorrdp0/workspace0/image-style -s 0
DISPLAY=:0 xfconf-query -n -t int -c xfce4-desktop -p /backdrop/screen0/monitorrdp0/workspace1/image-style -s 0
DISPLAY=:0 xfconf-query -n -t int -c xfce4-desktop -p /backdrop/screen0/monitorrdp0/workspace2/image-style -s 0
DISPLAY=:0 xfconf-query -n -t int -c xfce4-desktop -p /backdrop/screen0/monitorrdp0/workspace3/image-style -s 0

#echo "# chrome 설정"
#sudo sed -i 's#/chrome" #/chrome" --no-sandbox #' /usr/bin/google-chrome
