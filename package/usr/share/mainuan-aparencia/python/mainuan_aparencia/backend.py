"""Qt bridge: exposes the core logic to QML as `systemService` and `layoutService`."""
from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Property, QFileSystemWatcher, QObject, Qt, QTimer, QUrl, Signal, Slot

from . import __version__, core, i18n

# Theme, wallpaper and layout operations all talk to plasmashell: run one at a time.
_OPERATION_LOCK = threading.Lock()


def _to_path(value) -> str:
    if isinstance(value, QUrl):
        return value.toLocalFile()
    text = str(value)
    if text.startswith("file:"):
        return QUrl(text).toLocalFile()
    return text


def _url(path: str) -> str:
    return QUrl.fromLocalFile(path).toString()


class _Worker(QObject):
    """Runs a blocking function on a Python thread and delivers the result on the Qt thread."""
    done = Signal(object)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._callback: Optional[Callable] = None
        self.done.connect(self._deliver, Qt.ConnectionType.QueuedConnection)

    def start(self, work: Callable, callback: Callable) -> bool:
        if not _OPERATION_LOCK.acquire(blocking=False):
            return False
        self._callback = callback

        def target():
            try:
                result = work()
            except Exception as exc:  # never let a worker thread die silently
                result = (False, f"Erro: {exc}")
            finally:
                _OPERATION_LOCK.release()
            self.done.emit(result)

        threading.Thread(target=target, daemon=True).start()
        return True

    @Slot(object)
    def _deliver(self, result) -> None:
        callback, self._callback = self._callback, None
        if callback:
            callback(result)


class Translator(QObject):
    """Texts for QML. The language is chosen once from the system, there is no setting."""

    @Slot(str, result=str)
    def t(self, key: str) -> str:
        return i18n.t(key)

    @Slot(str, "QVariant", result=str)
    def tf(self, key: str, args) -> str:
        return i18n.tf(key, args if isinstance(args, (list, tuple)) else [args])

    language = Property(str, lambda self: i18n.language(), constant=True)


