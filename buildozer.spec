[app]
# (str) Title of your application
title = TelemuTV

# (str) Package name
package.name = telemu

# (str) Package domain (needed for android/ios packaging)
package.domain = com.diegob.telemu

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, venv, .git, __pycache__

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements - AGGIORNATO per la tua app
requirements = python3,kivy,requests,ffpyplayer

# (list) Supported orientations - LANDSCAPE per TV
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not - TRUE per TV
fullscreen = 1

# (list) Permissions - NECESSARIE per download e riproduzione video
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,WAKE_LOCK

# (int) Target Android API, should be as high as possible - AGGIORNATO
android.api = 33

# (int) Minimum API your APK / AAB will support - OK per TV
android.minapi = 21

# (str) Android NDK version to use - PIÙ RECENTE
android.ndk = 25b

# (list) The Android archs to build for - OTTIMIZZATO per TV moderne
android.archs = arm64-v8a

# SUPPORTO TV - AGGIUNTE SPECIFICHE PER ANDROID TV
android.manifest.intent_filters = android/intent_filters.xml

# (bool) enables Android auto backup feature
android.allow_backup = True

# (str) Presplash background color - NERO per TV
android.presplash_color = #000000

# (str) Android app theme - FULLSCREEN per TV
android.apptheme = "@android:style/Theme.NoTitleBar.Fullscreen"

# MODALITÀ RELEASE - MANTENUTE le tue impostazioni keystore
android.release = 1
android.keystore = my-release-key.keystore
android.keyalias = my-key-alias
android.keystore_pass = bibo46
android.keyalias_pass = bibo46

#
# Android specific
#

# (str) Adaptive icon of the application (used if Android API level is 26+ at runtime)
#icon.adaptive_foreground.filename = %(source.dir)s/data/icon_fg.png
#icon.adaptive_background.filename = %(source.dir)s/data/icon_bg.png

# (list) features (adds uses-feature -tags to manifest) - SUPPORTO TV
android.features = android.software.leanback

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (bool) If True, then automatically accept SDK license
android.accept_sdk_license = True

# (str) Android entry point, default is ok for Kivy-based app
#android.entrypoint = org.kivy.android.PythonActivity

# (str) Full name including package path of the Java class that implements Android Activity
#android.activity_class_name = org.kivy.android.PythonActivity

# (str) Extra xml to write directly inside the <manifest> element of AndroidManifest.xml
android.extra_manifest_xml = ./android/extra_manifest.xml

# (str) Extra xml to write directly inside the <manifest><application> tag of AndroidManifest.xml
android.extra_manifest_application_arguments = ./android/extra_manifest_application.xml

# (bool) Skip byte compile for .py files
android.no-byte-compile-python = False

# (str) The format used to package the app for debug mode (apk or aar).
android.debug_artifact = apk

#
# Python for android (p4a) specific
#

# (str) python-for-android fork to use in case if p4a.url is not specified, defaults to upstream (kivy)
#p4a.fork = kivy

# (str) python-for-android branch to use, defaults to master
#p4a.branch = master

# (str) Bootstrap to use for android builds
p4a.bootstrap = sdl2

#
# iOS specific (non necessario per TV ma mantenuto)
#

ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.10.0
ios.codesign.allowed = false

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1