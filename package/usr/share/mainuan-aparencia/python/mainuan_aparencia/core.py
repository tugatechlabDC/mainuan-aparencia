"""Mainuan Aparência: system logic without any Qt dependency.

Everything that touches the desktop (kdeglobals, plasma-apply-*, Plasma scripting
over D-Bus, KWin) lives here so it can be tested with a fake command runner.
All user-visible texts go through i18n.t().
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import unquote, urlparse

from .i18n import t

APP_ID = "mainuan-aparencia"
SHARE_DIR = Path(os.environ.get("MAINUAN_APARENCIA_SHARE", "/usr/share/mainuan-aparencia"))

# --------------------------------------------------------------------------- #
# Static tables (taken from Mainuan Welcome 1.0)
# --------------------------------------------------------------------------- #

ACCENTS = [
    {"id": "brown", "color": "#d08040", "scheme": "DreamBrown", "icons": "kora-brown"},
    {"id": "cyan", "color": "#3daee9", "scheme": "DreamCyan", "icons": "kora-cyan"},
    {"id": "magenta", "color": "#e8177d", "scheme": "DreamMagenta", "icons": "kora-magenta"},
    {"id": "lime", "color": "#3dd425", "scheme": "DreamLime", "icons": "kora-lima"},
    {"id": "gray", "color": "#aab6b9", "scheme": "DreamGray", "icons": "kora-grey"},
    {"id": "violet", "color": "#a588cb", "scheme": "DreamViolet", "icons": "kora-violet"},
]
DEFAULT_ACCENT = "cyan"


def accent_name(accent: dict) -> str:
    return t(f"accent_{accent['id']}")


VISUAL_STYLES = {
    "blur": {"light": "Dream-Light-Color-Global-6", "dark": "Dream-Dark-Color-Global-6",
             "desktoptheme": "Dream-Color-Plasma", "label": "Dream"},
    "glass": {"light": "com.github.vinceliuice.MacTahoe-Light", "dark": "com.github.vinceliuice.MacTahoe-Dark",
              "desktoptheme": None, "label": "MacTahoe"},
    "solid": {"light": "org.kde.breeze.desktop", "dark": "org.kde.breezedark.desktop",
              "desktoptheme": None, "label": "Breeze"},
}

# Wallpaper applied by the system theme: dark mode -> Mainuan_B, light mode -> Mainuan_C.
THEME_WALLPAPERS = {"dark": "Mainuan_B.png", "light": "Mainuan_C.png"}

LAYOUT_IDS = ["plasma-default", "three-panels", "single-bar", "panel-top", "minimal", "unity", "tiling",
              "macos", "windows11"]


def layouts_info() -> list[dict]:
    """Layout cards in the current language."""
    return [{"layoutId": i, "name": t(f"layout_{i}_name"), "description": t(f"layout_{i}_desc")} for i in LAYOUT_IDS]


def layout_name(layout_id: str) -> str:
    return t(f"layout_{layout_id}_name")


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".svg"}
MAX_WALLPAPERS = 400
MAX_USER_IMAGE_BYTES = 200 * 1024 * 1024


# --------------------------------------------------------------------------- #
# Environment / command runner
# --------------------------------------------------------------------------- #

Runner = Callable[..., "tuple[int, str, str]"]


def default_runner(cmd: list[str], timeout: float = 30.0) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, "", f"{cmd[0]}: command not found"
    except subprocess.TimeoutExpired:
        return 124, "", f"{cmd[0]}: timeout"
    except OSError as exc:  # pragma: no cover - defensive
        return 126, "", str(exc)


@dataclass
class Env:
    home: Path = field(default_factory=Path.home)
    system_data: list[Path] = field(default_factory=lambda: [Path("/usr/local/share"), Path("/usr/share")])
    runner: Runner = default_runner
    share: Path = SHARE_DIR
    sleep: Callable[[float], None] = time.sleep

    @property
    def config_dir(self) -> Path:
        return Path(os.environ["XDG_CONFIG_HOME"]) if os.environ.get("XDG_CONFIG_HOME") and self.home == Path.home() \
            else self.home / ".config"

    @property
    def user_data(self) -> Path:
        return self.home / ".local" / "share"

    @property
    def data_dirs(self) -> list[Path]:
        return [self.user_data] + list(self.system_data)

    @property
    def app_config(self) -> Path:
        return self.config_dir / APP_ID

    @property
    def app_data(self) -> Path:
        return self.user_data / APP_ID

    @property
    def user_wallpapers(self) -> Path:
        return self.app_data / "wallpapers"

    @property
    def backup_dir(self) -> Path:
        return self.app_data / "layout-backups"

    @property
    def appletsrc(self) -> Path:
        return self.config_dir / "plasma-org.kde.plasma.desktop-appletsrc"

    def run(self, cmd: list[str], timeout: float = 30.0) -> tuple[int, str, str]:
        return self.runner(cmd, timeout=timeout)

    def find_tool(self, name: str) -> Optional[str]:
        found = shutil.which(name)
        if found:
            return found
        for base in ("/usr/libexec", "/usr/lib/x86_64-linux-gnu/libexec", "/usr/lib/libexec", "/usr/lib64/libexec"):
            candidate = Path(base) / name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
        return None


# --------------------------------------------------------------------------- #
# ini helpers
# --------------------------------------------------------------------------- #

def read_ini(path: Path) -> dict[str, dict[str, str]]:
    """Tiny KDE-style ini reader (keys are case sensitive, no interpolation)."""
    data: dict[str, dict[str, str]] = {}
    section = ""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return data
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
            data.setdefault(section, {})
        elif "=" in line:
            key, _, value = line.partition("=")
            data.setdefault(section, {})[key.strip()] = value.strip()
    return data


def merge_ini(path: Path, updates: dict[str, dict[str, str]]) -> None:
    """Update keys inside a KDE ini file keeping every other line, section and order."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        lines = []
    pending = {sec: dict(kv) for sec, kv in updates.items()}
    out: list[str] = []
    section: Optional[str] = None

    def flush_section() -> None:
        if section is not None and section in pending and pending[section]:
            for key, value in pending[section].items():
                out.append(f"{key}={value}")
            pending[section] = {}

    for raw in lines:
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            flush_section()
            section = line[1:-1]
            out.append(raw)
            continue
        if section in pending and "=" in line and not line.startswith(("#", ";")):
            key = line.partition("=")[0].strip()
            if key in pending[section]:
                out.append(f"{key}={pending[section].pop(key)}")
                continue
        out.append(raw)
    flush_section()
    for sec, kv in pending.items():
        if kv:
            if out and out[-1].strip():
                out.append("")
            out.append(f"[{sec}]")
            out.extend(f"{k}={v}" for k, v in kv.items())
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".mainuan-tmp")
    tmp.write_text("\n".join(out) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def luminance(rgb: str) -> Optional[float]:
    try:
        r, g, b = [int(part) for part in rgb.split(",")[:3]]
    except ValueError:
        return None
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def style_label(style: str) -> str:
    return VISUAL_STYLES.get(style, {}).get("label", style)


def _detail(err: str, out: str = "") -> str:
    text = (err or out or "").strip().splitlines()
    return text[-1].strip() if text else ""


# --------------------------------------------------------------------------- #
# Theme, accent, style, wallpaper
# --------------------------------------------------------------------------- #

class Appearance:
    """Theme, accent, visual style and wallpaper operations."""

    def __init__(self, env: Optional[Env] = None):
        self.env = env or Env()

    # -- state file ------------------------------------------------------------
    @property
    def state_path(self) -> Path:
        return self.env.app_config / "state.json"

    def read_state(self) -> dict:
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, ValueError):
            return {}

    def write_state(self, **changes) -> None:
        state = self.read_state()
        state.update(changes)
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.state_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
            os.replace(tmp, self.state_path)
        except OSError:
            pass

    # -- detection -------------------------------------------------------------
    def kdeglobals(self) -> dict[str, dict[str, str]]:
        return read_ini(self.env.config_dir / "kdeglobals")

    def current_scheme(self) -> str:
        return self.kdeglobals().get("General", {}).get("ColorScheme", "")

    def is_dark(self) -> bool:
        data = self.kdeglobals()
        lum = luminance(data.get("Colors:Window", {}).get("BackgroundNormal", ""))
        if lum is not None:
            return lum < 128
        scheme = data.get("General", {}).get("ColorScheme", "").lower()
        return "dark" in scheme or "night" in scheme

    # -- colour scheme files -------------------------------------------------------
    @staticmethod
    def scheme_id(accent: dict, dark: bool) -> str:
        return f"{accent['scheme']}{'Dark' if dark else 'Light'}Color"

    def scheme_file(self, scheme_id: str) -> Optional[Path]:
        for base in self.env.data_dirs:
            path = base / "color-schemes" / f"{scheme_id}.colors"
            if path.is_file():
                return path
        return None

    def scheme_installed(self, scheme_id: str) -> bool:
        return self.scheme_file(scheme_id) is not None

    def scheme_display_name(self, scheme_id: str) -> str:
        path = self.scheme_file(scheme_id)
        return read_ini(path).get("General", {}).get("Name", "") if path else ""

    def scheme_is_applied(self, scheme_id: str) -> bool:
        """kdeglobals may store the file id or the display name, so accept both; fall back to the
        window background colour, which every scheme defines."""
        data = self.kdeglobals()
        current = data.get("General", {}).get("ColorScheme", "")
        if current and current in (scheme_id, self.scheme_display_name(scheme_id)):
            return True
        path = self.scheme_file(scheme_id)
        if path is None:
            return False
        wanted = read_ini(path).get("Colors:Window", {}).get("BackgroundNormal", "")
        have = data.get("Colors:Window", {}).get("BackgroundNormal", "")
        return bool(wanted) and wanted == have

    def current_accent_id(self) -> str:
        current = self.current_scheme()
        if not current:
            return ""
        for accent in ACCENTS:
            for variant in (False, True):
                sid = self.scheme_id(accent, variant)
                if current == sid or (self.scheme_display_name(sid) and current == self.scheme_display_name(sid)):
                    return accent["id"]
        return ""

    def accent_id(self) -> str:
        return self.current_accent_id() or self.read_state().get("accent", "") or DEFAULT_ACCENT

    def accent_color(self) -> str:
        wanted = self.current_accent_id() or self.read_state().get("accent", "")
        return next((a["color"] for a in ACCENTS if a["id"] == wanted), "")

    def current_style(self) -> str:
        package = self.kdeglobals().get("KDE", {}).get("LookAndFeelPackage", "")
        if package.startswith("Dream"):
            return "blur"
        if "MacTahoe" in package:
            return "glass"
        if package.startswith("org.kde.breeze"):
            return "solid"
        return "other" if package else "solid"

    def current_icons(self) -> str:
        return self.kdeglobals().get("Icons", {}).get("Theme", "")

    def current_cursor(self) -> str:
        return read_ini(self.env.config_dir / "kcminputrc").get("Mouse", {}).get("cursorTheme", "")

    # -- availability ------------------------------------------------------------
    def lnf_installed(self, package_id: str) -> bool:
        for base in self.env.data_dirs:
            root = base / "plasma" / "look-and-feel" / package_id
            if (root / "metadata.json").is_file() or (root / "metadata.desktop").is_file():
                return True
        return False

    def desktoptheme_installed(self, name: str) -> bool:
        return any((base / "plasma" / "desktoptheme" / name).is_dir() for base in self.env.data_dirs)

    def icon_theme_valid(self, name: str) -> bool:
        roots = [self.env.home / ".icons"] + [base / "icons" for base in self.env.data_dirs]
        return any((root / name / "index.theme").is_file() for root in roots)

    def installed_visual_styles(self) -> list[str]:
        return [key for key, ids in VISUAL_STYLES.items()
                if self.lnf_installed(ids["light"]) or self.lnf_installed(ids["dark"])]

    def visual_style_available(self) -> bool:
        return self.env.find_tool("plasma-apply-lookandfeel") is not None

    # -- colour scheme -------------------------------------------------------------
    def _wait_scheme(self, scheme_id: str, timeout: float = 3.0) -> bool:
        deadline = time.monotonic() + timeout
        while True:
            if self.scheme_is_applied(scheme_id):
                return True
            if time.monotonic() >= deadline:
                return False
            self.env.sleep(0.25)

    # -- icon theme ------------------------------------------------------------------
    def _icons_match(self, icons: str) -> bool:
        return self.current_icons().strip().lower() == icons.strip().lower()

    def _wait_icons(self, icons: str, timeout: float = 3.0) -> bool:
        """Plasma writes the icon theme asynchronously (and a global theme applied just before
        can overwrite it a moment later), so poll instead of reading once."""
        deadline = time.monotonic() + timeout
        while True:
            if self._icons_match(icons):
                return True
            if time.monotonic() >= deadline:
                return False
            self.env.sleep(0.25)

    def _apply_icons(self, icons: str) -> bool:
        """plasma-changeicons first; if Plasma does not confirm, write kdeglobals ourselves and
        notify running applications (KGlobalSettings::IconChanged = 4). Returns True when confirmed."""
        changer = self.env.find_tool("plasma-changeicons")
        for attempt in range(2):
            if changer is not None:
                self.env.run([changer, icons])
                if self._wait_icons(icons, 3.0):
                    return True
            try:
                merge_ini(self.env.config_dir / "kdeglobals", {"Icons": {"Theme": icons}})
            except OSError:
                pass
            dbus = self.env.find_tool("dbus-send")
            if dbus:
                self.env.run([dbus, "--session", "--type=signal", "/KGlobalSettings",
                              "org.kde.KGlobalSettings.notifyChange", "int32:4", "int32:0"], timeout=10)
            if self._wait_icons(icons, 2.0):
                return True
        return False

    def _apply_scheme_manually(self, scheme_id: str) -> bool:
        """Same thing plasma-apply-colorscheme does: copy the scheme's colour groups into
        kdeglobals, record its name and tell running applications to reload the palette."""
        path = self.scheme_file(scheme_id)
        if path is None:
            return False
        source = read_ini(path)
        updates = {sec: kv for sec, kv in source.items() if sec.startswith("Colors:") or sec == "WM"}
        if not updates:
            return False
        updates.setdefault("General", {})
        updates["General"] = {"ColorScheme": scheme_id}
        name = source.get("General", {}).get("Name")
        if name:
            updates["General"]["Name"] = name
        try:
            merge_ini(self.env.config_dir / "kdeglobals", updates)
        except OSError:
            return False
        dbus = self.env.find_tool("dbus-send")
        if dbus:
            # KGlobalSettings::PaletteChanged = 0
            self.env.run([dbus, "--session", "--type=signal", "/KGlobalSettings",
                          "org.kde.KGlobalSettings.notifyChange", "int32:0", "int32:0"], timeout=10)
        return self.scheme_is_applied(scheme_id)

    def _apply_scheme(self, scheme_id: str) -> Optional[str]:
        """Returns None on success or a short technical detail on failure."""
        detail = ""
        tool = self.env.find_tool("plasma-apply-colorscheme")
        if tool is not None:
            rc, out, err = self.env.run([tool, scheme_id])
            detail = _detail(err, out)
            if self._wait_scheme(scheme_id):
                return None
            if rc != 0 and not detail:
                detail = f"rc={rc}"
        else:
            detail = "plasma-apply-colorscheme"
        if self._apply_scheme_manually(scheme_id):
            return None
        return detail or "?"

    # -- applying --------------------------------------------------------------
    def _apply_accent(self, accent_id: str, dark: bool) -> tuple[Optional[str], list[str]]:
        """Apply colour scheme and Kora icons.

        Returns (fatal error or None, non-fatal problems). A fatal error means the
        colour scheme could not be applied at all.
        """
        accent = next((a for a in ACCENTS if a["id"] == accent_id), None)
        if accent is None:
            return t("accent_invalid"), []
        problems: list[str] = []
        scheme = self.scheme_id(accent, dark)
        if not self.scheme_installed(scheme):
            return t("scheme_missing", scheme=scheme), []
        failure = self._apply_scheme(scheme)
        if failure is not None:
            text = t("scheme_unconfirmed", scheme=scheme)
            return (f"{text} ({failure})" if failure else text), []
        icons = accent["icons"]
        if not self.icon_theme_valid(icons):
            problems.append(t("icons_missing", name=icons))
        else:
            if not self._apply_icons(icons):
                problems.append(t("icons_unconfirmed", name=icons))
        self.write_state(accent=accent_id)
        return None, problems

    def _restore_cursor(self, cursor: str) -> None:
        if cursor and self.current_cursor() != cursor:
            tool = self.env.find_tool("plasma-apply-cursortheme")
            if tool:
                self.env.run([tool, cursor])

    def _apply_lnf(self, style: str, dark: bool) -> tuple[bool, str]:
        ids = VISUAL_STYLES[style]
        package = ids["dark" if dark else "light"]
        if not self.lnf_installed(package):
            return False, t("style_not_installed", name=style_label(style))
        tool = self.env.find_tool("plasma-apply-lookandfeel")
        if tool is None:
            return False, t("no_lookandfeel")
        rc, out, err = self.env.run([tool, "-a", package], timeout=60)
        if rc != 0:
            detail = _detail(err, out)
            return False, t("style_failed", name=style_label(style)) + (f" {detail}" if detail else "")
        theme = ids.get("desktoptheme")
        if theme and self.desktoptheme_installed(theme):
            applier = self.env.find_tool("plasma-apply-desktoptheme")
            if applier:
                self.env.run([applier, theme])
        return True, ""

    def _partial(self, problems: list[str]) -> str:
        return t("partial", details="; ".join(problems)) if problems else ""

    def set_theme(self, mode: str) -> tuple[bool, str]:
        """Light/dark system theme. Also applies the matching Mainuan wallpaper."""
        if mode not in ("light", "dark"):
            return False, t("theme_invalid")
        dark = mode == "dark"
        accent_id = self.accent_id()
        style = self.current_style()
        cursor = self.current_cursor()
        before = self.current_wallpaper()
        problems: list[str] = []
        if style in VISUAL_STYLES and self.lnf_installed(VISUAL_STYLES[style]["dark" if dark else "light"]):
            ok, message = self._apply_lnf(style, dark)
            if not ok:
                problems.append(message.rstrip("."))
        fatal, accent_problems = self._apply_accent(accent_id, dark)
        scheme_ok = fatal is None
        if fatal:
            problems.append(fatal.rstrip("."))
        problems += accent_problems
        self._restore_cursor(cursor)
        # The wallpaper follows the chosen mode even if the colour scheme had a problem.
        wp_ok, wp_message = self.set_wallpaper(self.theme_wallpaper(mode), remember=False)
        if not wp_ok:
            problems.append(wp_message)
            if before:
                self.set_wallpaper(before, remember=False)
        problems = self._settle_icons(accent_id, problems)
        wp_note = t("theme_wallpaper_dark" if dark else "theme_wallpaper_light") if wp_ok else ""
        if not scheme_ok:
            return False, fatal.rstrip(".") + "." + wp_note
        message = t("theme_dark_applied" if dark else "theme_light_applied") + wp_note
        return True, message + self._partial(problems)

    def _settle_icons(self, accent_id: str, problems: list[str]) -> list[str]:
        """Last step: make sure the accent's icon theme is really the active one."""
        accent = next((a for a in ACCENTS if a["id"] == accent_id), None)
        if accent is None or not self.icon_theme_valid(accent["icons"]):
            return problems
        icons = accent["icons"]
        unconfirmed = t("icons_unconfirmed", name=icons)
        if self._icons_match(icons) and unconfirmed not in problems:
            return problems
        self.env.sleep(1.0)
        if self._icons_match(icons) or self._apply_icons(icons):
            return [p for p in problems if p != unconfirmed]
        return problems

    def set_accent(self, accent_id: str) -> tuple[bool, str]:
        accent = next((a for a in ACCENTS if a["id"] == accent_id), None)
        if accent is None:
            return False, t("accent_invalid")
        fatal, problems = self._apply_accent(accent_id, self.is_dark())
        if fatal:
            return False, fatal
        name = accent_name(accent)
        if problems:
            return True, t("accent_applied_partial", name=name) + self._partial(problems)
        return True, t("accent_applied", name=name)

    def set_visual_style(self, style: str) -> tuple[bool, str]:
        if style not in VISUAL_STYLES:
            return False, t("style_invalid")
        dark = self.is_dark()
        accent_id = self.accent_id()
        cursor = self.current_cursor()
        wallpaper = self.current_wallpaper()
        ok, message = self._apply_lnf(style, dark)
        if not ok:
            return False, message
        # Global themes bring their own colours, icons, cursor and wallpaper: keep the user's choices.
        fatal, problems = self._apply_accent(accent_id, dark)
        if fatal:
            problems = [fatal.rstrip(".")]
        self._restore_cursor(cursor)
        if wallpaper and self.current_wallpaper() != wallpaper:
            self.set_wallpaper(wallpaper, remember=False)
        problems = self._settle_icons(accent_id, problems)
        return True, t("style_applied", name=style_label(style)) + self._partial(problems)

    # -- wallpapers --------------------------------------------------------------
    def theme_wallpaper(self, mode: str) -> str:
        return str(self.env.share / "wallpapers" / THEME_WALLPAPERS[mode])

    def current_wallpaper(self) -> str:
        """First wallpaper configured in the Plasma desktop containments."""
        try:
            text = self.env.appletsrc.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return self.read_state().get("wallpaper", "")
        section = ""
        for raw in text.splitlines():
            line = raw.strip()
            if line.startswith("[") and line.endswith("]"):
                section = line
            elif line.startswith("Image=") and section.endswith("[Wallpaper][org.kde.image][General]"):
                value = line[len("Image="):].strip()
                if value.startswith("file:"):
                    value = unquote(urlparse(value).path)
                return value
        return self.read_state().get("wallpaper", "")

    def set_wallpaper(self, path: str, remember: bool = True) -> tuple[bool, str]:
        target = Path(path)
        if not target.is_file() or target.suffix.lower() not in IMAGE_EXTENSIONS:
            return False, t("wallpaper_invalid", name=target.name or path)
        tool = self.env.find_tool("plasma-apply-wallpaperimage")
        if tool is None:
            return False, t("no_wallpaper_tool")
        rc, out, err = self.env.run([tool, str(target)], timeout=60)
        if rc != 0:
            detail = _detail(err, out)
            return False, t("wallpaper_failed") + (f": {detail}" if detail else "")
        self.write_state(wallpaper=str(target))
        return True, ""

    def list_wallpapers(self) -> list[dict]:
        return list_wallpapers(self.env)

    def add_wallpaper(self, source: str) -> tuple[bool, str]:
        src = Path(source)
        if not src.is_file():
            return False, t("add_not_found", name=src.name)
        if src.suffix.lower() not in IMAGE_EXTENSIONS:
            return False, t("add_bad_format", name=src.name)
        try:
            size = src.stat().st_size
        except OSError:
            return False, t("add_unreadable", name=src.name)
        if size <= 0 or size > MAX_USER_IMAGE_BYTES:
            return False, t("add_bad_size", name=src.name)
        folder = self.env.user_wallpapers
        try:
            folder.mkdir(parents=True, exist_ok=True)
            stem = re.sub(r"[^\w.\- ]", "_", src.stem)[:80] or "wallpaper"
            dest = folder / f"{stem}{src.suffix.lower()}"
            counter = 2
            while dest.exists():
                dest = folder / f"{stem}-{counter}{src.suffix.lower()}"
                counter += 1
            shutil.copyfile(src, dest)
        except OSError as exc:
            return False, t("add_copy_failed", name=src.name, reason=exc.strerror or exc)
        return True, str(dest)

    def remove_wallpaper(self, path: str) -> tuple[bool, str]:
        target = Path(path)
        try:
            inside = target.resolve().parent == self.env.user_wallpapers.resolve()
        except OSError:
            inside = False
        if not inside or not target.is_file():
            return False, t("remove_only_own")
        try:
            target.unlink()
        except OSError as exc:
            return False, t("remove_failed", reason=exc.strerror or exc)
        return True, t("removed", name=target.name)


