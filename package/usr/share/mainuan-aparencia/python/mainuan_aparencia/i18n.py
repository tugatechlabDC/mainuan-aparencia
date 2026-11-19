"""Translations (pt-PT, pt-BR, fr, es, en). The language follows the system, never a setting.

Each entry is (pt-PT, en, fr, es) with an optional fifth item for pt-BR. pt-BR falls back
to pt-PT and any other missing text falls back to English.
"""
from __future__ import annotations

import os
from typing import Iterable, Optional

LANGS = ("pt-PT", "en", "fr", "es", "pt-BR")
_language = "en"


def normalize(tag: str) -> Optional[str]:
    """Map a locale tag (pt_BR.UTF-8, fr-CA, es_ES@euro...) to a supported language or None."""
    tag = tag.split(".")[0].split("@")[0].replace("-", "_").strip().lower()
    if tag in ("", "c", "posix"):
        return None
    lang, _, region = tag.partition("_")
    if lang == "pt":
        return "pt-BR" if region == "br" else "pt-PT"
    if lang in ("fr", "es", "en"):
        return lang
    return None


def detect(extra: Iterable[str] = (), environ=None) -> str:
    """First supported language of LANGUAGE, the Qt UI languages, LC_ALL, LC_MESSAGES and LANG."""
    env = os.environ if environ is None else environ
    candidates: list[str] = [item for item in env.get("LANGUAGE", "").split(":") if item]
    candidates += list(extra)
    candidates += [env.get(name, "") for name in ("LC_ALL", "LC_MESSAGES", "LANG")]
    for candidate in candidates:
        found = normalize(candidate)
        if found:
            return found
    return "en"


def set_language(lang: str) -> None:
    global _language
    _language = lang if lang in LANGS else "en"


def language() -> str:
    return _language


def t(key: str, **kw) -> str:
    entry = TABLE.get(key)
    if entry is None:
        return key
    pt, en, fr, es = entry[:4]
    pt_br = entry[4] if len(entry) > 4 else None
    text = {"pt-PT": pt, "en": en, "fr": fr, "es": es, "pt-BR": pt_br or pt}.get(_language) or en
    if kw:
        try:
            return text.format(**kw)
        except (KeyError, IndexError):
            return text
    return text


def tf(key: str, args) -> str:
    """Positional version for QML: {0}, {1}..."""
    text = t(key)
    try:
        return text.format(*[str(a) for a in (args or [])])
    except (KeyError, IndexError):
        return text


