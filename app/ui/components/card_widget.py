"""
Modern Card Container Widget.
"""

from app.ui.qt_compat import QtWidgets, QtCore


class CardWidget(QtWidgets.QFrame):
    def __init__(self, title: str = "", subtitle: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 16, 16, 16)
        self.main_layout.setSpacing(12)

        if title or subtitle:
            hdr_layout = QtWidgets.QVBoxLayout()
            hdr_layout.setSpacing(2)
            if title:
                self.title_lbl = QtWidgets.QLabel(title)
                self.title_lbl.setObjectName("card_title")
                hdr_layout.addWidget(self.title_lbl)
            if subtitle:
                self.subtitle_lbl = QtWidgets.QLabel(subtitle)
                self.subtitle_lbl.setObjectName("card_subtitle")
                hdr_layout.addWidget(self.subtitle_lbl)
            self.main_layout.addLayout(hdr_layout)

    def add_widget(self, widget: QtWidgets.QWidget):
        self.main_layout.addWidget(widget)

    def add_layout(self, layout: QtWidgets.QLayout):
        self.main_layout.addLayout(layout)
