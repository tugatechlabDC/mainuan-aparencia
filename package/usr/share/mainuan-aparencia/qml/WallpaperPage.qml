import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Dialogs as Dialogs
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.Page {
    id: page
    property var system
    property bool dark: false
    property color accent: "#3daee9"
    property color pageColor: "#f3f5f9"
    property color surfaceColor: "#ffffff"
    property color elevatedColor: "#f5f7fb"
    property color borderColor: "#d9deea"
    property color textColor: "#202532"
    property color mutedColor: "#697286"
    property color successColor: "#2da65a"

    // Wallpaper pending removal (confirmed in a dialog).
    property string pendingRemoval: ""
    property string pendingName: ""

    title: i18n.t("nav_wallpaper")
    padding: 0
    background: Rectangle { color: page.pageColor }
    onVisibleChanged: if (visible) page.system.refreshWallpapers()

    function isCurrent(entry) {
        const current = page.system.currentWallpaper;
        if (current.length === 0)
            return false;
        for (let i = 0; i < entry.match.length; ++i) {
            if (entry.match[i] === current || current.indexOf(entry.match[i] + "/") === 0)
                return true;
        }
        return false;
    }

    PageContainer {
        contentSpacing: 12

        Kirigami.Heading { text: i18n.t("nav_wallpaper"); level: 1 }
        Controls.Label {
            Layout.fillWidth: true
            text: i18n.t("wp_intro")
            color: page.mutedColor
            wrapMode: Text.WordWrap
        }

        MessageBanner {
            Layout.fillWidth: true
            text: page.system.lastMessage
            dark: page.dark
            accent: page.accent
            textColor: page.textColor
            error: page.system.lastMessageIsError
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.topMargin: 8
            spacing: 10
            Controls.Button {
                text: i18n.t("wp_add")
                icon.name: "list-add"
                enabled: !page.system.busy
                onClicked: fileDialog.open()
                Accessible.description: i18n.t("wp_add_hint")
            }
            Controls.Button {
                text: i18n.t("wp_refresh")
                icon.name: "view-refresh"
                onClicked: page.system.refreshWallpapers()
            }
            Item { Layout.fillWidth: true }
            Controls.Label {
                text: i18n.tf(page.system.wallpapers.length === 1 ? "wp_count_one" : "wp_count_many", [page.system.wallpapers.length])
                color: page.mutedColor
                font.pixelSize: 12
            }
        }

        Controls.Label {
            Layout.fillWidth: true
            visible: page.system.wallpapers.length === 0
            text: i18n.t("wp_empty")
            color: page.mutedColor
            wrapMode: Text.WordWrap
        }

        GridLayout {
            id: grid
            Layout.fillWidth: true
            readonly property int cardMinimum: 210
            columns: Math.max(1, Math.min(4, Math.floor((width + columnSpacing) / (cardMinimum + columnSpacing))))
            columnSpacing: 14
            rowSpacing: 14

            Repeater {
                model: page.system.wallpapers
                delegate: Rectangle {
                    id: card
                    required property var modelData
                    readonly property bool active: page.isCurrent(modelData)

                    Layout.fillWidth: true
                    Layout.preferredWidth: grid.cardMinimum
                    Layout.alignment: Qt.AlignTop
                    implicitHeight: cardColumn.implicitHeight + 20
                    radius: 14
                    color: page.surfaceColor
                    border.width: active ? 2 : 1
                    border.color: active ? page.accent
                                         : (cardHover.hovered ? Qt.rgba(page.accent.r, page.accent.g, page.accent.b, 0.45) : page.borderColor)
                    Behavior on border.color { ColorAnimation { duration: 120 } }
                    HoverHandler { id: cardHover }

                    ColumnLayout {
                        id: cardColumn
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 8

                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: width * 9 / 16
                            radius: 8
                            clip: true
                            color: Qt.rgba(page.accent.r, page.accent.g, page.accent.b, 0.14)
                            border.color: page.borderColor
                            Image {
                                anchors.fill: parent
                                anchors.margins: 1
                                source: card.modelData.thumbUrl
                                sourceSize.width: 480
                                sourceSize.height: 270
                                fillMode: Image.PreserveAspectCrop
                                asynchronous: true
                                smooth: true
                                Accessible.ignored: true
                            }
                            MouseArea {
                                anchors.fill: parent
                                enabled: !page.system.busy
                                cursorShape: Qt.PointingHandCursor
                                onClicked: page.system.setWallpaper(card.modelData.path)
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Controls.Label {
                                Layout.fillWidth: true
                                text: card.modelData.name
                                color: page.textColor
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Kirigami.Icon {
                                visible: card.active
                                Layout.preferredWidth: 16
                                Layout.preferredHeight: 16
                                source: "checkmark"
                                color: page.successColor
                                Accessible.ignored: true
                            }
                            Controls.Label {
                                visible: card.active
                                text: i18n.t("in_use")
                                color: page.successColor
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Controls.Label {
                                Layout.fillWidth: true
                                text: card.modelData.source === "mainuan" ? i18n.t("wp_source_mainuan")
                                      : (card.modelData.source === "user" ? i18n.t("wp_source_user") : i18n.t("wp_source_system"))
                                color: page.mutedColor
                                font.pixelSize: 12
                            }
                            Controls.Button {
                                visible: card.modelData.removable
                                flat: true
                                icon.name: "edit-delete"
                                enabled: !page.system.busy
                                onClicked: {
                                    page.pendingRemoval = card.modelData.path;
                                    page.pendingName = card.modelData.name;
                                    removeDialog.open();
                                }
                                Accessible.name: i18n.t("wp_remove_aria") + card.modelData.name
                                Controls.ToolTip.visible: hovered
                                Controls.ToolTip.text: i18n.t("wp_remove_tip")
                                Controls.ToolTip.delay: 400
                            }
                            Controls.Button {
                                text: card.active ? i18n.t("applied") : i18n.t("apply")
                                icon.name: card.active ? "checkmark" : "dialog-ok-apply"
                                enabled: !page.system.busy && !card.active
                                onClicked: page.system.setWallpaper(card.modelData.path)
                                Accessible.name: (card.active ? i18n.t("wp_current_aria") : i18n.t("wp_apply_aria")) + card.modelData.name
                            }
                        }
                    }
                }
            }
        }
    }

    Dialogs.FileDialog {
        id: fileDialog
        title: i18n.t("wp_dialog_title")
        fileMode: Dialogs.FileDialog.OpenFiles
        nameFilters: [i18n.t("wp_filter_images") + " (*.png *.jpg *.jpeg *.webp *.bmp *.svg)", i18n.t("wp_filter_all") + " (*)"]
        onAccepted: page.system.addWallpapers(selectedFiles)
    }

    Kirigami.PromptDialog {
        id: removeDialog
        parent: page.Controls.Overlay.overlay
        preferredWidth: Kirigami.Units.gridUnit * 26
        title: i18n.t("wp_remove_title")
        subtitle: i18n.tf("wp_remove_sub", [page.pendingName])
        standardButtons: Kirigami.Dialog.NoButton
        customFooterActions: [
            Kirigami.Action {
                text: i18n.t("remove")
                icon.name: "edit-delete"
                onTriggered: {
                    removeDialog.close();
                    page.system.removeWallpaper(page.pendingRemoval);
                }
            },
            Kirigami.Action {
                text: i18n.t("cancel")
                icon.name: "dialog-cancel"
                onTriggered: removeDialog.close()
            }
        ]
    }
}
