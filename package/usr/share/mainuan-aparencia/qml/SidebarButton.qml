import QtQuick
import QtQuick.Controls as Controls
import org.kde.kirigami as Kirigami

// Sidebar entry: line icon (qml/icons) drawn as a mask in the text/accent colour, plus a label.
Controls.Button {
    id: control

    property bool selected: false
    property bool collapsed: false
    property string label: ""
    property string iconFile: ""
    property bool dark: false
    property color accent: "#3daee9"
    property color mutedColor: "#697286"
    property color textColor: "#202532"

    readonly property int iconSize: 24

    implicitHeight: 46
    implicitWidth: collapsed ? 52 : 196
    text: collapsed ? "" : label
    display: collapsed ? Controls.AbstractButton.IconOnly : Controls.AbstractButton.TextBesideIcon
    leftPadding: collapsed ? (width - iconSize) / 2 : 16
    rightPadding: collapsed ? (width - iconSize) / 2 : 12
    Accessible.name: label
    Controls.ToolTip.visible: collapsed && hovered
    Controls.ToolTip.text: label

    background: Rectangle {
        radius: 10
        color: control.selected ? Qt.rgba(control.accent.r, control.accent.g, control.accent.b, control.dark ? 0.20 : 0.12)
                                : (control.hovered ? Qt.rgba(1, 1, 1, control.dark ? 0.07 : 0.50) : "transparent")
        border.color: control.visualFocus ? control.accent
                    : (control.selected ? Qt.rgba(control.accent.r, control.accent.g, control.accent.b, 0.45) : "transparent")
        border.width: control.visualFocus ? 2 : (control.selected ? 1 : 0)

        // Accent bar on the selected entry.
        Rectangle {
            visible: control.selected
            width: 3
            height: parent.height * 0.5
            radius: 2
            anchors.left: parent.left
            anchors.leftMargin: 2
            anchors.verticalCenter: parent.verticalCenter
            color: control.accent
        }
    }

    contentItem: Row {
        spacing: 12
        anchors.fill: parent
        anchors.leftMargin: control.leftPadding
        anchors.rightMargin: control.rightPadding
        anchors.topMargin: 1
        anchors.bottomMargin: 1
        layoutDirection: Qt.LeftToRight

        Kirigami.Icon {
            width: control.iconSize
            height: control.iconSize
            anchors.verticalCenter: parent.verticalCenter
            source: Qt.resolvedUrl("icons/" + control.iconFile + ".svg")
            isMask: true
            color: control.selected ? control.accent : (control.hovered || control.visualFocus ? control.textColor : control.mutedColor)
            Behavior on color { ColorAnimation { duration: 120 } }
            Accessible.ignored: true
        }

        Controls.Label {
            visible: !control.collapsed
            width: parent.width - control.iconSize - 12
            anchors.verticalCenter: parent.verticalCenter
            text: control.label
            color: control.selected ? control.accent : control.textColor
            elide: Text.ElideRight
            font.weight: control.selected ? Font.DemiBold : Font.Normal
        }
    }
}
