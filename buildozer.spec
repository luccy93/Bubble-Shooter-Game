[app]
title = Bubble Shooter
package.name = bubbleshooter
package.domain = com.luccy93
source.dir = .
source.include_exts = py,png,jpg,ogg,json
source.include_patterns = assets/*,game/*
version = 1.0.0
version.numeric = 1
requirements = python3,pygame-ce

# Icon and Splash Screen
icon.filename = %(source.dir)s/assets/images/app_icon.png
presplash.filename = %(source.dir)s/assets/images/app_splash.png

# Android configuration
orientation = portrait
osx.kivy_version = 2.3.0
fullscreen = 1
android.permissions = VIBRATE
android.api = 33
android.minapi = 21
android.ndk_api = 21

# Bootstrap settings for Pygame (uses SDL2)
p4a.branch = master
p4a.bootstrap = sdl2

[buildozer]
log_level = 2
warn_on_root = 1