TABLE: dict[str, tuple] = {
    # ------------------------------------------------------------------ window / navigation
    "app_title": ("Mainuan Aparência", "Mainuan Appearance", "Mainuan Apparence", "Mainuan Apariencia"),
    "nav_appearance": ("Aparência", "Appearance", "Apparence", "Apariencia"),
    "nav_wallpaper": ("Wallpaper", "Wallpaper", "Fond d'écran", "Fondo de pantalla", "Papel de parede"),
    "nav_about": ("Sobre", "About", "À propos", "Acerca de"),
    "sidebar_expand": ("Expandir menu", "Expand menu", "Développer le menu", "Expandir menú"),
    "sidebar_collapse": ("Reduzir menu", "Collapse menu", "Réduire le menu", "Contraer menú"),
    "close_busy_appearance": (
        "Aguarde a aplicação da aparência terminar antes de fechar.",
        "Wait for the appearance to finish applying before closing.",
        "Attendez la fin de l'application de l'apparence avant de fermer.",
        "Espere a que termine de aplicarse la apariencia antes de cerrar."),
    "close_busy_layout": (
        "Aguarde a aplicação ou restauro do layout terminar antes de fechar.",
        "Wait for the layout to finish applying or restoring before closing.",
        "Attendez la fin de l'application ou de la restauration de la disposition avant de fermer.",
        "Espere a que termine de aplicarse o restaurarse la disposición antes de cerrar.",
        "Aguarde a aplicação ou restauração do layout terminar antes de fechar."),
    # ------------------------------------------------------------------ appearance page
    "appearance_intro": (
        "Personalize as cores, a transparência e a disposição da sua área de trabalho.",
        "Customize the colors, transparency and arrangement of your desktop.",
        "Personnalisez les couleurs, la transparence et la disposition de votre bureau.",
        "Personalice los colores, la transparencia y la disposición de su escritorio.",
        "Personalize as cores, a transparência e a disposição da sua área de trabalho."),
    "section_system": ("Aparência do sistema", "System appearance", "Apparence du système", "Apariencia del sistema"),
    "visual_style_title": ("Estilo visual", "Visual style", "Style visuel", "Estilo visual"),
    "visual_style_sub": (
        "Muda o estilo do Plasma e mantém a cor Mainuan e os ícones selecionados.",
        "Changes the Plasma style and keeps the selected Mainuan color and icons.",
        "Change le style de Plasma et conserve la couleur Mainuan et les icônes choisies.",
        "Cambia el estilo de Plasma y mantiene el color Mainuan y los iconos seleccionados."),
    "visual_style_unavailable": (
        "Disponível apenas no KDE Plasma.", "Only available on KDE Plasma.",
        "Disponible uniquement sous KDE Plasma.", "Disponible solo en KDE Plasma."),
    "style_blur": ("Desfocado", "Blurred", "Flou", "Desenfocado"),
    "style_blur_tip": (
        "Tema Dream: painéis translúcidos com desfoque", "Dream theme: translucent panels with blur",
        "Thème Dream : panneaux translucides avec flou", "Tema Dream: paneles translúcidos con desenfoque"),
    "style_glass": ("Vítreo", "Glass", "Verre", "Cristal"),
    "style_glass_tip": (
        "Tema Tahoe: painéis claros com efeito de vidro", "Tahoe theme: light panels with a glass effect",
        "Thème Tahoe : panneaux clairs à effet verre", "Tema Tahoe: paneles claros con efecto cristal"),
    "style_solid": ("Sólido", "Solid", "Plein", "Sólido"),
    "style_solid_tip": (
        "Tema Breeze: o visual padrão do KDE, sem transparência",
        "Breeze theme: the default KDE look, without transparency",
        "Thème Breeze : l'apparence par défaut de KDE, sans transparence",
        "Tema Breeze: el aspecto predeterminado de KDE, sin transparencia"),
    "theme_title": ("Tema do sistema", "System theme", "Thème du système", "Tema del sistema"),
    "theme_sub": (
        "Cores claras ou escuras em todo o sistema. O wallpaper Mainuan muda junto: escuro no modo escuro, claro no modo claro.",
        "Light or dark colors across the system. The Mainuan wallpaper changes with it: dark in dark mode, light in light mode.",
        "Couleurs claires ou sombres pour tout le système. Le fond d'écran Mainuan change aussi : sombre en mode sombre, clair en mode clair.",
        "Colores claros u oscuros en todo el sistema. El fondo Mainuan cambia con ellos: oscuro en modo oscuro, claro en modo claro.",
        "Cores claras ou escuras em todo o sistema. O papel de parede Mainuan muda junto: escuro no modo escuro, claro no modo claro."),
    "theme_light": ("Claro", "Light", "Clair", "Claro"),
    "theme_dark": ("Escuro", "Dark", "Sombre", "Oscuro"),
    "accent_title": ("Cor de destaque", "Accent color", "Couleur d'accentuation", "Color de énfasis"),
    "accent_sub": (
        "Aplica o esquema KDE e os ícones Kora. Mantém a escolha ao trocar estilo ou tema.",
        "Applies the KDE color scheme and the Kora icons. The choice is kept when changing style or theme.",
        "Applique le jeu de couleurs KDE et les icônes Kora. Le choix est conservé en changeant de style ou de thème.",
        "Aplica el esquema de colores de KDE y los iconos Kora. La elección se mantiene al cambiar de estilo o tema."),
    "accent_aria": ("Cor de destaque ", "Accent color ", "Couleur d'accentuation ", "Color de énfasis "),
    "layout_section": ("Layout do desktop", "Desktop layout", "Disposition du bureau", "Disposición del escritorio"),
    "layout_intro_ok": (
        "Escolha como os painéis ficam no ecrã. Antes de cada troca é guardada uma cópia do layout atual. Os estilos macOS e Windows 11 só mudam os painéis.",
        "Choose how the panels are arranged on screen. A copy of the current layout is saved before each change. The macOS and Windows 11 styles only change the panels.",
        "Choisissez la disposition des panneaux à l'écran. Une copie de la disposition actuelle est enregistrée avant chaque changement. Les styles macOS et Windows 11 ne modifient que les panneaux.",
        "Elija cómo se organizan los paneles en la pantalla. Antes de cada cambio se guarda una copia de la disposición actual. Los estilos macOS y Windows 11 solo cambian los paneles.",
        "Escolha como os painéis ficam na tela. Antes de cada troca é guardada uma cópia do layout atual. Os estilos macOS e Windows 11 só mudam os painéis."),
    "layout_intro_unavailable": (
        "Os layouts só podem ser aplicados dentro de uma sessão do KDE Plasma.",
        "Layouts can only be applied inside a KDE Plasma session.",
        "Les dispositions ne peuvent être appliquées que dans une session KDE Plasma.",
        "Las disposiciones solo se pueden aplicar dentro de una sesión de KDE Plasma."),
    "in_use": ("Em uso", "In use", "Utilisé", "En uso"),
    "applied": ("Aplicado", "Applied", "Appliqué", "Aplicado"),
    "apply": ("Aplicar", "Apply", "Appliquer", "Aplicar"),
    "apply_layout_aria": ("Aplicar layout ", "Apply layout ", "Appliquer la disposition ", "Aplicar la disposición "),
    "layout_in_use_aria": ("Layout em uso: ", "Layout in use: ", "Disposition utilisée : ", "Disposición en uso: "),
    "restore_hint": (
        "Volta ao layout que estava em uso antes da última troca. O Plasma é reiniciado por alguns segundos.",
        "Goes back to the layout that was in use before the last change. Plasma restarts for a few seconds.",
        "Revient à la disposition utilisée avant le dernier changement. Plasma redémarre pendant quelques secondes.",
        "Vuelve a la disposición que se usaba antes del último cambio. Plasma se reinicia durante unos segundos.",
        "Volta ao layout que estava em uso antes da última troca. O Plasma é reiniciado por alguns segundos."),
    "restore_button": ("Restaurar layout anterior", "Restore previous layout", "Restaurer la disposition précédente", "Restaurar disposición anterior"),
    "restore_title": ("Restaurar layout anterior?", "Restore previous layout?", "Restaurer la disposition précédente ?", "¿Restaurar la disposición anterior?"),
    "restore_subtitle": (
        "Os painéis voltam a ser como estavam antes da última troca de layout. O Plasma será reiniciado por alguns segundos.",
        "The panels go back to how they were before the last layout change. Plasma will restart for a few seconds.",
        "Les panneaux reviennent à leur état avant le dernier changement de disposition. Plasma redémarrera pendant quelques secondes.",
        "Los paneles vuelven a como estaban antes del último cambio de disposición. Plasma se reiniciará durante unos segundos."),
    "restore": ("Restaurar", "Restore", "Restaurer", "Restaurar"),
    "cancel": ("Cancelar", "Cancel", "Annuler", "Cancelar"),
    # ------------------------------------------------------------------ wallpaper page
    "wp_intro": (
        "Escolha o wallpaper do ambiente de trabalho entre as imagens do sistema ou adicione as suas. Ao mudar o tema do sistema, o Mainuan Escuro ou o Mainuan Claro é aplicado automaticamente.",
        "Choose the desktop wallpaper from the system images or add your own. When you change the system theme, Mainuan Dark or Mainuan Light is applied automatically.",
        "Choisissez le fond d'écran du bureau parmi les images du système ou ajoutez les vôtres. En changeant le thème du système, Mainuan Sombre ou Mainuan Clair est appliqué automatiquement.",
        "Elija el fondo del escritorio entre las imágenes del sistema o añada las suyas. Al cambiar el tema del sistema, se aplica automáticamente Mainuan Oscuro o Mainuan Claro.",
        "Escolha o papel de parede da área de trabalho entre as imagens do sistema ou adicione as suas. Ao mudar o tema do sistema, o Mainuan Escuro ou o Mainuan Claro é aplicado automaticamente."),
    "wp_add": ("Adicionar imagem…", "Add image…", "Ajouter une image…", "Añadir imagen…"),
    "wp_add_hint": (
        "Escolhe imagens do computador para usar como wallpaper", "Choose images from your computer to use as wallpaper",
        "Choisissez des images de votre ordinateur à utiliser comme fond d'écran",
        "Elija imágenes de su equipo para usarlas como fondo",
        "Escolhe imagens do computador para usar como papel de parede"),
    "wp_refresh": ("Atualizar lista", "Refresh list", "Actualiser la liste", "Actualizar lista"),
    "wp_count_one": ("{0} imagem", "{0} image", "{0} image", "{0} imagen"),
    "wp_count_many": ("{0} imagens", "{0} images", "{0} images", "{0} imágenes"),
    "wp_empty": (
        "Nenhuma imagem encontrada. Use «Adicionar imagem…» para escolher uma.",
        "No images found. Use “Add image…” to choose one.",
        "Aucune image trouvée. Utilisez « Ajouter une image… » pour en choisir une.",
        "No se encontraron imágenes. Use «Añadir imagen…» para elegir una."),
    "wp_source_mainuan": ("Mainuan", "Mainuan", "Mainuan", "Mainuan"),
    "wp_source_user": ("Adicionada por si", "Added by you", "Ajoutée par vous", "Añadida por usted"),
    "wp_source_system": ("Sistema", "System", "Système", "Sistema"),
    "wp_name_dark": ("Mainuan Escuro", "Mainuan Dark", "Mainuan Sombre", "Mainuan Oscuro"),
    "wp_name_light": ("Mainuan Claro", "Mainuan Light", "Mainuan Clair", "Mainuan Claro"),
    "wp_current_aria": ("Wallpaper em uso: ", "Wallpaper in use: ", "Fond d'écran utilisé : ", "Fondo en uso: ", "Papel de parede em uso: "),
    "wp_apply_aria": ("Aplicar wallpaper ", "Apply wallpaper ", "Appliquer le fond d'écran ", "Aplicar el fondo ", "Aplicar papel de parede "),
    "wp_remove_aria": ("Remover ", "Remove ", "Supprimer ", "Quitar "),
    "wp_remove_tip": ("Remover da lista", "Remove from the list", "Retirer de la liste", "Quitar de la lista"),
    "wp_remove_title": ("Remover imagem?", "Remove image?", "Supprimer l'image ?", "¿Quitar la imagen?"),
    "wp_remove_sub": (
        "A cópia «{0}» adicionada por si será apagada da lista. O ficheiro original não é alterado.",
        "The copy “{0}” you added will be deleted from the list. The original file is not changed.",
        "La copie « {0} » que vous avez ajoutée sera supprimée de la liste. Le fichier d'origine n'est pas modifié.",
        "La copia «{0}» que añadió se eliminará de la lista. El archivo original no se modifica.",
        "A cópia «{0}» adicionada por você será apagada da lista. O arquivo original não é alterado."),
    "remove": ("Remover", "Remove", "Supprimer", "Quitar"),
    "wp_dialog_title": (
        "Escolha imagens para o wallpaper", "Choose images for the wallpaper",
        "Choisissez des images pour le fond d'écran", "Elija imágenes para el fondo",
        "Escolha imagens para o papel de parede"),
    "wp_filter_images": ("Imagens", "Images", "Images", "Imágenes"),
    "wp_filter_all": ("Todos os ficheiros", "All files", "Tous les fichiers", "Todos los archivos", "Todos os arquivos"),
    # ------------------------------------------------------------------ about page
    "about_subtitle": (
        "Aparência e personalização da distribuição Mainuan",
        "Appearance and customization for the Mainuan distribution",
        "Apparence et personnalisation de la distribution Mainuan",
        "Apariencia y personalización de la distribución Mainuan"),
    "about_version": ("Versão", "Version", "Version", "Versión"),
    "about_copyright": ("Direitos de autor", "Copyright", "Droits d'auteur", "Derechos de autor", "Direitos autorais"),
    "about_license": ("Licença", "License", "Licence", "Licencia"),
    "about_license_text": (
        "Licença Pública Geral GNU, versão 3 ou posterior",
        "GNU General Public License, version 3 or later",
        "Licence publique générale GNU, version 3 ou ultérieure",
        "Licencia Pública General de GNU, versión 3 o posterior"),
    "about_author": ("Autor", "Author", "Auteur", "Autor"),
    "about_translator": ("Tradutor", "Translator", "Traducteur", "Traductor"),
    # ------------------------------------------------------------------ accents
    "accent_brown": ("Castanho", "Brown", "Marron", "Marrón", "Marrom"),
    "accent_cyan": ("Ciano", "Cyan", "Cyan", "Cian"),
    "accent_magenta": ("Magenta", "Magenta", "Magenta", "Magenta"),
    "accent_lime": ("Lima", "Lime", "Citron vert", "Lima"),
    "accent_gray": ("Cinzento", "Gray", "Gris", "Gris", "Cinza"),
    "accent_violet": ("Violeta", "Violet", "Violet", "Violeta"),
    # ------------------------------------------------------------------ layouts
    "layout_plasma-default_name": ("Mainuan", "Mainuan", "Mainuan", "Mainuan"),
    "layout_plasma-default_desc": (
        "O visual do Mainuan: ilhas flutuantes na base com menu, tarefas, bandeja e relógio.",
        "The Mainuan look: floating islands at the bottom with menu, tasks, tray and clock.",
        "L'apparence Mainuan : îlots flottants en bas avec menu, tâches, zone de notification et horloge.",
        "El aspecto Mainuan: islas flotantes en la base con menú, tareas, bandeja y reloj."),
    "layout_three-panels_name": ("3 barras", "3 bars", "3 barres", "3 barras"),
    "layout_three-panels_desc": (
        "Três segmentos flutuantes na base: menu e informações, tarefas e controlos do sistema.",
        "Three floating segments at the bottom: menu and information, tasks and system controls.",
        "Trois segments flottants en bas : menu et informations, tâches et contrôles du système.",
        "Tres segmentos flotantes en la base: menú e información, tareas y controles del sistema.",
        "Três segmentos flutuantes na base: menu e informações, tarefas e controles do sistema."),
    "layout_single-bar_name": ("Barra única", "Single bar", "Barre unique", "Barra única"),
    "layout_single-bar_desc": (
        "Uma barra inferior flutuante com margens laterais, widgets e aplicações fixadas.",
        "A floating bottom bar with side margins, widgets and pinned applications.",
        "Une barre inférieure flottante avec marges latérales, widgets et applications épinglées.",
        "Una barra inferior flotante con márgenes laterales, widgets y aplicaciones fijadas.",
        "Uma barra inferior flutuante com margens laterais, widgets e aplicativos fixados."),
    "layout_panel-top_name": ("Painel superior", "Top panel", "Panneau supérieur", "Panel superior"),
    "layout_panel-top_desc": (
        "Painel superior flutuante com TahoeLauncher, pesquisa, tarefas e controlos.",
        "Floating top panel with TahoeLauncher, search, tasks and controls.",
        "Panneau supérieur flottant avec TahoeLauncher, recherche, tâches et contrôles.",
        "Panel superior flotante con TahoeLauncher, búsqueda, tareas y controles.",
        "Painel superior flutuante com TahoeLauncher, pesquisa, tarefas e controles."),
    "layout_minimal_name": ("Barra W7", "W7 bar", "Barre W7", "Barra W7"),
    "layout_minimal_desc": (
        "Barra inferior de largura total, sem flutuação, com Kickoff e aplicações fixadas.",
        "Full-width bottom bar, not floating, with Kickoff and pinned applications.",
        "Barre inférieure pleine largeur, non flottante, avec Kickoff et applications épinglées.",
        "Barra inferior de ancho completo, sin flotación, con Kickoff y aplicaciones fijadas.",
        "Barra inferior de largura total, sem flutuação, com Kickoff e aplicativos fixados."),
    "layout_unity_name": ("Lomiri", "Lomiri", "Lomiri", "Lomiri"),
    "layout_unity_desc": (
        "Menu global no topo e painel vertical à esquerda com Orbit Start Menu.",
        "Global menu on top and a vertical panel on the left with Orbit Start Menu.",
        "Menu global en haut et panneau vertical à gauche avec Orbit Start Menu.",
        "Menú global arriba y panel vertical a la izquierda con Orbit Start Menu."),
    "layout_tiling_name": ("Tiling", "Tiling", "Mosaïque", "Mosaico"),
    "layout_tiling_desc": (
        "Barra compacta no topo e blocos do KWin para organizar as janelas lado a lado.",
        "Compact top bar and KWin tiles to arrange windows side by side.",
        "Barre compacte en haut et mosaïques KWin pour disposer les fenêtres côte à côte.",
        "Barra compacta arriba y mosaicos de KWin para organizar las ventanas una junto a otra."),
    "layout_macos_name": ("Estilo macOS", "macOS style", "Style macOS", "Estilo macOS"),
    "layout_macos_desc": (
        "Barra superior global, dock inferior centrada e botões de janela à esquerda. Não altera janelas, wallpaper, ícones nem cursor.",
        "Global top bar, centered bottom dock and window buttons on the left. Does not change windows, wallpaper, icons or cursor.",
        "Barre supérieure globale, dock inférieur centré et boutons de fenêtre à gauche. Ne modifie ni les fenêtres, ni le fond d'écran, ni les icônes, ni le curseur.",
        "Barra superior global, dock inferior centrado y botones de ventana a la izquierda. No cambia ventanas, fondo, iconos ni cursor.",
        "Barra superior global, dock inferior centralizada e botões de janela à esquerda. Não altera janelas, papel de parede, ícones nem cursor."),
    "layout_windows11_name": ("Estilo Windows 11", "Windows 11 style", "Style Windows 11", "Estilo Windows 11"),
    "layout_windows11_desc": (
        "Painel inferior com os ícones centrados e menu iniciar moderno em grelha. Não altera janelas, wallpaper, ícones nem cursor.",
        "Bottom panel with centered icons and a modern grid start menu. Does not change windows, wallpaper, icons or cursor.",
        "Panneau inférieur avec icônes centrées et menu démarrer moderne en grille. Ne modifie ni les fenêtres, ni le fond d'écran, ni les icônes, ni le curseur.",
        "Panel inferior con iconos centrados y menú de inicio moderno en cuadrícula. No cambia ventanas, fondo, iconos ni cursor.",
        "Painel inferior com os ícones centralizados e menu iniciar moderno em grade. Não altera janelas, papel de parede, ícones nem cursor."),
    # ------------------------------------------------------------------ messages (backend)
    "busy": ("Aguarde a operação atual terminar.", "Wait for the current operation to finish.",
             "Attendez la fin de l'opération en cours.", "Espere a que termine la operación actual."),
    "msg_applying_theme": ("A aplicar o tema…", "Applying theme…", "Application du thème…", "Aplicando el tema…", "Aplicando o tema…"),
    "msg_applying_accent": ("A aplicar a cor…", "Applying color…", "Application de la couleur…", "Aplicando el color…", "Aplicando a cor…"),
    "msg_applying_style": ("A aplicar o estilo…", "Applying style…", "Application du style…", "Aplicando el estilo…", "Aplicando o estilo…"),
    "msg_applying_wallpaper": ("A aplicar o wallpaper…", "Applying wallpaper…", "Application du fond d'écran…", "Aplicando el fondo…", "Aplicando o papel de parede…"),
    "msg_applying_layout": ("A aplicar o layout {name}…", "Applying layout {name}…", "Application de la disposition {name}…", "Aplicando la disposición {name}…", "Aplicando o layout {name}…"),
    "msg_restoring": (
        "A restaurar o layout anterior; o Plasma será reiniciado…",
        "Restoring the previous layout; Plasma will restart…",
        "Restauration de la disposition précédente ; Plasma va redémarrer…",
        "Restaurando la disposición anterior; Plasma se reiniciará…",
        "Restaurando o layout anterior; o Plasma será reiniciado…"),
    "theme_invalid": ("Tema inválido.", "Invalid theme.", "Thème invalide.", "Tema no válido."),
    "accent_invalid": ("Cor de destaque inválida.", "Invalid accent color.", "Couleur d'accentuation invalide.", "Color de énfasis no válido."),
    "style_invalid": ("Estilo visual inválido.", "Invalid visual style.", "Style visuel invalide.", "Estilo visual no válido."),
    "theme_dark_applied": ("Tema escuro aplicado.", "Dark theme applied.", "Thème sombre appliqué.", "Tema oscuro aplicado."),
    "theme_light_applied": ("Tema claro aplicado.", "Light theme applied.", "Thème clair appliqué.", "Tema claro aplicado."),
    "theme_wallpaper_dark": (" Wallpaper Mainuan Escuro aplicado.", " Mainuan Dark wallpaper applied.", " Fond d'écran Mainuan Sombre appliqué.", " Fondo Mainuan Oscuro aplicado.", " Papel de parede Mainuan Escuro aplicado."),
    "theme_wallpaper_light": (" Wallpaper Mainuan Claro aplicado.", " Mainuan Light wallpaper applied.", " Fond d'écran Mainuan Clair appliqué.", " Fondo Mainuan Claro aplicado.", " Papel de parede Mainuan Claro aplicado."),
    "partial": (
        " Não foi possível concluir todos os ajustes: {details}.",
        " Not all adjustments could be completed: {details}.",
        " Tous les réglages n'ont pas pu être terminés : {details}.",
        " No se pudieron completar todos los ajustes: {details}."),
    "accent_applied": ("Cor {name} e ícones aplicados.", "Color {name} and icons applied.", "Couleur {name} et icônes appliquées.", "Color {name} e iconos aplicados."),
    "accent_applied_partial": ("Cor {name} aplicada.", "Color {name} applied.", "Couleur {name} appliquée.", "Color {name} aplicado."),
    "style_applied": ("Estilo {name} aplicado.", "Style {name} applied.", "Style {name} appliqué.", "Estilo {name} aplicado."),
    "style_not_installed": (
        "O estilo {name} não está instalado neste sistema.", "The {name} style is not installed on this system.",
        "Le style {name} n'est pas installé sur ce système.", "El estilo {name} no está instalado en este sistema."),
    "no_lookandfeel": (
        "O Plasma deste sistema não oferece plasma-apply-lookandfeel; o estilo não pode ser trocado.",
        "This system's Plasma does not provide plasma-apply-lookandfeel; the style cannot be changed.",
        "Le Plasma de ce système ne fournit pas plasma-apply-lookandfeel ; le style ne peut pas être changé.",
        "El Plasma de este sistema no ofrece plasma-apply-lookandfeel; no se puede cambiar el estilo.",
        "O Plasma deste sistema não oferece plasma-apply-lookandfeel; o estilo não pode ser trocado."),
    "style_failed": ("Não foi possível aplicar o estilo {name}.", "Could not apply the {name} style.", "Impossible d'appliquer le style {name}.", "No se pudo aplicar el estilo {name}."),
    "scheme_missing": (
        "Esquema {scheme}.colors ausente ou ilegível.", "Color scheme {scheme}.colors is missing or unreadable.",
        "Le jeu de couleurs {scheme}.colors est absent ou illisible.", "El esquema {scheme}.colors falta o no se puede leer."),
    "scheme_unconfirmed": (
        "O Plasma não confirmou o esquema {scheme}.", "Plasma did not confirm the {scheme} scheme.",
        "Plasma n'a pas confirmé le jeu de couleurs {scheme}.", "Plasma no confirmó el esquema {scheme}."),
    "icons_missing": (
        "tema de ícones {name} ausente ou index.theme inválido (ícones anteriores preservados)",
        "icon theme {name} is missing or its index.theme is invalid (previous icons kept)",
        "thème d'icônes {name} absent ou index.theme invalide (icônes précédentes conservées)",
        "tema de iconos {name} ausente o index.theme no válido (se conservan los iconos anteriores)"),
    "icons_unconfirmed": ("o Plasma não confirmou os ícones {name}", "Plasma did not confirm the {name} icons", "Plasma n'a pas confirmé les icônes {name}", "Plasma no confirmó los iconos {name}"),
    "no_changeicons": ("plasma-changeicons não está disponível", "plasma-changeicons is not available", "plasma-changeicons n'est pas disponible", "plasma-changeicons no está disponible"),
    "wallpaper_invalid": ("wallpaper {name} ausente ou inválido", "wallpaper {name} is missing or invalid", "fond d'écran {name} absent ou invalide", "fondo {name} ausente o no válido", "papel de parede {name} ausente ou inválido"),
    "no_wallpaper_tool": ("plasma-apply-wallpaperimage não está disponível", "plasma-apply-wallpaperimage is not available", "plasma-apply-wallpaperimage n'est pas disponible", "plasma-apply-wallpaperimage no está disponible"),
    "wallpaper_failed": ("não foi possível aplicar o wallpaper", "could not apply the wallpaper", "impossible d'appliquer le fond d'écran", "no se pudo aplicar el fondo", "não foi possível aplicar o papel de parede"),
    "wallpaper_applied": ("Wallpaper aplicado.", "Wallpaper applied.", "Fond d'écran appliqué.", "Fondo aplicado.", "Papel de parede aplicado."),
    "wp_added_one": ("{n} imagem adicionada.", "{n} image added.", "{n} image ajoutée.", "{n} imagen añadida."),
    "wp_added_many": ("{n} imagens adicionadas.", "{n} images added.", "{n} images ajoutées.", "{n} imágenes añadidas."),
    "wp_not_added": (" Não adicionadas: {errors}", " Not added: {errors}", " Non ajoutées : {errors}", " No añadidas: {errors}"),
    "add_not_found": ("{name}: ficheiro não encontrado.", "{name}: file not found.", "{name} : fichier introuvable.", "{name}: archivo no encontrado.", "{name}: arquivo não encontrado."),
    "add_bad_format": (
        "{name}: formato não suportado (use PNG, JPG, WEBP, BMP ou SVG).", "{name}: unsupported format (use PNG, JPG, WEBP, BMP or SVG).",
        "{name} : format non pris en charge (utilisez PNG, JPG, WEBP, BMP ou SVG).", "{name}: formato no admitido (use PNG, JPG, WEBP, BMP o SVG)."),
    "add_unreadable": ("{name}: não foi possível ler o ficheiro.", "{name}: could not read the file.", "{name} : impossible de lire le fichier.", "{name}: no se pudo leer el archivo.", "{name}: não foi possível ler o arquivo."),
    "add_bad_size": ("{name}: tamanho de imagem inválido.", "{name}: invalid image size.", "{name} : taille d'image invalide.", "{name}: tamaño de imagen no válido."),
    "add_copy_failed": ("{name}: não foi possível copiar ({reason}).", "{name}: could not copy ({reason}).", "{name} : copie impossible ({reason}).", "{name}: no se pudo copiar ({reason})."),
    "remove_only_own": ("Só é possível remover imagens adicionadas por si.", "Only images you added can be removed.", "Seules les images que vous avez ajoutées peuvent être supprimées.", "Solo se pueden quitar las imágenes que usted añadió.", "Só é possível remover imagens adicionadas por você."),
    "remove_failed": ("Não foi possível remover a imagem ({reason}).", "Could not remove the image ({reason}).", "Impossible de supprimer l'image ({reason}).", "No se pudo quitar la imagen ({reason})."),
    "removed": ("Imagem {name} removida.", "Image {name} removed.", "Image {name} supprimée.", "Imagen {name} quitada."),
    # layouts
    "layout_invalid": ("Layout inválido.", "Invalid layout.", "Disposition invalide.", "Disposición no válida."),
    "no_plasma": (
        "Os layouts só podem ser aplicados dentro de uma sessão do KDE Plasma.", "Layouts can only be applied inside a KDE Plasma session.",
        "Les dispositions ne peuvent être appliquées que dans une session KDE Plasma.", "Las disposiciones solo se pueden aplicar dentro de una sesión de KDE Plasma."),
    "plasma_no_answer": ("O Plasma não respondeu.", "Plasma did not respond.", "Plasma n'a pas répondu.", "Plasma no respondió."),
    "layout_launcher_missing": (
        "Lançador obrigatório ausente: {detail}. Os painéis anteriores foram preservados.",
        "Required launcher missing: {detail}. The previous panels were kept.",
        "Lanceur requis absent : {detail}. Les panneaux précédents ont été conservés.",
        "Falta el lanzador obligatorio: {detail}. Se conservaron los paneles anteriores."),
    "layout_widget_missing": (
        "Widget obrigatório ausente: {detail}. Os painéis anteriores foram preservados.",
        "Required widget missing: {detail}. The previous panels were kept.",
        "Widget requis absent : {detail}. Les panneaux précédents ont été conservés.",
        "Falta el widget obligatorio: {detail}. Se conservaron los paneles anteriores."),
    "layout_no_screen": ("Nenhum ecrã disponível no Plasma.", "No screen available in Plasma.", "Aucun écran disponible dans Plasma.", "No hay ninguna pantalla disponible en Plasma.", "Nenhuma tela disponível no Plasma."),
    "layout_geometry": ("Não foi possível consultar a geometria do ecrã.", "Could not query the screen geometry.", "Impossible d'obtenir la géométrie de l'écran.", "No se pudo consultar la geometría de la pantalla.", "Não foi possível consultar a geometria da tela."),
    "layout_cannot_apply": (
        "Não foi possível aplicar o layout {name} ({reason}).", "Could not apply the {name} layout ({reason}).",
        "Impossible d'appliquer la disposition {name} ({reason}).", "No se pudo aplicar la disposición {name} ({reason})."),
    "layout_restored_suffix": (" O layout anterior foi restaurado.", " The previous layout was restored.", " La disposition précédente a été restaurée.", " Se restauró la disposición anterior."),
    "layout_restore_failed_suffix": (
        " Não foi possível restaurar o layout anterior automaticamente.", " The previous layout could not be restored automatically.",
        " La disposition précédente n'a pas pu être restaurée automatiquement.", " No se pudo restaurar automáticamente la disposición anterior."),
    "layout_scripts_failed": (
        "Não foi possível carregar os scripts de layout; nada foi alterado.", "Could not load the layout scripts; nothing was changed.",
        "Impossible de charger les scripts de disposition ; rien n'a été modifié.", "No se pudieron cargar los scripts de disposición; no se cambió nada."),
    "layout_backup_failed": (
        "Não foi possível guardar uma cópia do layout atual; nada foi alterado.", "Could not save a copy of the current layout; nothing was changed.",
        "Impossible d'enregistrer une copie de la disposition actuelle ; rien n'a été modifié.", "No se pudo guardar una copia de la disposición actual; no se cambió nada."),
    "layout_applied": ("Layout {name} aplicado.", "Layout {name} applied.", "Disposition {name} appliquée.", "Disposición {name} aplicada."),
    "layout_tiling_hint": (
        " Arraste janelas com Shift premido para as encaixar nos blocos.", " Drag windows with Shift held to snap them into the tiles.",
        " Faites glisser les fenêtres en maintenant Maj pour les placer dans les mosaïques.", " Arrastre las ventanas con Mayús pulsada para encajarlas en los mosaicos.",
        " Arraste janelas com Shift pressionado para encaixá-las nos blocos."),
    "layout_notes": (" Atenção: {notes}.", " Note: {notes}.", " Attention : {notes}.", " Atención: {notes}."),
    "reason_structure": ("a estrutura dos painéis não foi confirmada", "the panel structure was not confirmed", "la structure des panneaux n'a pas été confirmée", "no se confirmó la estructura de los paneles"),
    "reason_nofit": (
        "os widgets não cabem no ecrã sem se sobreporem", "the widgets do not fit on the screen without overlapping",
        "les widgets ne tiennent pas à l'écran sans se chevaucher", "los widgets no caben en la pantalla sin superponerse",
        "os widgets não cabem na tela sem se sobreporem"),
    "note_tiling": ("os blocos do KWin não puderam ser configurados", "the KWin tiles could not be configured", "les mosaïques KWin n'ont pas pu être configurées", "no se pudieron configurar los mosaicos de KWin"),
    "note_buttons_left": ("não foi possível mover os botões de janela para a esquerda", "could not move the window buttons to the left", "impossible de déplacer les boutons de fenêtre à gauche", "no se pudieron mover los botones de ventana a la izquierda"),
    "note_buttons_restore": ("não foi possível repor a posição dos botões de janela", "could not restore the window button positions", "impossible de rétablir la position des boutons de fenêtre", "no se pudo restablecer la posición de los botones de ventana"),
    "restore_none": ("Não há cópia do layout atual; nada foi alterado.", "There is no copy of the layout; nothing was changed.", "Il n'y a pas de copie de la disposition ; rien n'a été modifié.", "No hay copia de la disposición; no se cambió nada."),
    "restore_failed": ("Não foi possível restaurar o layout anterior.", "Could not restore the previous layout.", "Impossible de restaurer la disposition précédente.", "No se pudo restaurar la disposición anterior."),
    "restore_ok": ("Layout anterior restaurado.", "Previous layout restored.", "Disposition précédente restaurée.", "Disposición anterior restaurada."),
    "problem_details": ("detalhe", "details", "détails", "detalles"),
}
