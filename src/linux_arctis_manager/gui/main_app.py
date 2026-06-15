import logging
from typing import Literal

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
                               QLabel, QPushButton, QScrollArea, QSizePolicy,
                               QSlider, QStackedWidget, QVBoxLayout, QWidget)

from linux_arctis_manager.audio_endpoints import VIRTUAL_AUDIO_ENDPOINTS
from linux_arctis_manager.gui.base_app import QBaseDesktopApp
from linux_arctis_manager.gui.main_app_proto_widget import QMainAppProtoWidget
from linux_arctis_manager.gui.status_widget import QStatusWidget
from linux_arctis_manager.gui.ui_utils import get_icon_pixmap
from linux_arctis_manager.gui.view_models import dashboard_summary, demo_status, mixer_levels
from linux_arctis_manager.i18n import I18n

PanelName = Literal['dashboard', 'mixer', 'device', 'routing', 'profiles', 'settings']


class QMainApp(QBaseDesktopApp):
    app: QApplication
    main_window: QMainAppProtoWidget

    side_panel: QWidget
    main_panel: QWidget
    status_widget: QStatusWidget

    def __init__(self, app: QApplication, log_level: int, demo_mode: bool = False):
        super().__init__(parent=app)

        self.logger = logging.getLogger('QMainApp')
        self.logger.setLevel(log_level)

        self.app = app
        self.demo_mode = demo_mode
        self.settings = {}
        self.status = {}

        self.dbus_wrapper = None
        if not self.demo_mode:
            from linux_arctis_manager.gui.dbus_wrapper import DbusWrapper

            self.dbus_wrapper = DbusWrapper()
            self.dbus_wrapper.sig_settings.connect(self.on_settings_received)
            self.dbus_wrapper.sig_status.connect(self.on_status_received)

        self.main_window = self.main_window_setup()

        self.status_widget = QStatusWidget(self.dashboard_status_card)
        self.dashboard_status_card.layout().addWidget(self.status_widget)

        if self.dbus_wrapper:
            from linux_arctis_manager.gui.settings_widget import QSettingsWidget

            self.general_settings_widget = QSettingsWidget(self.settings_page, 'general', 'general')
            self.device_settings_widget = QSettingsWidget(self.device_settings_card, 'device', 'device')
            self.settings_page_content_layout.addWidget(self.general_settings_widget)
            self.device_settings_card.layout().addWidget(self.device_settings_widget)
            self.dbus_wrapper.sig_status.connect(self.status_widget.update_status)
            self.dbus_wrapper.sig_settings.connect(self.general_settings_widget.update_settings)
            self.dbus_wrapper.sig_settings.connect(self.device_settings_widget.update_settings)
        else:
            self.device_settings_card.layout().addWidget(self._muted_label('Demo mode uses sample status only. D-Bus device controls are hidden.'))

        self.switch_panel('dashboard')
        if self.dbus_wrapper:
            self.dbus_wrapper.start()
        else:
            status = demo_status()
            self.status_widget.update_status(status)
            self.on_status_received(status)
            self.service_status_label.setText('Demo mode - D-Bus disabled')

        self.destroyed.connect(self.sig_stop)

    def main_window_setup(self) -> QMainAppProtoWidget:
        window = QMainAppProtoWidget()

        window.setWindowFlags(Qt.WindowType.Window)
        window.setWindowTitle(I18n.get_instance().translate('ui', 'app_name'))
        window.setWindowIcon(QIcon(get_icon_pixmap()))
        window.setObjectName('mainWindow')
        window.setStyleSheet(self._stylesheet())

        window_layout = QHBoxLayout()
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)
        window.setLayout(window_layout)

        window.setMinimumSize(1040, 680)
        available_geometry = window.screen().availableGeometry()
        window.resize(min(1180, available_geometry.width()), min(760, available_geometry.height()))

        self.side_panel = self._build_side_panel()
        window_layout.addWidget(self.side_panel)

        self.main_panel = QWidget()
        self.main_panel.setObjectName('contentPanel')
        self.main_panel_layout = QVBoxLayout()
        self.main_panel_layout.setContentsMargins(28, 24, 28, 24)
        self.main_panel_layout.setSpacing(18)
        self.main_panel.setLayout(self.main_panel_layout)
        window_layout.addWidget(self.main_panel, 1)

        self.header_title = QLabel('Dashboard')
        self.header_title.setObjectName('pageTitle')
        self.header_subtitle = QLabel('Headset status, routing, profiles, and device controls.')
        self.header_subtitle.setObjectName('pageSubtitle')
        self.main_panel_layout.addWidget(self.header_title)
        self.main_panel_layout.addWidget(self.header_subtitle)

        self.stack = QStackedWidget()
        self.main_panel_layout.addWidget(self.stack, 1)

        self.pages: dict[PanelName, QWidget] = {
            'dashboard': self._build_dashboard_page(),
            'mixer': self._build_mixer_page(),
            'device': self._build_device_page(),
            'routing': self._build_routing_page(),
            'profiles': self._build_profiles_page(),
            'settings': self._build_settings_page(),
        }

        self.page_titles: dict[PanelName, tuple[str, str]] = {
            'dashboard': ('Dashboard', 'Current device health and active control surface.'),
            'mixer': ('Mixer', 'Multi-channel outputs for game, chat, media, aux, and microphone.'),
            'device': ('Device', 'Hardware controls exposed by the connected headset configuration.'),
            'routing': ('Routing', 'Virtual endpoints today, per-app routing prepared for native PipeWire work.'),
            'profiles': ('Profiles', 'Per-device profiles and future app-aware switching.'),
            'settings': ('Settings', 'Service setup, redirect behavior, license, and project information.'),
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        return window

    def _build_side_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName('sidePanel')
        panel.setFixedWidth(240)
        layout = QVBoxLayout()
        layout.setContentsMargins(18, 22, 18, 22)
        layout.setSpacing(8)
        panel.setLayout(layout)

        brand = QLabel(I18n.get_instance().translate('ui', 'app_name'))
        brand.setObjectName('brandTitle')
        layout.addWidget(brand)

        tagline = QLabel('Linux headset control')
        tagline.setObjectName('brandTagline')
        layout.addWidget(tagline)

        layout.addSpacing(20)

        self.nav_buttons: dict[PanelName, QPushButton] = {}
        nav_items: list[tuple[PanelName, str]] = [
            ('dashboard', 'Dashboard'),
            ('mixer', 'Mixer'),
            ('device', 'Device'),
            ('routing', 'Routing'),
            ('profiles', 'Profiles'),
            ('settings', 'Settings'),
        ]

        for panel_name, text in nav_items:
            button = QPushButton(text)
            button.setObjectName('navButton')
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _, name=panel_name: self.switch_panel(name))
            self.nav_buttons[panel_name] = button
            layout.addWidget(button)

        layout.addStretch(1)

        notice = QLabel('Unaffiliated community project')
        notice.setObjectName('sidebarNotice')
        notice.setWordWrap(True)
        layout.addWidget(notice)

        return panel

    def _build_dashboard_page(self) -> QWidget:
        page, layout = self._scroll_page()

        summary_grid = QGridLayout()
        summary_grid.setSpacing(14)
        layout.addLayout(summary_grid)

        self.dashboard_cards: dict[str, QLabel] = {}
        for index, (key, title, value) in enumerate([
            ('device', 'Device', 'No device detected'),
            ('battery', 'Battery', 'Unknown'),
            ('microphone', 'Microphone', 'Unknown'),
            ('outputs', 'Outputs', 'Game / Chat / Media / Aux'),
            ('profile', 'Profile', 'Default'),
        ]):
            card = self._summary_card(title, value)
            value_label = card.findChild(QLabel, 'summaryValue')
            if value_label is not None:
                self.dashboard_cards[key] = value_label
            summary_grid.addWidget(card, index // 2, index % 2)

        self.dashboard_status_card = self._card('Live Status')
        layout.addWidget(self.dashboard_status_card)

        return page

    def _build_mixer_page(self) -> QWidget:
        page, layout = self._scroll_page()

        self.mixer_sliders: dict[str, QSlider] = {}
        endpoint_grid = QGridLayout()
        endpoint_grid.setSpacing(14)
        layout.addLayout(endpoint_grid)

        for index, endpoint in enumerate(VIRTUAL_AUDIO_ENDPOINTS):
            card = self._card(endpoint.label)
            status = 'Planned' if not endpoint.implemented else ('Input source' if endpoint.kind == 'source' else 'Virtual output')
            card.layout().addWidget(self._muted_label(status))

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(0 if not endpoint.implemented else 100)
            slider.setEnabled(False)
            slider.setObjectName('mixerSlider')
            card.layout().addWidget(slider)
            self.mixer_sliders[endpoint.node_name] = slider

            hint = 'Controlled by ChatMix' if endpoint.mix_group == 'chat' else 'Controlled by media mix'
            if not endpoint.implemented:
                hint = 'Reserved for future microphone routing'
            card.layout().addWidget(self._muted_label(hint))
            endpoint_grid.addWidget(card, index // 2, index % 2)

        balance_card = self._card('ChatMix Balance')
        balance_card.layout().addWidget(self._muted_label(
            'Hardware ChatMix status updates Game/Media/Aux separately from Chat when supported.'
        ))
        layout.addWidget(balance_card)

        return page

    def _build_device_page(self) -> QWidget:
        page, layout = self._scroll_page()

        self.device_settings_card = self._card('Device Controls')
        self.device_settings_card.layout().addWidget(self._muted_label(
            'Controls appear when the connected headset exposes them over D-Bus.'
        ))
        layout.addWidget(self.device_settings_card)

        return page

    def _build_routing_page(self) -> QWidget:
        page, layout = self._scroll_page()

        route_grid = QGridLayout()
        route_grid.setSpacing(14)
        layout.addLayout(route_grid)

        for index, endpoint in enumerate(VIRTUAL_AUDIO_ENDPOINTS):
            card = self._card(endpoint.label)
            card.layout().addWidget(QLabel(endpoint.node_name))
            card.layout().addWidget(self._muted_label('Implemented' if endpoint.implemented else 'Planned'))
            card.layout().addWidget(self._muted_label('Output sink' if endpoint.kind == 'sink' else 'Input source'))
            route_grid.addWidget(card, index // 2, index % 2)

        planned = self._card('Per-App Routing')
        planned.layout().addWidget(self._muted_label(
            'Prepared for native PipeWire/WirePlumber integration. Applications are not moved yet.'
        ))
        planned.layout().addWidget(self._disabled_action('Assign app to endpoint - planned'))
        layout.addWidget(planned)

        return page

    def _build_profiles_page(self) -> QWidget:
        page, layout = self._scroll_page()

        current = self._card('Current Profile')
        current.layout().addWidget(QLabel('Default'))
        current.layout().addWidget(self._muted_label(
            'Per-device YAML settings are persisted today. Named profile save/load is planned.'
        ))
        profile_actions = QWidget()
        profile_action_layout = QHBoxLayout()
        profile_action_layout.setContentsMargins(0, 0, 0, 0)
        profile_actions.setLayout(profile_action_layout)
        profile_action_layout.addWidget(self._disabled_action('Save profile - planned'))
        profile_action_layout.addWidget(self._disabled_action('Load profile - planned'))
        current.layout().addWidget(profile_actions)
        layout.addWidget(current)

        future = self._card('Profile Automation')
        future.layout().addWidget(self._muted_label(
            'Future work: switch profiles by game, app, or output route.'
        ))
        layout.addWidget(future)

        return page

    def _build_settings_page(self) -> QWidget:
        page, layout = self._scroll_page()
        self.settings_page = page
        self.settings_page_content_layout = layout

        service = self._card('Service')
        self.service_status_label = QLabel('Waiting for D-Bus response')
        service.layout().addWidget(self.service_status_label)
        service.layout().addWidget(self._muted_label(
            'Run lam-cli setup if udev rules or the user service are missing.'
        ))
        layout.addWidget(service)

        about = self._card('About')
        about.layout().addWidget(QLabel('GPL-3.0 community headset manager for Linux.'))
        about.layout().addWidget(self._muted_label(
            'Unaffiliated with SteelSeries. Product names are used only for compatibility.'
        ))
        layout.addWidget(about)

        return page

    def _scroll_page(self) -> tuple[QWidget, QVBoxLayout]:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 8, 0)
        content_layout.setSpacing(16)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        content.setLayout(content_layout)
        scroll.setWidget(content)

        return scroll, content_layout

    def _card(self, title: str) -> QFrame:
        card = QFrame()
        card.setObjectName('card')
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout()
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        card.setLayout(layout)

        label = QLabel(title)
        label.setObjectName('cardTitle')
        layout.addWidget(label)

        return card

    def _summary_card(self, title: str, value: str) -> QFrame:
        card = self._card(title)
        value_label = QLabel(value)
        value_label.setObjectName('summaryValue')
        value_label.setWordWrap(True)
        card.layout().addWidget(value_label)
        return card

    def _muted_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName('mutedText')
        label.setWordWrap(True)
        return label

    def _disabled_action(self, text: str) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName('disabledAction')
        button.setEnabled(False)
        return button

    def switch_panel(self, panel: PanelName) -> None:
        self.stack.setCurrentWidget(self.pages[panel])
        title, subtitle = self.page_titles[panel]
        self.header_title.setText(title)
        self.header_subtitle.setText(subtitle)

        for name, button in self.nav_buttons.items():
            button.setChecked(name == panel)

    def start_sync(self):
        self.logger.info('Starting Main Window app.')
        self.main_window.show()

        self.app.exec()

    async def start(self):
        self.start_sync()

    def on_settings_received(self, settings):
        if settings == self.settings:
            return

        self.settings = settings
        self.service_status_label.setText('D-Bus settings connected')

    def on_status_received(self, status):
        if status == self.status:
            return

        self.status = status
        self.service_status_label.setText('D-Bus status connected')
        self._refresh_dashboard_status(status)
        self._refresh_mixer_status(status)

    def _refresh_dashboard_status(self, status: dict) -> None:
        for key, value in dashboard_summary(status).items():
            if key in self.dashboard_cards:
                self.dashboard_cards[key].setText(value)

    def _refresh_mixer_status(self, status: dict) -> None:
        for node_name, level in mixer_levels(status).items():
            slider = self.mixer_sliders.get(node_name)
            if not slider:
                continue
            slider.setValue(level)

    def _stylesheet(self) -> str:
        return '''
            #mainWindow {
                background: #0f1419;
                color: #edf2f7;
                font-family: "Noto Sans", "Segoe UI", "Inter", "Arial";
            }
            #sidePanel {
                background: #111922;
                border-right: 1px solid #263241;
            }
            #contentPanel {
                background: #0f1419;
            }
            #brandTitle {
                color: #f8fafc;
                font-size: 21px;
                font-weight: 700;
            }
            #brandTagline, #sidebarNotice, #pageSubtitle, #mutedText {
                color: #91a4b7;
            }
            #pageTitle {
                color: #f8fafc;
                font-size: 30px;
                font-weight: 700;
            }
            #pageSubtitle {
                font-size: 13px;
            }
            #navButton {
                background: transparent;
                border: 0;
                border-radius: 8px;
                color: #cbd5e1;
                font-size: 14px;
                padding: 10px 12px;
                text-align: left;
            }
            #navButton:hover {
                background: #1a2633;
            }
            #navButton:checked {
                background: #22425f;
                color: #ffffff;
            }
            #disabledAction {
                background: #1c2733;
                border: 1px solid #2e3c4d;
                border-radius: 8px;
                color: #7f92a5;
                padding: 8px 10px;
                text-align: left;
            }
            #card {
                background: #151d27;
                border: 1px solid #263241;
                border-radius: 8px;
            }
            #cardTitle {
                color: #f8fafc;
                font-size: 15px;
                font-weight: 700;
            }
            #summaryValue {
                color: #ffffff;
                font-size: 22px;
                font-weight: 700;
            }
            QLabel {
                color: #dbe7f3;
                font-size: 13px;
            }
            QScrollArea {
                background: transparent;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QSlider::groove:horizontal {
                background: #283545;
                border-radius: 4px;
                height: 8px;
            }
            QSlider::handle:horizontal {
                background: #5fb3f3;
                border-radius: 8px;
                height: 16px;
                margin: -4px 0;
                width: 16px;
            }
            QSlider::sub-page:horizontal {
                background: #5fb3f3;
                border-radius: 4px;
            }
        '''

    @Slot()
    def sig_stop(self):
        if hasattr(self, '_stopping') and self._stopping:
            return
        self._stopping = True

        if self.dbus_wrapper:
            self.dbus_wrapper.stop()

        self.logger.debug('Received shutdown signal, shutting down.')
        self.app.quit()
