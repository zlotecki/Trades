# PyInstaller spec: menu-bar-only Mac app (no Dock icon, no Terminal window).
block_cipher = None

a = Analysis(
    ["run_aisec.py"],
    pathex=["."],
    hiddenimports=["pystray._darwin", "PyObjCTools.AppHelper"],
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="AISecurity",
          console=False)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, name="AISecurity")
app = BUNDLE(
    coll,
    name="AI Security.app",
    bundle_identifier="com.aisecurity.app",
    info_plist={
        "LSUIElement": True,  # menu-bar only
        "CFBundleName": "AI Security",
        "CFBundleShortVersionString": "0.1.0",
        "NSHumanReadableCopyright": "AI Security prototype",
    },
)
