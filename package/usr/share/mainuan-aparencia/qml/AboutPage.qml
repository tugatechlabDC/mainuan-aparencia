import QtQuick
import QtQuick.Controls as Controls
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

// About page: same information as the reference app, with this app's name, icon and version.
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

    readonly property string licenseUrl: "https://www.gnu.org/licenses/gpl-3.0.html"

    title: i18n.t("nav_about")
    padding: 0
    background: Rectangle { color: page.pageColor }

    component Field: ColumnLayout {
        property string label: ""
        property string value: ""
        property string link: ""
        Layout.alignment: Qt.AlignHCenter
        spacing: 2
        Controls.Label {
            Layout.alignment: Qt.AlignHCenter
            text: parent.label.toUpperCase()
            color: page.mutedColor
            font.pixelSize: 11
            font.letterSpacing: 0.8
        }
        Controls.Label {
            Layout.alignment: Qt.AlignHCenter
            text: parent.value
            color: page.textColor
            horizontalAlignment: Text.AlignHCenter
            wrapMode: Text.WordWrap
        }
        Controls.Label {
            visible: parent.link.length > 0
            Layout.alignment: Qt.AlignHCenter
            text: parent.link
            color: page.accent
            font.underline: true
            font.pixelSize: 12
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: Qt.openUrlExternally(parent.text)
            }
            Accessible.role: Accessible.Link
            Accessible.name: parent.link
        }
    }

    Controls.ScrollView {
        id: scroll
        anchors.fill: parent
        clip: true
        contentWidth: availableWidth

        ColumnLayout {
            width: scroll.availableWidth
            spacing: 14

            Item { Layout.preferredHeight: 28 }

            Image {
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 96
                Layout.preferredHeight: 96
                source: page.system.logoSource
                sourceSize.width: 192
                sourceSize.height: 192
                fillMode: Image.PreserveAspectFit
                smooth: true
                mipmap: true
                Accessible.role: Accessible.Graphic
                Accessible.name: i18n.t("app_title")
            }

            Kirigami.Heading {
                Layout.alignment: Qt.AlignHCenter
                text: i18n.t("app_title")
                level: 1
                font.weight: Font.Bold
                color: page.textColor
            }
            Controls.Label {
                Layout.alignment: Qt.AlignHCenter
                Layout.maximumWidth: 520
                text: i18n.t("about_subtitle")
                color: page.mutedColor
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }

            Item { Layout.preferredHeight: 6 }

            Field { label: i18n.t("about_version"); value: page.system.appVersion }
            Field { label: i18n.t("about_copyright"); value: "© 2026 David Caixinha" }
            Field { label: i18n.t("about_license"); value: i18n.t("about_license_text"); link: page.licenseUrl }
            Field { label: i18n.t("about_author"); value: "David Caixinha" }
            Field { label: i18n.t("about_translator"); value: "David Caixinha" }

            Item { Layout.preferredHeight: 28 }
        }
    }
}