class SystemService(QObject):
    stateChanged = Signal()
    busyChanged = Signal()
    messageChanged = Signal()
    wallpapersChanged = Signal()

    def __init__(self, appearance: Optional[core.Appearance] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._ap = appearance or core.Appearance()
        self._worker = _Worker(self)
        self._busy = False
        self._message = ""
        self._message_error = False
        self._dark = False
        self._theme_known = False
        self._accent_id = core.DEFAULT_ACCENT
        self._accent_color = ""
        self._style = "solid"
        self._styles: list[str] = []
        self._style_available = False
        self._wallpapers: list[dict] = []
        self._current_wallpaper = ""

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(400)
        self._timer.timeout.connect(self.refresh)
        # Follow the system when the theme changes outside this app (system settings, day/night switch).
        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_file_changed)
        self._watcher.directoryChanged.connect(self._on_file_changed)
        self._watch_paths()
        self.refresh()
        self.refreshWallpapers()

    # -- watching ----------------------------------------------------------------
    def _watch_paths(self) -> None:
        env = self._ap.env
        wanted = [str(env.config_dir), str(env.config_dir / "kdeglobals"), str(env.appletsrc)]
        known = set(self._watcher.files()) | set(self._watcher.directories())
        for path in wanted:
            if path not in known and Path(path).exists():
                self._watcher.addPath(path)

    @Slot(str)
    def _on_file_changed(self, _path: str) -> None:
        self._watch_paths()  # an atomic replace drops the watch of the old inode
        self._timer.start()

    # -- state ---------------------------------------------------------------------
    @Slot()
    def refresh(self) -> None:
        ap = self._ap
        data = ap.kdeglobals()
        known = "Colors:Window" in data or "ColorScheme" in data.get("General", {})
        if known:
            dark = ap.is_dark()
        else:  # not a KDE session: ask Qt for the platform colour scheme
            try:
                from PySide6.QtGui import QGuiApplication
                dark = QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
            except Exception:
                dark = False
        values = (dark, known, ap.accent_id(), ap.accent_color(), ap.current_style(),
                  ap.installed_visual_styles(), ap.visual_style_available(), ap.current_wallpaper())
        current = (self._dark, self._theme_known, self._accent_id, self._accent_color, self._style,
                   self._styles, self._style_available, self._current_wallpaper)
        if values == current:
            return
        (self._dark, self._theme_known, self._accent_id, self._accent_color, self._style,
         self._styles, self._style_available, self._current_wallpaper) = values
        self.stateChanged.emit()

    @Slot()
    def refreshWallpapers(self) -> None:
        items = []
        for entry in self._ap.list_wallpapers():
            items.append({**entry, "url": _url(entry["path"]), "thumbUrl": _url(entry["thumb"])})
        self._wallpapers = items
        self.wallpapersChanged.emit()

    def _set_busy(self, value: bool) -> None:
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit()

    def _set_message(self, text: str, error: bool = False) -> None:
        self._message, self._message_error = text, error
        self.messageChanged.emit()

    def _run(self, work: Callable[[], "tuple[bool, str]"]) -> None:
        if self._busy or not self._worker.start(work, self._finished):
            self._set_message(i18n.t("busy"), True)
            return
        self._set_busy(True)

    def _finished(self, result) -> None:
        ok, message = result
        self._set_busy(False)
        self._set_message(message, not ok)
        self.refresh()
        self.refreshWallpapers()

    # -- properties ------------------------------------------------------------------
    darkTheme = Property(bool, lambda self: self._dark, notify=stateChanged)
    themeKnown = Property(bool, lambda self: self._theme_known, notify=stateChanged)
    accentId = Property(str, lambda self: self._accent_id, notify=stateChanged)
    accentColor = Property(str, lambda self: self._accent_color, notify=stateChanged)
    visualStyle = Property(str, lambda self: self._style, notify=stateChanged)
    installedVisualStyles = Property("QVariantList", lambda self: list(self._styles), notify=stateChanged)
    visualStyleAvailable = Property(bool, lambda self: self._style_available, notify=stateChanged)
    currentWallpaper = Property(str, lambda self: self._current_wallpaper, notify=stateChanged)
    busy = Property(bool, lambda self: self._busy, notify=busyChanged)
    lastMessage = Property(str, lambda self: self._message, notify=messageChanged)
    lastMessageIsError = Property(bool, lambda self: self._message_error, notify=messageChanged)
    appVersion = Property(str, lambda self: __version__, constant=True)
    wallpapers = Property("QVariantList", lambda self: list(self._wallpapers), notify=wallpapersChanged)
    accentProfiles = Property("QVariantList", lambda self: [
        {"id": a["id"], "name": core.accent_name(a), "color": a["color"]} for a in core.ACCENTS], constant=True)
    logoSource = Property(str, lambda self: _url(str(self._ap.env.share / "logoMainuan.png")), constant=True)

    # -- actions ---------------------------------------------------------------------
    @Slot(str)
    def setTheme(self, value: str) -> None:
        self._set_message(i18n.t("msg_applying_theme"))
        self._run(lambda: self._ap.set_theme(value))

    @Slot(str)
    def setAccent(self, accent_id: str) -> None:
        self._set_message(i18n.t("msg_applying_accent"))
        self._run(lambda: self._ap.set_accent(accent_id))

    @Slot(str)
    def setVisualStyle(self, style: str) -> None:
        self._set_message(i18n.t("msg_applying_style"))
        self._run(lambda: self._ap.set_visual_style(style))

    @Slot(str)
    def setWallpaper(self, path: str) -> None:
        def work():
            ok, message = self._ap.set_wallpaper(_to_path(path))
            return (True, i18n.t("wallpaper_applied")) if ok else (False, message[:1].upper() + message[1:])
        self._set_message(i18n.t("msg_applying_wallpaper"))
        self._run(work)

    @Slot("QVariant")
    def addWallpapers(self, urls) -> None:
        paths = [_to_path(item) for item in (urls or [])]
        if not paths:
            return
        added, errors = 0, []
        for path in paths:
            ok, info = self._ap.add_wallpaper(path)
            if ok:
                added += 1
            else:
                errors.append(info)
        if added:
            text = i18n.t("wp_added_one" if added == 1 else "wp_added_many", n=added)
            if errors:
                text += i18n.t("wp_not_added", errors=" ".join(errors))
        else:
            text = " ".join(errors)
        self._set_message(text, not added)
        self.refreshWallpapers()

    @Slot(str)
    def removeWallpaper(self, path: str) -> None:
        ok, message = self._ap.remove_wallpaper(_to_path(path))
        self._set_message(message, not ok)
        self.refreshWallpapers()


