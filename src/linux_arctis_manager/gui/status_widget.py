from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from linux_arctis_manager.i18n import I18n


class QStatusWidget(QWidget):
    main_layout: QVBoxLayout

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.main_layout = QVBoxLayout()
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(8)
        self.setLayout(self.main_layout)
    
    def clean_layout(self):
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def update_status(self, new_status: dict[str, dict[str, dict[str, str|int]]]):
        if hasattr(self, 'status') and new_status == self.status:
            return

        self.status = new_status

        self.clean_layout()
        if not self.status:
            label = QLabel(I18n.get_instance().translate('ui', 'no_device_detected'))
            label.setObjectName('mutedText')
            self.main_layout.addWidget(label)

            return

        for category, status_obj in self.status.items():
            group = QWidget()
            group.setObjectName('statusGroup')
            group_layout = QVBoxLayout()
            group_layout.setContentsMargins(10, 8, 10, 8)
            group_layout.setSpacing(6)
            group.setLayout(group_layout)

            category_label = QLabel(I18n.get_instance().translate('status', category))
            category_label.setObjectName('statusGroupTitle')
            group_layout.addWidget(category_label)

            for status, status_o in status_obj.items():
                row = QWidget()
                row_layout = QHBoxLayout()
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(12)
                row.setLayout(row_layout)

                label = QLabel(I18n.translate('status', status))
                label.setObjectName('statusKey')
                label.setWordWrap(True)
                row_layout.addWidget(label, 1)

                value = QLabel(
                    f"{I18n.translate('status_values', status_o['value'])}"
                    f"{'%' if status_o['type'] == 'percentage' else ''}"
                )
                value.setObjectName('statusValue')
                value.setWordWrap(True)
                row_layout.addWidget(value)

                group_layout.addWidget(row)

            self.main_layout.addWidget(group)
