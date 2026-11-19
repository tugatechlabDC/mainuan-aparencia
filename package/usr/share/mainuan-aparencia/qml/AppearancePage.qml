import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.Page {
    id: page
    property var system
    property var layouts
    property var layoutManager
    property bool dark: false
    property color accent: "#3daee9"
    property color pageColor: "#f3f5f9"
    property color surfaceColor: "#ffffff"
    property color elevatedColor: "#f5f7fb"
    property color borderColor: "#d9deea"
    property color textColor: "#202532"
    property color mutedColor: "#697286"
    property color successColor: "#2da65a"

    readonly property var accentPalette: page.system.accentProfiles

    title: i18n.t("nav_appearance")
    padding: 0
    background: Rectangle { color: page.pageColor }
    // Plasma may not have answered yet when the app starts at login.
    onVisibleChanged: if (visible && layoutManager && !layoutManager.busy) layoutManager.refresh()

    component Separator: Rectangle {
        Layout.fillWidth: true
        Layout.leftMargin: 54
        implicitHeight: 1
    }

    PageContainer {
        contentSpacing: 12

        Kirigami.Heading { text: i18n.t("nav_appearance"); level: 1 }
        Controls.Label {
            Layout.fillWidth: true
            text: i18n.t("appearance_intro")
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

        Controls.Label {
            Layout.topMargin: 12
            text: i18n.t("section_system")
            color: page.mutedColor
            font.pixelSize: 12
            font.weight: Font.DemiBold
            Accessible.role: Accessible.Heading
        }

        Rectangle {
            Layout.fillWidth: true
            implicitHeight: systemColumn.implicitHeight
            radius: 12
            color: page.surfaceColor
            border.color: page.borderColor

            ColumnLayout {
                id: systemColumn
                anchors.left: parent.left
                anchors.right: parent.right
                spacing: 0

                SettingRow {
                    Layout.fillWidth: true
                    title: i18n.t("visual_style_title")
                    subtitle: page.system.visualStyleAvailable
                              ? i18n.t("visual_style_sub")
                              : i18n.t("visual_style_unavailable")
                    iconName: "preferences-desktop-effects"
                    accent: page.accent; textColor: page.textColor; mutedColor: page.mutedColor
                    compactWidth: 720

                    SegmentedChoice {
                        enabled: page.system.visualStyleAvailable && !page.system.busy
                        groupName: i18n.t("visual_style_title")
                        current: page.system.visualStyle
                        availableValues: page.system.installedVisualStyles
                        options: [
                            { value: "blur", label: i18n.t("style_blur"), icon: "blur", tooltip: i18n.t("style_blur_tip") },
                            { value: "glass", label: i18n.t("style_glass"), icon: "window", tooltip: i18n.t("style_glass_tip") },
                            { value: "solid", label: i18n.t("style_solid"), icon: "object-fill", tooltip: i18n.t("style_solid_tip") }
                        ]
                        onActivated: (value) => page.system.setVisualStyle(value)
                    }
                }

                Separator { color: page.borderColor }

                SettingRow {
                    Layout.fillWidth: true
                    title: i18n.t("theme_title")
                    subtitle: i18n.t("theme_sub")
                    iconName: "preferences-desktop-theme"
                    accent: page.accent; textColor: page.textColor; mutedColor: page.mutedColor

                    SegmentedChoice {
                        enabled: !page.system.busy
                        groupName: i18n.t("theme_title")
                        current: page.dark ? "dark" : "light"
                        options: [
                            { value: "light", label: i18n.t("theme_light"), icon: "weather-clear" },
                            { value: "dark", label: i18n.t("theme_dark"), icon: "weather-clear-night" }
                        ]
                        onActivated: (value) => page.system.setTheme(value)
                    }
                }

                Separator { color: page.borderColor }

                SettingRow {
                    Layout.fillWidth: true
                    title: i18n.t("accent_title")
                    subtitle: i18n.t("accent_sub")
                    iconName: "color-picker"
                    accent: page.accent; textColor: page.textColor; mutedColor: page.mutedColor

                    Row {
                        spacing: 8
                        Accessible.role: Accessible.Grouping
                        Accessible.name: i18n.t("accent_title")
                        Repeater {
                            model: page.accentPalette
                            delegate: Controls.AbstractButton {
                                id: swatch
                                required property var modelData
                                readonly property bool selected: page.system.accentId === modelData.id
                                implicitWidth: 30
                                implicitHeight: 30
                                enabled: !page.system.busy
                                focusPolicy: Qt.StrongFocus
                                checkable: true
                                checked: selected
                                // As in SegmentedChoice: AT-SPI toggles `checked` without clicked().
                                onCheckedChanged: {
                                    if (checked === selected)
                                        return;
                                    const requested = checked;
                                    checked = Qt.binding(() => selected);
                                    if (requested)
                                        page.system.setAccent(modelData.id);
                                }
                                Accessible.role: Accessible.RadioButton
                                Accessible.name: i18n.t("accent_aria") + modelData.name
                                Controls.ToolTip.visible: hovered
                                Controls.ToolTip.text: modelData.name
                                Controls.ToolTip.delay: 400

                                background: Rectangle {
                                    radius: width / 2
                                    color: swatch.modelData.color
                                    opacity: swatch.enabled ? 1 : 0.5
                                    border.width: swatch.selected || swatch.visualFocus ? 2 : 1
                                    border.color: swatch.selected || swatch.visualFocus ? page.textColor
                                                                                        : Qt.rgba(0, 0, 0, 0.18)
                                    scale: swatch.hovered && !swatch.selected ? 1.08 : 1
                                    Behavior on scale { NumberAnimation { duration: 120 } }
                                }
                                contentItem: Kirigami.Icon {
                                    source: "checkmark"
                                    color: "#ffffff"
                                    visible: swatch.selected
                                    anchors.centerIn: parent
                                    width: 16
                                    height: 16
                                    Accessible.ignored: true
                                }
                            }
                        }
                    }
                }
            }
        }

        Controls.Label {
            Layout.topMargin: 16
            text: i18n.t("layout_section")
            color: page.mutedColor
            font.pixelSize: 12
            font.weight: Font.DemiBold
            Accessible.role: Accessible.Heading
        }
        Controls.Label {
            Layout.fillWidth: true
            text: page.layoutManager.available
                  ? i18n.t("layout_intro_ok")
                  : i18n.t("layout_intro_unavailable")
            color: page.mutedColor
            wrapMode: Text.WordWrap
        }

        MessageBanner {
            Layout.fillWidth: true
            text: page.layoutManager.message
            error: page.layoutManager.messageIsError
            dark: page.dark
            accent: page.accent
            textColor: page.textColor
        }

        GridLayout {
            id: layoutGrid
            Layout.fillWidth: true
            readonly property int cardMinimum: 240
            columns: Math.max(1, Math.min(3, Math.floor((width + columnSpacing) / (cardMinimum + columnSpacing))))
            columnSpacing: 14
            rowSpacing: 14

            Repeater {
                model: page.layouts
                delegate: Rectangle {
                    id: layoutCard
                    required property var modelData
                    readonly property string layoutId: modelData.layoutId
                    readonly property string name: modelData.name
                    readonly property string description: modelData.description
                    objectName: "layoutCard-" + layoutId
                    readonly property bool active: page.layoutManager.activeLayout === layoutId

                    Layout.fillWidth: true
                    Layout.fillHeight: true // cards of a row share one height
                    Layout.preferredWidth: layoutGrid.cardMinimum
                    implicitHeight: cardColumn.implicitHeight + 28
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
                        anchors.margins: 14
                        spacing: 8

                        LayoutPreview {
                            Layout.fillWidth: true
                            layoutId: layoutCard.layoutId
                            accent: page.accent
                            panelColor: page.dark ? "#d8dde6" : "#4f5a70"
                            borderColor: page.borderColor
                        }
                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            Controls.Label {
                                Layout.fillWidth: true
                                text: layoutCard.name
                                color: page.textColor
                                font.weight: Font.DemiBold
                                elide: Text.ElideRight
                            }
                            Kirigami.Icon {
                                visible: layoutCard.active
                                Layout.preferredWidth: 16
                                Layout.preferredHeight: 16
                                source: "checkmark"
                                color: page.successColor
                                Accessible.ignored: true
                            }
                            Controls.Label {
                                visible: layoutCard.active
                                text: i18n.t("in_use")
                                color: page.successColor
                                font.pixelSize: 12
                                font.weight: Font.DemiBold
                            }
                        }
                        Controls.Label {
                            Layout.fillWidth: true
                            Layout.preferredHeight: Math.max(implicitHeight, 3 * fontMetrics.height)
                            text: layoutCard.description
                            color: page.mutedColor
                            font.pixelSize: 12
                            wrapMode: Text.WordWrap
                            FontMetrics { id: fontMetrics; font.pixelSize: 12 }
                        }
                        Item { Layout.fillHeight: true }
                        Controls.Button {
                            objectName: "applyLayout-" + layoutCard.layoutId
                            Layout.alignment: Qt.AlignRight
                            text: layoutCard.active ? i18n.t("applied") : i18n.t("apply")
                            icon.name: layoutCard.active ? "checkmark" : "dialog-ok-apply"
                            enabled: page.layoutManager.available && !page.layoutManager.busy && !layoutCard.active
                            onClicked: page.layoutManager.apply(layoutCard.layoutId)
                            Accessible.name: (layoutCard.active ? i18n.t("layout_in_use_aria") : i18n.t("apply_layout_aria")) + layoutCard.name
                            Accessible.description: layoutCard.description
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            visible: page.layoutManager.hasBackup
            spacing: 10
            Controls.Label {
                Layout.fillWidth: true
                text: i18n.t("restore_hint")
                color: page.mutedColor
                font.pixelSize: 12
                wrapMode: Text.WordWrap
            }
            Controls.Button {
                text: i18n.t("restore_button")
                icon.name: "edit-undo"
                enabled: !page.layoutManager.busy
                onClicked: restoreDialog.open()
            }
        }
    }

    Kirigami.PromptDialog {
        id: restoreDialog
        parent: page.Controls.Overlay.overlay
        preferredWidth: Kirigami.Units.gridUnit * 28
        title: i18n.t("restore_title")
        subtitle: i18n.t("restore_subtitle")
        standardButtons: Kirigami.Dialog.NoButton
        customFooterActions: [
            Kirigami.Action {
                text: i18n.t("restore")
                icon.name: "edit-undo"
                onTriggered: {
                    restoreDialog.close();
                    page.layoutManager.restoreBackup();
                }
            },
            Kirigami.Action {
                text: i18n.t("cancel")
                icon.name: "dialog-cancel"
                onTriggered: restoreDialog.close()
            }
        ]
    }
}