class LayoutService(QObject):
    changed = Signal()
    busyChanged = Signal()
    messageChanged = Signal()
    _queried = Signal(object)

    def __init__(self, layouts: Optional[core.Layouts] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._lay = layouts or core.Layouts()
        self._worker = _Worker(self)
        self._busy = False
        self._available = False
        self._active = ""
        self._message = ""
        self._error = False
        self._has_backup = self._lay.has_backup
        self._queried.connect(self._on_queried, Qt.ConnectionType.QueuedConnection)

    # -- properties --------------------------------------------------------------------
    available = Property(bool, lambda self: self._available, notify=changed)
    activeLayout = Property(str, lambda self: self._active, notify=changed)
    hasBackup = Property(bool, lambda self: self._has_backup, notify=changed)
    busy = Property(bool, lambda self: self._busy, notify=busyChanged)
    message = Property(str, lambda self: self._message, notify=messageChanged)
    messageIsError = Property(bool, lambda self: self._error, notify=messageChanged)
    layouts = Property("QVariantList", lambda self: core.layouts_info(), constant=True)

    def _set_message(self, text: str, error: bool = False) -> None:
        self._message, self._error = text, error
        self.messageChanged.emit()

    def _set_busy(self, value: bool) -> None:
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit()

    # -- refresh (asks Plasma which layout is active) -------------------------------------
    @Slot()
    def refresh(self) -> None:
        if self._busy:
            return

        def query():
            if not _OPERATION_LOCK.acquire(blocking=False):
                return
            try:
                available = self._lay.available()
                active = self._lay.describe()[1] if available else ""
            except Exception:
                available, active = False, ""
            finally:
                _OPERATION_LOCK.release()
            self._queried.emit((available, active))

        threading.Thread(target=query, daemon=True).start()

    @Slot(object)
    def _on_queried(self, result) -> None:
        available, active = result
        self._available, self._active = available, active
        self._has_backup = self._lay.has_backup
        self.changed.emit()

    # -- actions -----------------------------------------------------------------------------
    def _run(self, work: Callable[[], "tuple[bool, str]"]) -> None:
        if self._busy or not self._worker.start(work, self._finished):
            self._set_message(i18n.t("busy"), True)
            return
        self._set_busy(True)

    def _finished(self, result) -> None:
        ok, message = result
        self._set_busy(False)
        self._set_message(message, not ok)
        self._has_backup = self._lay.has_backup
        self.changed.emit()
        self.refresh()

    @Slot(str)
    def apply(self, layout_id: str) -> None:
        self._set_message(i18n.t("msg_applying_layout", name=core.layout_name(layout_id) if layout_id in core.LAYOUT_IDS else ""))
        self._run(lambda: self._lay.apply(layout_id))

    @Slot()
    def restoreBackup(self) -> None:
        self._set_message(i18n.t("msg_restoring"))
        self._run(self._lay.restore_backup)
