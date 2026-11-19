import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.ApplicationWindow {
    id: root
    visible: true
    width: 1100
    height: 760
    minimumWidth: 760
    minimumHeight: 560
    // The title bar shows the name once; the application display name is not set on purpose.
    title: i18n.t("app_title")

    // The whole window follows the system light/dark mode. systemService watches the
    // KDE colour scheme, so changes made elsewhere (System Settings, day/night) apply too.
    property bool dark: systemService.darkTheme
    property color accent: systemService.accentColor.length > 0 ? systemService.accentColor : "#3daee9"
    // Explicit surfaces keep contrast stable on Plasma sessions whose QPA palette is not synchronised.
    property color pageColor: dark ? "#1b1f26" : "#f2f4f7"
    property color surfaceColor: dark ? "#242a33" : "#ffffff"
    property color elevatedColor: dark ? "#2d3440" : "#f7f8fa"
    property color borderColor: dark ? "#3d4653" : "#d6dbe3"
    property color textColor: dark ? "#f1f4f8" : "#20252d"
    property color mutedColor: dark ? "#aeb8c8" : "#657080"
    property color successColor: dark ? "#7fdda5" : "#258b4b"
    property color warningColor: dark ? "#f2c46d" : "#94600b"
    property color errorColor: dark ? "#ff8f87" : "#c0392b"
    property int currentPage: 0
    // Icons only by default; the menu button expands the labels.
    property bool sidebarExpanded: false
    property real sidebarWidth: sidebarExpanded ? 220 : 68
    Behavior on sidebarWidth { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }

    background: Rectangle {
        color: root.pageColor
        Behavior on color { ColorAnimation { duration: 180 } }
    }

    // Applying a theme or a layout cannot be interrupted safely.
    onClosing: (close) => {
        if (systemService.busy) {
            close.accepted = false;
            root.showPassiveNotification(i18n.t("close_busy_appearance"));
        } else if (layoutService.busy) {
            close.accepted = false;
            root.showPassiveNotification(i18n.t("close_busy_layout"));
        }
    }

    ListModel {
        id: navigationModel
        ListElement { key: "nav_appearance"; iconFile: "palette" }
        ListElement { key: "nav_wallpaper"; iconFile: "image" }
        ListElement { key: "nav_about"; iconFile: "info" }
    }

    RowLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            id: sidebar
            Layout.fillHeight: true
            Layout.preferredWidth: root.sidebarWidth
            color: root.dark ? "#20252d" : "#e7ebf1"
            border.color: root.borderColor
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 6

                // Expand / collapse the labels.
                SidebarButton {
                    Layout.fillWidth: true
                    collapsed: !root.sidebarExpanded
                    dark: root.dark
                    accent: root.accent
                    mutedColor: root.mutedColor
                    textColor: root.textColor
                    label: root.sidebarExpanded ? i18n.t("sidebar_collapse") : i18n.t("sidebar_expand")
                    iconFile: "menu"
                    onClicked: root.sidebarExpanded = !root.sidebarExpanded
                    Accessible.role: Accessible.Button
                    Accessible.description: root.sidebarExpanded ? i18n.t("sidebar_collapse") : i18n.t("sidebar_expand")
                }

                // App icon; a themed icon stands in if the file is missing.
                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 64
                    Layout.topMargin: 4
                    Layout.bottomMargin: 8
                    Image {
                        id: logo
                        anchors.centerIn: parent
                        width: 44
                        height: 44
                        source: systemService.logoSource
                        sourceSize.width: 128
                        sourceSize.height: 128
                        fillMode: Image.PreserveAspectFit
                        asynchronous: true
                        smooth: true
                        mipmap: true
                        visible: status === Image.Ready
                        Accessible.role: Accessible.Graphic
                        Accessible.name: i18n.t("app_title")
                    }
                    Kirigami.Icon {
                        anchors.centerIn: parent
                        width: 40
                        height: 40
                        visible: logo.status !== Image.Ready
                        source: "preferences-desktop-theme"
                        Accessible.name: i18n.t("app_title")
                    }
                }

                ListView {
                    id: navigation
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    model: navigationModel
                    spacing: 4
                    interactive: false
                    delegate: SidebarButton {
                        width: navigation.width
                        collapsed: !root.sidebarExpanded
                        dark: root.dark
                        accent: root.accent
                        mutedColor: root.mutedColor
                        textColor: root.textColor
                        label: i18n.t(model.key)
                        iconFile: model.iconFile
                        selected: root.currentPage === index
                        onClicked: root.currentPage = index
                    }
                }
            }
        }

        StackLayout {
            id: pages
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: root.currentPage

            AppearancePage {
                system: systemService; layouts: layoutModel; layoutManager: layoutService
                dark: root.dark; accent: root.accent; pageColor: root.pageColor; surfaceColor: root.surfaceColor
                elevatedColor: root.elevatedColor; borderColor: root.borderColor; textColor: root.textColor
                mutedColor: root.mutedColor; successColor: root.successColor
            }
            WallpaperPage {
                system: systemService
                dark: root.dark; accent: root.accent; pageColor: root.pageColor; surfaceColor: root.surfaceColor
                elevatedColor: root.elevatedColor; borderColor: root.borderColor; textColor: root.textColor
                mutedColor: root.mutedColor; successColor: root.successColor
            }
            AboutPage {
                system: systemService
                dark: root.dark; accent: root.accent; pageColor: root.pageColor; surfaceColor: root.surfaceColor
                elevatedColor: root.elevatedColor; borderColor: root.borderColor; textColor: root.textColor
                mutedColor: root.mutedColor; successColor: root.successColor
            }
        }
    }
}