# --------------------------------------------------------------------------- #
# Wallpaper discovery
# --------------------------------------------------------------------------- #

def _package_image(package: Path) -> Optional[Path]:
    """Largest image of a KDE wallpaper package (contents/images/WxH.ext)."""
    images = package / "contents" / "images"
    best: Optional[tuple[int, Path]] = None
    try:
        files = list(images.iterdir())
    except OSError:
        return None
    for item in files:
        if item.suffix.lower() not in IMAGE_EXTENSIONS or not item.is_file():
            continue
        match = re.match(r"(\d+)x(\d+)", item.stem)
        score = int(match.group(1)) * int(match.group(2)) if match else 1
        if best is None or score > best[0]:
            best = (score, item)
    return best[1] if best else None


def _package_name(package: Path) -> str:
    try:
        meta = json.loads((package / "metadata.json").read_text(encoding="utf-8"))
        name = meta.get("KPlugin", {}).get("Name")
        if isinstance(name, str) and name:
            return name
    except (OSError, ValueError):
        pass
    return package.name


def _pretty(name: str) -> str:
    return re.sub(r"[_\-]+", " ", name).strip() or name


def list_wallpapers(env: Env) -> list[dict]:
    """Wallpapers installed with the system plus the ones added by the user."""
    seen: set[str] = set()
    result: list[dict] = []

    def add(path: Path, name: str, source: str, package: Optional[Path] = None, thumb: Optional[Path] = None):
        try:
            key = str(path.resolve())
        except OSError:
            return
        if key in seen or len(result) >= MAX_WALLPAPERS:
            return
        seen.add(key)
        result.append({"path": str(path), "name": name, "source": source,
                       "thumb": str(thumb or path), "match": [str(path)] + ([str(package)] if package else []),
                       "removable": source == "user"})

    # 1. Mainuan wallpapers bundled with this app.
    for mode, key in (("dark", "wp_name_dark"), ("light", "wp_name_light")):
        path = env.share / "wallpapers" / THEME_WALLPAPERS[mode]
        if path.is_file():
            add(path, t(key), "mainuan")
    # 2. Images added by the user.
    try:
        for item in sorted(env.user_wallpapers.iterdir(), key=lambda p: p.name.lower()):
            if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS:
                add(item, _pretty(item.stem), "user")
    except OSError:
        pass
    # 3. System wallpapers: KDE packages and loose images.
    roots: list[Path] = [base / "wallpapers" for base in env.data_dirs]
    roots.append(Path("/usr/share/backgrounds"))
    for root in roots:
        try:
            entries = sorted(root.iterdir(), key=lambda p: p.name.lower())
        except OSError:
            continue
        for entry in entries:
            if entry.is_dir() and (entry / "contents").is_dir():
                image = _package_image(entry)
                if image is not None:
                    shot = entry / "contents" / "screenshot.png"
                    add(image, _package_name(entry), "system", package=entry,
                        thumb=shot if shot.is_file() else image)
            elif entry.is_file() and entry.suffix.lower() in IMAGE_EXTENSIONS:
                add(entry, _pretty(entry.stem), "system")
            elif entry.is_dir():
                try:
                    inner = sorted(entry.iterdir(), key=lambda p: p.name.lower())
                except OSError:
                    continue
                for item in inner:
                    if item.is_file() and item.suffix.lower() in IMAGE_EXTENSIONS:
                        add(item, _pretty(item.stem), "system")
    return result


