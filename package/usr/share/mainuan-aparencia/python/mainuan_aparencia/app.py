"""Application entry point."""
from __future__ import annotations

import glob
import os
import signal
import sys
from pathlib import Path

from . import __version__, core, i18n


def _pick_quick_style() -> str:
    for pattern in ("/usr/lib/*/qt6/qml/org/kde/desktop", "/usr/lib/qt6/qml/org/kde/desktop"):
        if glob.glob(pattern):
            return "org.kde.desktop"
    return "Fusion"


def main() -> int:
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", _pick_quick_style())
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QGuiApplication, QIcon
    from PySide6.QtQml import QQmlApplicationEngine

    from PySide6.QtCore import QLocale

    from .backend import LayoutService, SystemService, Translator

    # Language: automatic, from the system (LANGUAGE, Qt UI languages, LC_ALL, LC_MESSAGES, LANG).
    i18n.set_language(i18n.detect(QLocale.system().uiLanguages()))

    app = QGuiApplication(sys.argv)
    app.setApplicationName("mainuan-aparencia")
    app.setApplicationVersion(__version__)
    app.setDesktopFileName("org.mainuan.Aparencia")
    logo = core.SHARE_DIR / "logoMainuan.png"
    app.setWindowIcon(QIcon.fromTheme("mainuan-aparencia", QIcon(str(logo))))
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    env = core.Env()
    appearance = core.Appearance(env)
    translator = Translator()
    system = SystemService(appearance)
    layouts = LayoutService(core.Layouts(env, appearance))

    engine = QQmlApplicationEngine()
    context = engine.rootContext()
    context.setContextProperty("systemService", system)
    context.setContextProperty("layoutService", layouts)
    context.setContextProperty("layoutModel", layouts.layouts)
    context.setContextProperty("i18n", translator)
    engine.load(QUrl.fromLocalFile(str(core.SHARE_DIR / "qml" / "Main.qml")))
    if not engine.rootObjects():
        print("mainuan-aparencia: não foi possível carregar a interface (módulos QML em falta?).", file=sys.stderr)
        return 1
    layouts.refresh()
    return app.exec()