# --------------------------------------------------------------------------- #
# Desktop layouts
# --------------------------------------------------------------------------- #

PLASMA_NAME = "org.kde.plasmashell"
UNSET_MARK = "__mainuan_unset__"
MAC_BUTTONS = {"left": "XIA", "right": ""}  # close, minimise, maximise on the left
SETTLE_ATTEMPTS = 8      # Plasma builds widgets asynchronously: look again before giving up


class Layouts:
    def __init__(self, env: Optional[Env] = None, appearance: Optional[Appearance] = None):
        self.env = env or Env()
        self.appearance = appearance or Appearance(self.env)
        self.positioning_delay = 2.0
        self.settle_delay = 1.0

    # -- D-Bus helpers -----------------------------------------------------------
    def _dbus(self, args: list[str], timeout: float = 60.0) -> tuple[int, str, str]:
        tool = self.env.find_tool("dbus-send")
        if tool is None:
            return 127, "", "dbus-send"
        return self.env.run([tool, "--session", "--print-reply", *args], timeout=timeout)

    def plasma_running(self) -> bool:
        rc, out, _ = self._dbus(["--dest=org.freedesktop.DBus", "/org/freedesktop/DBus",
                                 "org.freedesktop.DBus.NameHasOwner", f"string:{PLASMA_NAME}"], timeout=10)
        return rc == 0 and "boolean true" in out

    def available(self) -> bool:
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
        return ("KDE" in desktop.upper() or not desktop) and self.plasma_running()

    def installed_widgets(self) -> list[str]:
        found: set[str] = set()
        for base in self.env.data_dirs:
            root = base / "plasma" / "plasmoids"
            try:
                entries = list(root.iterdir())
            except OSError:
                continue
            for entry in entries:
                if not entry.is_dir():
                    continue
                found.add(entry.name)
                try:
                    meta = json.loads((entry / "metadata.json").read_text(encoding="utf-8"))
                    plugin_id = meta.get("KPlugin", {}).get("Id")
                    if isinstance(plugin_id, str) and plugin_id:
                        found.add(plugin_id)
                except (OSError, ValueError):
                    pass
        return sorted(found)

    def _script_source(self, call: str) -> str:
        layouts = self.env.share / "layouts"
        reference = (layouts / "reference-layouts.js").read_text(encoding="utf-8")
        desktop = (layouts / "desktop-layouts.js").read_text(encoding="utf-8")
        widgets = "var installedWidgets = " + json.dumps(self.installed_widgets()) + ";\n"
        return widgets + reference + "\n" + desktop + "\n" + call + "\n"

    def evaluate(self, call: str, timeout: float = 90.0) -> tuple[bool, str]:
        try:
            script = self._script_source(call)
        except OSError:
            return False, t("layout_scripts_failed")
        rc, out, err = self._dbus(["--dest=" + PLASMA_NAME, "/PlasmaShell",
                                   "org.kde.PlasmaShell.evaluateScript", "string:" + script], timeout=timeout)
        if rc != 0:
            return False, err.strip() or t("plasma_no_answer")
        return True, out

    @staticmethod
    def _json_in(text: str, key: str) -> Optional[dict]:
        for match in re.finditer(r"\{[^{}]*\}", text):
            try:
                value = json.loads(match.group(0))
            except ValueError:
                continue
            if isinstance(value, dict) and key in value:
                return value
        return None

    # -- queries -----------------------------------------------------------------
    def describe_full(self) -> tuple[bool, str, dict]:
        """(plasma answered, active layout id or '', raw description)."""
        ok, out = self.evaluate("describeMainuanLayout();", timeout=30)
        if not ok:
            return False, "", {}
        info = self._json_in(out, "layout") or {}
        active = str(info.get("layout", "")) if info.get("structureOk") is True else ""
        return True, active, info

    def describe(self) -> tuple[bool, str]:
        ok, active, _ = self.describe_full()
        return ok, active

    @property
    def has_backup(self) -> bool:
        return (self.env.backup_dir / "previous.appletsrc").is_file()

    # -- backup / restore --------------------------------------------------------
    def _backup(self, current_layout: str) -> bool:
        try:
            self.env.backup_dir.mkdir(parents=True, exist_ok=True)
            if self.env.appletsrc.is_file():
                tmp = self.env.backup_dir / "previous.appletsrc.tmp"
                shutil.copyfile(self.env.appletsrc, tmp)
                os.replace(tmp, self.env.backup_dir / "previous.appletsrc")
            meta = {"layout": current_layout, "saved": int(time.time())}
            (self.env.backup_dir / "previous.json").write_text(json.dumps(meta), encoding="utf-8")
            return True
        except OSError:
            return False

    def _wait_plasma(self, running: bool, timeout: float) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.plasma_running() == running:
                return True
            self.env.sleep(0.5)
        return self.plasma_running() == running

    def _restart_plasma_with_backup(self) -> bool:
        backup = self.env.backup_dir / "previous.appletsrc"
        if not backup.is_file():
            return False
        stopped = self.env.run(["systemctl", "--user", "stop", "plasma-plasmashell.service"], timeout=30)[0] == 0
        if not stopped:
            quitter = self.env.find_tool("kquitapp6")
            if quitter:
                self.env.run([quitter, "plasmashell"], timeout=20)
        self._wait_plasma(False, 12)
        try:
            tmp = self.env.appletsrc.with_suffix(".mainuan-tmp")
            shutil.copyfile(backup, tmp)
            os.replace(tmp, self.env.appletsrc)
        except OSError:
            return False
        started = self.env.run(["systemctl", "--user", "start", "plasma-plasmashell.service"], timeout=30)[0] == 0
        if not started:
            launcher = self.env.find_tool("kstart") or self.env.find_tool("plasmashell")
            if launcher:
                args = [launcher, "plasmashell"] if launcher.endswith("kstart") else [launcher]
                try:
                    subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     start_new_session=True)
                except OSError:
                    return False
        return self._wait_plasma(True, 30)

    def restore_backup(self) -> tuple[bool, str]:
        if not self.has_backup:
            return False, t("restore_none")
        previous = ""
        try:
            previous = json.loads((self.env.backup_dir / "previous.json").read_text(encoding="utf-8")).get("layout", "")
        except (OSError, ValueError):
            pass
        if not self._restart_plasma_with_backup():
            return False, t("restore_failed")
        self._sync_window_buttons(previous)
        return True, t("restore_ok")

    # -- window buttons (macOS style only moves the buttons, not the window theme) --
    def _kconfig(self, tool: str, *args: str) -> tuple[int, str, str]:
        path = self.env.find_tool(tool)
        if path is None:
            return 127, "", tool
        return self.env.run([path, *args], timeout=15)

    def _read_button(self, key: str) -> Optional[str]:
        rc, out, _ = self._kconfig("kreadconfig6", "--file", "kwinrc", "--group", "org.kde.kdecoration2",
                                   "--key", key, "--default", UNSET_MARK)
        if rc != 0:
            return None
        value = out.rstrip("\n")
        return None if value == UNSET_MARK else value

    def _write_button(self, key: str, value: Optional[str]) -> bool:
        base = ["--file", "kwinrc", "--group", "org.kde.kdecoration2", "--key", key]
        rc, _, _ = self._kconfig("kwriteconfig6", *(base + ["--delete"] if value is None else base + [value]))
        return rc == 0

    def _kwin_reconfigure(self) -> None:
        self._dbus(["--dest=org.kde.KWin", "/KWin", "org.kde.KWin.reconfigure"], timeout=15)

    def _sync_window_buttons(self, layout_id: str) -> Optional[str]:
        """macOS style: buttons on the left. Any other layout: put back what the user had."""
        state = self.appearance.read_state()
        saved = state.get("mac_buttons")
        if layout_id == "macos":
            if not saved:
                saved = {"left": self._read_button("ButtonsOnLeft"), "right": self._read_button("ButtonsOnRight")}
                self.appearance.write_state(mac_buttons=saved)
            ok = self._write_button("ButtonsOnLeft", MAC_BUTTONS["left"]) and \
                self._write_button("ButtonsOnRight", MAC_BUTTONS["right"])
            self._kwin_reconfigure()
            return None if ok else t("note_buttons_left")
        if saved:
            ok = self._write_button("ButtonsOnLeft", saved.get("left")) and \
                self._write_button("ButtonsOnRight", saved.get("right"))
            self.appearance.write_state(mac_buttons=None)
            self._kwin_reconfigure()
            return None if ok else t("note_buttons_restore")
        return None

    # -- apply -------------------------------------------------------------------
    def _run_tiling_script(self) -> bool:
        script = self.env.share / "layouts" / "kwin-tiling.js"
        if not script.is_file():
            return False
        rc, out, _ = self._dbus(["--dest=org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.loadScript",
                                 f"string:{script}", "string:mainuan-aparencia-tiling"], timeout=20)
        match = re.search(r"int32\s+(-?\d+)", out)
        if rc != 0 or not match or int(match.group(1)) < 0:
            return False
        ident = match.group(1)
        ran = self._dbus(["--dest=org.kde.KWin", f"/Scripting/Script{ident}", "org.kde.kwin.Script.run"], timeout=20)[0] == 0
        self.env.sleep(0.5)
        self._dbus(["--dest=org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.unloadScript",
                    "string:mainuan-aparencia-tiling"], timeout=20)
        return ran

    @staticmethod
    def _preflight_message(check: dict, name: str) -> str:
        code, detail = check.get("code"), str(check.get("detail") or "")
        if code == "launcher":
            return t("layout_launcher_missing", detail=detail)
        if code == "widget":
            return t("layout_widget_missing", detail=detail)
        if code == "noscreen":
            return t("layout_no_screen")
        if code == "geometry":
            return t("layout_geometry")
        if code == "invalid":
            return t("layout_invalid")
        return t("layout_cannot_apply", name=name, reason=str(check.get("message") or "?"))

    def _settle(self, layout_id: str) -> tuple[bool, dict]:
        """Plasma creates widgets asynchronously: look again a few times before judging the result."""
        info: dict = {}
        for attempt in range(SETTLE_ATTEMPTS):
            ok, active, info = self.describe_full()
            if ok and active == layout_id:
                return True, info
            if attempt < SETTLE_ATTEMPTS - 1:
                self.env.sleep(self.settle_delay)
        return False, info

    def apply(self, layout_id: str, progress: Callable[[str], None] = lambda _m: None) -> tuple[bool, str]:
        if layout_id not in LAYOUT_IDS:
            return False, t("layout_invalid")
        name = layout_name(layout_id)
        if not self.available():
            return False, t("no_plasma")
        progress(name)
        ok, out = self.evaluate(f'print(JSON.stringify(preflightMainuanLayout("{layout_id}")));', timeout=30)
        if not ok:
            return False, t("layout_cannot_apply", name=name, reason=out)
        check = self._json_in(out, "ok")
        if check is None:
            return False, t("layout_scripts_failed")
        if check.get("ok") is not True:
            return False, self._preflight_message(check, name)

        _, before = self.describe()
        if not self._backup(before):
            return False, t("layout_backup_failed")

        ok, out = self.evaluate(f'applyMainuanLayout("{layout_id}");')
        if not ok:
            return self._rollback(name, out)
        if "MAINUAN_PREFLIGHT_ERROR:" in out:
            tail = out.split("MAINUAN_PREFLIGHT_ERROR:", 1)[1].split('"')[0].strip()
            code, _, detail = tail.partition("|")
            return self._rollback(name, self._preflight_message({"code": code, "detail": detail}, name))

        notes: list[str] = []
        if layout_id == "tiling" and not self._run_tiling_script():
            notes.append(t("note_tiling"))

        if layout_id in ("plasma-default", "three-panels"):
            self.env.sleep(self.positioning_delay)
            ok, out = self.evaluate(f'print(JSON.stringify(positionMainuanLayout("{layout_id}")));', timeout=30)
            info = self._json_in(out, "ok") if ok else None
            if info is None or info.get("ok") is not True:
                return self._rollback(name, t("reason_nofit"))

        settled, info = self._settle(layout_id)
        if not settled:
            reason = t("reason_structure")
            if info.get("problems"):
                reason += f": {info['problems']}"
            return self._rollback(name, reason)

        button_problem = self._sync_window_buttons(layout_id)
        if button_problem:
            notes.append(button_problem)
        self.appearance.write_state(layout=layout_id)
        message = t("layout_applied", name=name)
        if layout_id == "tiling" and not notes:
            message += t("layout_tiling_hint")
        if notes:
            message += t("layout_notes", notes="; ".join(notes))
        return True, message

    def _rollback(self, name: str, reason: str) -> tuple[bool, str]:
        restored = self._restart_plasma_with_backup()
        text = t("layout_cannot_apply", name=name, reason=reason.rstrip("."))
        text += t("layout_restored_suffix") if restored else t("layout_restore_failed_suffix")
        return False, text
