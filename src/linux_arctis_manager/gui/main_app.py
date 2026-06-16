import logging
from typing import Literal

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QComboBox, QFrame, QGridLayout,
                               QHBoxLayout, QLabel, QLineEdit, QPushButton,
                               QScrollArea, QSizePolicy, QSlider,
                               QStackedWidget, QVBoxLayout, QWidget)

from linux_arctis_manager.audio_endpoints import VIRTUAL_AUDIO_ENDPOINTS
from linux_arctis_manager.gui.base_app import QBaseDesktopApp
from linux_arctis_manager.gui.main_app_proto_widget import QMainAppProtoWidget
from linux_arctis_manager.gui.status_widget import QStatusWidget
from linux_arctis_manager.gui.ui_utils import get_icon_pixmap
from linux_arctis_manager.gui.view_models import (
    application_route_rows,
    chatmix_balance_summary,
    dashboard_control_surface_summary,
    dashboard_detail_summary,
    dashboard_settings_summary,
    dashboard_summary,
    demo_settings,
    demo_status,
    device_capability_summary,
    device_control_snapshot,
    endpoint_route_map,
    header_context_summary,
    mixer_levels,
    mixer_overview_summary,
    profile_app_context_summary,
    profile_workflow_summary,
    routing_overview_summary,
)
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
        self._refresh_header_context()
        self._refresh_profile_state({})
        self._refresh_profile_overview({})
        self._refresh_profile_app_context({})
        self._refresh_device_capability_state({})
        self._refresh_device_control_snapshot({})
        self._refresh_routing_overview({})
        self._refresh_routing_state({})
        self._refresh_route_map({})
        self._refresh_mixer_overview({})
        self._refresh_mixer_settings({})
        self._refresh_application_routes({})
        self._refresh_dashboard_settings({})
        self._refresh_dashboard_control_surface()

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
            self.device_settings_card.layout().addWidget(self._muted_label(
                'Demo mode uses sample metadata for the overview. Live device controls need the D-Bus service.'
            ))

        self.switch_panel('dashboard')
        if self.dbus_wrapper:
            self.dbus_wrapper.start()
        else:
            self.on_settings_received(demo_settings())
            status = demo_status()
            self.status_widget.update_status(status)
            self.on_status_received(status)
            self._set_service_status(
                'Demo mode - D-Bus disabled',
                'Demo mode previews the redesigned GUI without touching the user service or headset.',
                'Demo',
            )

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

        window.setMinimumSize(960, 640)
        available_geometry = window.screen().availableGeometry()
        window.resize(min(1120, available_geometry.width()), min(720, available_geometry.height()))

        self.side_panel = self._build_side_panel()
        window_layout.addWidget(self.side_panel)

        self.main_panel = QWidget()
        self.main_panel.setObjectName('contentPanel')
        self.main_panel_layout = QVBoxLayout()
        self.main_panel_layout.setContentsMargins(22, 20, 22, 20)
        self.main_panel_layout.setSpacing(16)
        self.main_panel.setLayout(self.main_panel_layout)
        window_layout.addWidget(self.main_panel, 1)

        self.header_title = QLabel('Dashboard')
        self.header_title.setObjectName('pageTitle')
        self.header_subtitle = QLabel('Headset status, routing, profiles, and device controls.')
        self.header_subtitle.setObjectName('pageSubtitle')
        self.main_panel_layout.addWidget(self.header_title)
        self.main_panel_layout.addWidget(self.header_subtitle)

        self.header_context_values: dict[str, QLabel] = {}
        context_bar = QWidget()
        context_bar.setObjectName('headerContextBar')
        context_layout = QHBoxLayout()
        context_layout.setContentsMargins(0, 0, 0, 0)
        context_layout.setSpacing(8)
        context_bar.setLayout(context_layout)
        for key, title, value in [
            ('device', 'Device', 'No device detected'),
            ('battery', 'Battery', 'Unknown'),
            ('profile', 'Profile', 'Default'),
            ('outputs', 'Outputs', 'Game / Chat / Media / Aux'),
        ]:
            chip = self._header_chip(title, value)
            value_label = chip.findChild(QLabel, 'headerChipValue')
            if value_label is not None:
                self.header_context_values[key] = value_label
            context_layout.addWidget(chip, 1)
        self.main_panel_layout.addWidget(context_bar)

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
        panel.setFixedWidth(220)
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 20, 16, 20)
        layout.setSpacing(7)
        panel.setLayout(layout)

        brand = QLabel(I18n.get_instance().translate('ui', 'app_name'))
        brand.setObjectName('brandTitle')
        layout.addWidget(brand)

        tagline = QLabel('Linux headset control')
        tagline.setObjectName('brandTagline')
        layout.addWidget(tagline)

        layout.addSpacing(18)

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
        self.dashboard_card_details: dict[str, QLabel] = {}
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
            detail_label = card.findChild(QLabel, 'summaryDetail')
            if detail_label is not None:
                self.dashboard_card_details[key] = detail_label
            summary_grid.addWidget(card, index // 2, index % 2)

        control_surface = self._card('Control Surface')
        self.dashboard_control_state_labels: dict[str, QLabel] = {}
        self.dashboard_control_detail_labels: dict[str, QLabel] = {}
        for item in dashboard_control_surface_summary({}, {}):
            row = self._setup_step_row(
                item['title'],
                item['state'],
                item['detail'],
            )
            control_surface.layout().addWidget(row)
            self.dashboard_control_state_labels[item['key']] = row.findChild(QLabel, 'setupState')
            self.dashboard_control_detail_labels[item['key']] = row.findChild(QLabel, 'mutedText')
        layout.addWidget(control_surface)

        quick_controls = self._card('Quick Controls')
        quick_actions = QWidget()
        quick_actions_layout = QHBoxLayout()
        quick_actions_layout.setContentsMargins(0, 0, 0, 0)
        quick_actions_layout.setSpacing(8)
        quick_actions.setLayout(quick_actions_layout)

        self.dashboard_action_buttons: dict[PanelName, QPushButton] = {}
        for panel_name, text in [
            ('mixer', 'Open Mixer'),
            ('routing', 'Open Routing'),
            ('profiles', 'Open Profiles'),
            ('settings', 'Open Setup'),
        ]:
            button = QPushButton(text)
            button.setObjectName('secondaryAction')
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _, name=panel_name: self.switch_panel(name))
            quick_actions_layout.addWidget(button)
            self.dashboard_action_buttons[panel_name] = button

        quick_controls.layout().addWidget(quick_actions)
        layout.addWidget(quick_controls)

        self.dashboard_status_card = self._card('Live Status')
        layout.addWidget(self.dashboard_status_card)

        return page

    def _build_mixer_page(self) -> QWidget:
        page, layout = self._scroll_page()

        overview_grid = QGridLayout()
        overview_grid.setSpacing(14)
        layout.addLayout(overview_grid)

        self.mixer_overview_value_labels: dict[str, QLabel] = {}
        self.mixer_overview_detail_labels: dict[str, QLabel] = {}
        for index, (key, title) in enumerate([
            ('channels', 'Channel State'),
            ('media', 'Media Mix Group'),
            ('chat', 'Chat Mix Group'),
        ]):
            card = self._card(title)

            value_label = QLabel()
            value_label.setObjectName('endpointState')
            self._set_state_label(value_label, 'Waiting')
            card.layout().addWidget(value_label)
            self.mixer_overview_value_labels[key] = value_label

            detail_label = self._muted_label('Waiting for mixer metadata.')
            card.layout().addWidget(detail_label)
            self.mixer_overview_detail_labels[key] = detail_label

            overview_grid.addWidget(card, index // 2, index % 2)

        self.mixer_sliders: dict[str, QSlider] = {}
        self.mixer_value_labels: dict[str, QLabel] = {}
        self.mixer_state_labels: dict[str, QLabel] = {}
        self.mixer_detail_labels: dict[str, QLabel] = {}
        endpoint_grid = QGridLayout()
        endpoint_grid.setSpacing(14)
        layout.addLayout(endpoint_grid)

        for index, endpoint in enumerate(VIRTUAL_AUDIO_ENDPOINTS):
            card = self._card(endpoint.label)

            meter_row = QWidget()
            meter_row_layout = QHBoxLayout()
            meter_row_layout.setContentsMargins(0, 0, 0, 0)
            meter_row_layout.setSpacing(8)
            meter_row.setLayout(meter_row_layout)

            state_label = QLabel()
            state_label.setObjectName('endpointState')
            self._set_state_label(state_label, 'Planned' if not endpoint.implemented else 'Waiting')
            meter_row_layout.addWidget(state_label)
            self.mixer_state_labels[endpoint.node_name] = state_label

            meter_row_layout.addStretch(1)

            value_label = QLabel('0%' if not endpoint.implemented else '100%')
            value_label.setObjectName('mixerValue')
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            meter_row_layout.addWidget(value_label)
            self.mixer_value_labels[endpoint.node_name] = value_label

            card.layout().addWidget(meter_row)

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
            detail_label = self._muted_label(hint)
            card.layout().addWidget(detail_label)
            self.mixer_detail_labels[endpoint.node_name] = detail_label
            endpoint_grid.addWidget(card, index // 2, index % 2)

        balance_card = self._card('ChatMix Balance')
        self.chatmix_balance_value_label = QLabel('Waiting')
        self.chatmix_balance_value_label.setObjectName('mixerValue')
        balance_card.layout().addWidget(self.chatmix_balance_value_label)

        self.chatmix_media_balance_slider = self._readonly_meter('Game / Media / Aux')
        balance_card.layout().addWidget(self.chatmix_media_balance_slider)

        self.chatmix_chat_balance_slider = self._readonly_meter('Chat')
        balance_card.layout().addWidget(self.chatmix_chat_balance_slider)

        self.chatmix_balance_detail_label = self._muted_label(
            'Hardware ChatMix status updates Game/Media/Aux separately from Chat when supported.'
        )
        balance_card.layout().addWidget(self.chatmix_balance_detail_label)
        layout.addWidget(balance_card)

        return page

    def _build_device_page(self) -> QWidget:
        page, layout = self._scroll_page()

        capability_grid = QGridLayout()
        capability_grid.setSpacing(14)
        layout.addLayout(capability_grid)

        self.device_capability_state_labels: dict[str, QLabel] = {}
        self.device_capability_detail_labels: dict[str, QLabel] = {}
        for index, capability in enumerate(device_capability_summary({})):
            card = self._card(capability['title'])

            state_label = QLabel()
            state_label.setObjectName('endpointState')
            self._set_state_label(state_label, capability['state'])
            card.layout().addWidget(state_label)
            self.device_capability_state_labels[capability['key']] = state_label

            detail_label = self._muted_label(capability['detail'])
            card.layout().addWidget(detail_label)
            self.device_capability_detail_labels[capability['key']] = detail_label

            capability_grid.addWidget(card, index // 2, index % 2)

        snapshot = self._card('Control Snapshot')
        self.device_snapshot_state_labels: dict[str, QLabel] = {}
        self.device_snapshot_detail_labels: dict[str, QLabel] = {}
        for snapshot_item in device_control_snapshot({}):
            row = self._setup_step_row(
                snapshot_item['title'],
                snapshot_item['state'],
                snapshot_item['detail'],
            )
            snapshot.layout().addWidget(row)
            self.device_snapshot_state_labels[snapshot_item['key']] = row.findChild(QLabel, 'setupState')
            self.device_snapshot_detail_labels[snapshot_item['key']] = row.findChild(QLabel, 'mutedText')
        layout.addWidget(snapshot)

        self.device_settings_card = self._card('Device Controls')
        self.device_settings_card.layout().addWidget(self._muted_label(
            'Controls appear when the connected headset exposes them over D-Bus.'
        ))
        layout.addWidget(self.device_settings_card)

        return page

    def _build_routing_page(self) -> QWidget:
        page, layout = self._scroll_page()

        overview_grid = QGridLayout()
        overview_grid.setSpacing(14)
        layout.addLayout(overview_grid)

        self.routing_overview_value_labels: dict[str, QLabel] = {}
        self.routing_overview_detail_labels: dict[str, QLabel] = {}
        for index, (key, title) in enumerate([
            ('outputs', 'Virtual Outputs'),
            ('apps', 'Active App Streams'),
            ('planned', 'Planned Routing'),
        ]):
            card = self._card(title)

            value_label = QLabel()
            value_label.setObjectName('endpointState')
            self._set_state_label(value_label, 'Waiting')
            card.layout().addWidget(value_label)
            self.routing_overview_value_labels[key] = value_label

            detail_label = self._muted_label('Waiting for routing metadata.')
            card.layout().addWidget(detail_label)
            self.routing_overview_detail_labels[key] = detail_label

            overview_grid.addWidget(card, index // 2, index % 2)

        header = self._card('Endpoint State')
        self.routing_status_label = self._muted_label('Waiting for D-Bus endpoint state.')
        header.layout().addWidget(self.routing_status_label)
        self.refresh_routing_button = QPushButton('Refresh endpoint state')
        self.refresh_routing_button.setObjectName('secondaryAction')
        self.refresh_routing_button.clicked.connect(self._on_refresh_routing_clicked)
        header.layout().addWidget(self.refresh_routing_button)
        layout.addWidget(header)

        planned = self._card('Per-App Routing')
        planned.layout().addWidget(self._muted_label(
            'Move active application streams into Game, Chat, Media, or Aux virtual outputs.'
        ))

        self.route_app_stream_combo = QComboBox()
        self.route_app_stream_combo.setObjectName('routeCombo')
        planned.layout().addWidget(self.route_app_stream_combo)

        self.route_endpoint_combo = QComboBox()
        self.route_endpoint_combo.setObjectName('routeCombo')
        planned.layout().addWidget(self.route_endpoint_combo)

        self.assign_route_button = QPushButton('Assign selected stream')
        self.assign_route_button.setObjectName('primaryAction')
        self.assign_route_button.clicked.connect(self._on_assign_route_clicked)
        planned.layout().addWidget(self.assign_route_button)

        self.application_route_status_label = self._muted_label('Waiting for active application streams.')
        planned.layout().addWidget(self.application_route_status_label)
        layout.addWidget(planned)

        active_streams = self._card('Active App Streams')
        self.application_route_list_status_label = self._muted_label('Waiting for active playback streams.')
        active_streams.layout().addWidget(self.application_route_list_status_label)

        self.application_route_rows_container = QWidget()
        self.application_route_rows_layout = QVBoxLayout()
        self.application_route_rows_layout.setContentsMargins(0, 0, 0, 0)
        self.application_route_rows_layout.setSpacing(8)
        self.application_route_rows_container.setLayout(self.application_route_rows_layout)
        active_streams.layout().addWidget(self.application_route_rows_container)

        self.application_route_row_titles: list[QLabel] = []
        self.application_route_row_details: list[QLabel] = []
        self.application_route_row_current_labels: list[QLabel] = []
        layout.addWidget(active_streams)

        route_map = self._card('Route Map')
        self.route_map_state_labels: dict[str, QLabel] = {}
        self.route_map_detail_labels: dict[str, QLabel] = {}
        for item in endpoint_route_map({}):
            row = self._setup_step_row(
                item['title'],
                item['state'],
                item['detail'],
            )
            route_map.layout().addWidget(row)
            self.route_map_state_labels[item['key']] = row.findChild(QLabel, 'setupState')
            self.route_map_detail_labels[item['key']] = row.findChild(QLabel, 'mutedText')
        layout.addWidget(route_map)

        route_grid = QGridLayout()
        route_grid.setSpacing(14)
        layout.addLayout(route_grid)

        self.routing_state_labels: dict[str, QLabel] = {}
        self.routing_detail_labels: dict[str, QLabel] = {}
        for index, endpoint in enumerate(VIRTUAL_AUDIO_ENDPOINTS):
            card = self._card(endpoint.label)
            card.layout().addWidget(QLabel(endpoint.node_name))

            state_label = QLabel()
            state_label.setObjectName('routeState')
            self._set_state_label(state_label, 'Planned' if not endpoint.implemented else 'Waiting')
            card.layout().addWidget(state_label)
            self.routing_state_labels[endpoint.node_name] = state_label

            detail_label = self._muted_label('Output sink' if endpoint.kind == 'sink' else 'Input source')
            card.layout().addWidget(detail_label)
            self.routing_detail_labels[endpoint.node_name] = detail_label
            route_grid.addWidget(card, index // 2, index % 2)

        return page

    def _build_profiles_page(self) -> QWidget:
        page, layout = self._scroll_page()

        current = self._card('Current Profile')
        self.active_profile_label = QLabel('Default')
        self.active_profile_label.setObjectName('summaryValue')
        current.layout().addWidget(self.active_profile_label)
        current.layout().addWidget(self._muted_label(
            'Save the current device settings as a named profile, then load it again later.'
        ))

        self.profile_name_input = QLineEdit()
        self.profile_name_input.setObjectName('profileNameInput')
        self.profile_name_input.setPlaceholderText('Profile name')
        self.profile_name_input.setText('Default')
        current.layout().addWidget(self.profile_name_input)

        profile_actions = QWidget()
        profile_action_layout = QHBoxLayout()
        profile_action_layout.setContentsMargins(0, 0, 0, 0)
        profile_actions.setLayout(profile_action_layout)

        self.save_profile_button = QPushButton('Save profile')
        self.save_profile_button.setObjectName('primaryAction')
        self.save_profile_button.clicked.connect(self._on_save_profile_clicked)
        profile_action_layout.addWidget(self.save_profile_button)

        self.profile_combo = QComboBox()
        self.profile_combo.setObjectName('profileCombo')
        profile_action_layout.addWidget(self.profile_combo, 1)

        self.load_profile_button = QPushButton('Load profile')
        self.load_profile_button.setObjectName('secondaryAction')
        self.load_profile_button.clicked.connect(self._on_load_profile_clicked)
        profile_action_layout.addWidget(self.load_profile_button)

        current.layout().addWidget(profile_actions)

        self.profile_status_label = self._muted_label('Waiting for device settings.')
        current.layout().addWidget(self.profile_status_label)
        layout.addWidget(current)

        overview_grid = QGridLayout()
        overview_grid.setSpacing(14)
        layout.addLayout(overview_grid)

        self.profile_overview_value_labels: dict[str, QLabel] = {}
        self.profile_overview_detail_labels: dict[str, QLabel] = {}
        for index, (key, title) in enumerate([
            ('saved', 'Saved Profiles'),
            ('save', 'Save Readiness'),
            ('automation', 'Profile Automation'),
        ]):
            card = self._card(title)

            value_label = QLabel()
            value_label.setObjectName('endpointState')
            self._set_state_label(value_label, 'Waiting')
            card.layout().addWidget(value_label)
            self.profile_overview_value_labels[key] = value_label

            detail_label = self._muted_label('Waiting for profile metadata.')
            card.layout().addWidget(detail_label)
            self.profile_overview_detail_labels[key] = detail_label

            overview_grid.addWidget(card, index // 2, index % 2)

        context = self._card('App Context')
        self.profile_app_context_value_label = QLabel()
        self.profile_app_context_value_label.setObjectName('endpointState')
        self._set_state_label(self.profile_app_context_value_label, 'Waiting')
        context.layout().addWidget(self.profile_app_context_value_label)

        self.profile_app_context_detail_label = self._muted_label('Waiting for active app stream metadata.')
        context.layout().addWidget(self.profile_app_context_detail_label)
        layout.addWidget(context)

        return page

    def _build_settings_page(self) -> QWidget:
        page, layout = self._scroll_page()
        self.settings_page = page
        self.settings_page_content_layout = layout

        service = self._card('Service')
        self.service_status_label = QLabel()
        self.service_status_label.setObjectName('setupState')
        self._set_state_label(self.service_status_label, 'Waiting for D-Bus response')
        service.layout().addWidget(self.service_status_label)
        self.service_detail_label = self._muted_label(
            'Start the user service with lam-cli setup --start-now if the GUI does not connect.'
        )
        service.layout().addWidget(self.service_detail_label)
        layout.addWidget(service)

        setup = self._card('Setup Checklist')
        self.setup_state_labels: dict[str, QLabel] = {}
        self.setup_detail_labels: dict[str, QLabel] = {}
        for key, title, state, detail in [
            (
                'dbus',
                'D-Bus service',
                'Waiting',
                'The GUI reads headset status, settings, profiles, routes, and endpoint state from lam-daemon.',
            ),
            (
                'udev',
                'udev rules',
                'Required',
                'Run lam-cli setup after install so Linux grants the daemon access to supported USB/HID devices.',
            ),
            (
                'audio',
                'PulseAudio / PipeWire-pulse',
                'Required',
                'Virtual Game, Chat, Media, and Aux outputs use the PulseAudio compatibility API today.',
            ),
            (
                'autostart',
                'Tray autostart',
                'Optional',
                'Run lam-cli setup --systray-autostart --start-now if you want the tray helper at login.',
            ),
        ]:
            row = self._setup_step_row(title, state, detail)
            setup.layout().addWidget(row)
            self.setup_state_labels[key] = row.findChild(QLabel, 'setupState')
            self.setup_detail_labels[key] = row.findChild(QLabel, 'mutedText')
        layout.addWidget(setup)

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
        layout.setContentsMargins(16, 14, 16, 14)
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

        detail_label = self._muted_label('Waiting for metadata.')
        detail_label.setObjectName('summaryDetail')
        card.layout().addWidget(detail_label)
        return card

    def _header_chip(self, title: str, value: str) -> QFrame:
        chip = QFrame()
        chip.setObjectName('headerChip')
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(2)
        chip.setLayout(layout)

        title_label = QLabel(title)
        title_label.setObjectName('headerChipTitle')
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setObjectName('headerChipValue')
        value_label.setWordWrap(True)
        layout.addWidget(value_label)

        return chip

    def _readonly_meter(self, label: str) -> QWidget:
        meter = QWidget()
        meter_layout = QHBoxLayout()
        meter_layout.setContentsMargins(0, 0, 0, 0)
        meter_layout.setSpacing(10)
        meter.setLayout(meter_layout)

        label_widget = QLabel(label)
        label_widget.setObjectName('setupTitle')
        meter_layout.addWidget(label_widget)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(100)
        slider.setEnabled(False)
        slider.setObjectName('mixerSlider')
        meter_layout.addWidget(slider, 1)

        return meter

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

    @staticmethod
    def _state_tone(text: str) -> str:
        normalized = text.lower()
        if 'demo' in normalized:
            return 'demo'
        if 'optional' in normalized:
            return 'optional'
        if 'not exposed' in normalized:
            return 'neutral'
        if 'missing' in normalized:
            return 'warning' if 'ready' in normalized or 'planned' in normalized else 'missing'
        if 'planned' in normalized:
            return 'planned'
        if 'required' in normalized:
            return 'warning'
        if normalized.startswith('no ') or 'waiting' in normalized or 'unknown' in normalized:
            return 'waiting'
        if (
            'ready' in normalized
            or 'connected' in normalized
            or 'supported' in normalized
            or 'active app' in normalized
            or 'active stream' in normalized
            or 'saved profile' in normalized
        ):
            return 'ready'
        return 'neutral'

    def _set_state_label(self, label: QLabel, text: str) -> None:
        label.setText(text)
        label.setProperty('state', self._state_tone(text))
        label.style().unpolish(label)
        label.style().polish(label)
        label.update()

    def _setup_step_row(self, title: str, state: str, detail: str) -> QWidget:
        row = QWidget()
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)
        row.setLayout(row_layout)

        copy = QWidget()
        copy_layout = QVBoxLayout()
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.setSpacing(3)
        copy.setLayout(copy_layout)

        title_label = QLabel(title)
        title_label.setObjectName('setupTitle')
        copy_layout.addWidget(title_label)
        copy_layout.addWidget(self._muted_label(detail))
        row_layout.addWidget(copy, 1)

        state_label = QLabel()
        state_label.setObjectName('setupState')
        state_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._set_state_label(state_label, state)
        row_layout.addWidget(state_label)

        return row

    def _application_route_row(self, title: str, detail: str, current: str) -> QWidget:
        row = QWidget()
        row.setObjectName('appRouteRow')
        row_layout = QHBoxLayout()
        row_layout.setContentsMargins(10, 8, 10, 8)
        row_layout.setSpacing(12)
        row.setLayout(row_layout)

        copy = QWidget()
        copy_layout = QVBoxLayout()
        copy_layout.setContentsMargins(0, 0, 0, 0)
        copy_layout.setSpacing(3)
        copy.setLayout(copy_layout)

        title_label = QLabel(title)
        title_label.setObjectName('appRouteTitle')
        title_label.setWordWrap(True)
        copy_layout.addWidget(title_label)

        detail_label = self._muted_label(detail)
        copy_layout.addWidget(detail_label)
        row_layout.addWidget(copy, 1)

        current_label = QLabel(current)
        current_label.setObjectName('appRouteCurrent')
        current_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        current_label.setWordWrap(True)
        row_layout.addWidget(current_label)

        self.application_route_row_titles.append(title_label)
        self.application_route_row_details.append(detail_label)
        self.application_route_row_current_labels.append(current_label)

        return row

    @staticmethod
    def _clear_layout(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

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
        if self.demo_mode:
            self._set_service_status(
                'Demo metadata loaded',
                'Sample settings, routes, and profiles are driving the preview.',
                'Demo',
            )
        else:
            self._set_service_status(
                'D-Bus settings connected',
                'Settings metadata is flowing from lam-daemon.',
                'Connected',
            )
        self._refresh_dashboard_settings(settings)
        self._refresh_profile_state(settings)
        self._refresh_profile_overview(settings)
        self._refresh_profile_app_context(settings)
        self._refresh_device_capability_state(settings)
        self._refresh_device_control_snapshot(settings)
        self._refresh_routing_overview(settings)
        self._refresh_mixer_settings(settings)
        self._refresh_routing_state(settings)
        self._refresh_application_routes(settings)
        self._refresh_route_map(settings)

    def on_status_received(self, status):
        if status == self.status:
            return

        self.status = status
        if self.demo_mode:
            self._set_service_status(
                'Demo status loaded',
                'Sample headset status is driving the preview.',
                'Demo',
            )
        else:
            self._set_service_status(
                'D-Bus status connected',
                'Live headset status is flowing from lam-daemon.',
                'Connected',
            )
        self._refresh_dashboard_status(status)
        self._refresh_mixer_status(status)

    def _set_service_status(self, text: str, detail: str, dbus_state: str) -> None:
        self._set_state_label(self.service_status_label, text)
        self.service_detail_label.setText(detail)
        if 'dbus' in self.setup_state_labels:
            self._set_state_label(self.setup_state_labels['dbus'], dbus_state)

    def _refresh_dashboard_status(self, status: dict) -> None:
        self._refresh_header_context()
        for key, value in dashboard_summary(status, self.settings).items():
            if key in self.dashboard_cards:
                self.dashboard_cards[key].setText(value)
        self._refresh_dashboard_details()
        self._refresh_dashboard_control_surface()

    def _refresh_dashboard_settings(self, settings: dict) -> None:
        self._refresh_header_context()
        for key, value in dashboard_settings_summary(settings).items():
            if key in self.dashboard_cards:
                self.dashboard_cards[key].setText(value)
        self._refresh_dashboard_details()
        self._refresh_dashboard_control_surface()

    def _refresh_dashboard_details(self) -> None:
        for key, detail in dashboard_detail_summary(self.status, self.settings).items():
            if key in self.dashboard_card_details:
                self.dashboard_card_details[key].setText(detail)

    def _refresh_header_context(self) -> None:
        for key, value in header_context_summary(self.status, self.settings).items():
            value_label = self.header_context_values.get(key)
            if value_label:
                value_label.setText(value)
                value_label.setProperty('state', self._state_tone(value))
                value_label.style().unpolish(value_label)
                value_label.style().polish(value_label)
                value_label.update()

    def _refresh_dashboard_control_surface(self) -> None:
        for item in dashboard_control_surface_summary(self.status, self.settings):
            state_label = self.dashboard_control_state_labels.get(item['key'])
            detail_label = self.dashboard_control_detail_labels.get(item['key'])
            if state_label:
                self._set_state_label(state_label, item['state'])
            if detail_label:
                detail_label.setText(item['detail'])

    def _refresh_mixer_status(self, status: dict) -> None:
        for node_name, level in mixer_levels(status).items():
            slider = self.mixer_sliders.get(node_name)
            if not slider:
                continue
            slider.setValue(level)
            value_label = self.mixer_value_labels.get(node_name)
            if value_label:
                value_label.setText(f'{level}%')

        balance = chatmix_balance_summary(status)
        self.chatmix_balance_value_label.setText(str(balance['value']))
        self.chatmix_balance_detail_label.setText(str(balance['detail']))
        media_slider = self.chatmix_media_balance_slider.findChild(QSlider)
        chat_slider = self.chatmix_chat_balance_slider.findChild(QSlider)
        if media_slider:
            media_slider.setValue(int(balance['media_level']))
        if chat_slider:
            chat_slider.setValue(int(balance['chat_level']))

    def _refresh_mixer_overview(self, settings: dict) -> None:
        summary = mixer_overview_summary(settings)
        for key in ('channels', 'media', 'chat'):
            value_label = self.mixer_overview_value_labels.get(key)
            detail_label = self.mixer_overview_detail_labels.get(key)
            if value_label:
                self._set_state_label(value_label, summary[f'{key}_value'])
            if detail_label:
                detail_label.setText(summary[f'{key}_detail'])

    def _refresh_mixer_settings(self, settings: dict) -> None:
        self._refresh_mixer_overview(settings)
        endpoint_states = settings.get('audio_endpoints', [])
        if not isinstance(endpoint_states, list):
            endpoint_states = []

        states_by_node = {
            state.get('node_name'): state
            for state in endpoint_states
            if isinstance(state, dict) and isinstance(state.get('node_name'), str)
        }

        for endpoint in VIRTUAL_AUDIO_ENDPOINTS:
            state_label = self.mixer_state_labels.get(endpoint.node_name)
            detail_label = self.mixer_detail_labels.get(endpoint.node_name)
            if not state_label or not detail_label:
                continue

            if not endpoint.implemented:
                self._set_state_label(state_label, 'Planned')
                detail_label.setText('Reserved for future microphone routing')
                continue

            state = states_by_node.get(endpoint.node_name)
            if state is None:
                if self.dbus_wrapper:
                    self._set_state_label(state_label, 'Waiting')
                    detail_label.setText('Waiting for endpoint state from the D-Bus service.')
                else:
                    self._set_state_label(state_label, 'Demo')
                    detail_label.setText('Demo mix level from sample status.')
                continue

            present = bool(state.get('present'))
            is_default = bool(state.get('default'))
            description = state.get('description') or endpoint.node_name
            if present:
                self._set_state_label(state_label, 'Ready / Default' if is_default else 'Ready')
                detail_label.setText(f'Output present: {description}')
            else:
                self._set_state_label(state_label, 'Missing')
                detail_label.setText('Virtual output not available yet.')

    def _refresh_device_capability_state(self, settings: dict) -> None:
        for capability in device_capability_summary(settings):
            state_label = self.device_capability_state_labels.get(capability['key'])
            detail_label = self.device_capability_detail_labels.get(capability['key'])
            if state_label:
                self._set_state_label(state_label, capability['state'])
            if detail_label:
                detail_label.setText(capability['detail'])

    def _refresh_device_control_snapshot(self, settings: dict) -> None:
        for snapshot in device_control_snapshot(settings):
            state_label = self.device_snapshot_state_labels.get(snapshot['key'])
            detail_label = self.device_snapshot_detail_labels.get(snapshot['key'])
            if state_label:
                self._set_state_label(state_label, snapshot['state'])
            if detail_label:
                detail_label.setText(snapshot['detail'])

    def _refresh_profile_state(self, settings: dict) -> None:
        profiles = settings.get('profiles', {})
        if not isinstance(profiles, dict):
            profiles = {}

        available = profiles.get('available', [])
        active = profiles.get('active', 'Default')
        has_device_settings = bool(settings.get('device'))

        if not isinstance(available, list):
            available = []
        if not isinstance(active, str):
            active = 'Default'

        self.active_profile_label.setText(active)
        if self.profile_name_input.text().strip() in ('', 'Default'):
            self.profile_name_input.setText(active)

        self.profile_combo.clear()
        if available:
            self.profile_combo.addItems([str(profile) for profile in available])
            if active in available:
                self.profile_combo.setCurrentIndex(available.index(active))
        else:
            self.profile_combo.addItem('No saved profiles')

        controls_enabled = bool(self.dbus_wrapper) and has_device_settings
        self.save_profile_button.setEnabled(controls_enabled)
        self.profile_name_input.setEnabled(controls_enabled)
        self.profile_combo.setEnabled(controls_enabled and bool(available))
        self.load_profile_button.setEnabled(controls_enabled and bool(available))

        if not self.dbus_wrapper:
            self.profile_status_label.setText('Demo mode: profile actions need the D-Bus service.')
        elif has_device_settings:
            self.profile_status_label.setText('Profiles save and load the current device settings.')
        else:
            self.profile_status_label.setText('Connect a supported headset to save profiles.')

    def _refresh_profile_overview(self, settings: dict) -> None:
        summary = profile_workflow_summary(settings)
        for key in ('saved', 'save', 'automation'):
            value_label = self.profile_overview_value_labels.get(key)
            detail_label = self.profile_overview_detail_labels.get(key)
            if value_label:
                self._set_state_label(value_label, summary[f'{key}_value'])
            if detail_label:
                detail_label.setText(summary[f'{key}_detail'])

    def _refresh_profile_app_context(self, settings: dict) -> None:
        summary = profile_app_context_summary(settings)
        self._set_state_label(self.profile_app_context_value_label, summary['value'])
        self.profile_app_context_detail_label.setText(summary['detail'])

    def _on_save_profile_clicked(self) -> None:
        if not self.dbus_wrapper:
            self.profile_status_label.setText('D-Bus service is required to save profiles.')
            return

        profile_name = self.profile_name_input.text().strip()
        if not profile_name:
            self.profile_status_label.setText('Enter a profile name before saving.')
            return

        self.profile_status_label.setText(f'Save requested for "{profile_name}".')
        self.dbus_wrapper.save_profile(profile_name)

    def _on_load_profile_clicked(self) -> None:
        if not self.dbus_wrapper:
            self.profile_status_label.setText('D-Bus service is required to load profiles.')
            return

        profile_name = self.profile_combo.currentText().strip()
        if not profile_name or profile_name == 'No saved profiles':
            self.profile_status_label.setText('Choose a saved profile first.')
            return

        self.profile_name_input.setText(profile_name)
        self.profile_status_label.setText(f'Load requested for "{profile_name}".')
        self.dbus_wrapper.load_profile(profile_name)

    def _refresh_routing_state(self, settings: dict) -> None:
        endpoint_states = settings.get('audio_endpoints', [])
        if not isinstance(endpoint_states, list):
            endpoint_states = []

        states_by_node = {
            state.get('node_name'): state
            for state in endpoint_states
            if isinstance(state, dict) and isinstance(state.get('node_name'), str)
        }

        ready_count = 0
        missing_count = 0
        for endpoint in VIRTUAL_AUDIO_ENDPOINTS:
            state = states_by_node.get(endpoint.node_name, {})
            state_label = self.routing_state_labels.get(endpoint.node_name)
            detail_label = self.routing_detail_labels.get(endpoint.node_name)
            if not state_label or not detail_label:
                continue

            if not endpoint.implemented:
                self._set_state_label(state_label, 'Planned')
                detail_label.setText('Input source reserved for future microphone routing.')
                continue

            if not state:
                self._set_state_label(state_label, 'Unknown')
                detail_label.setText('Waiting for endpoint state from the D-Bus service.')
                continue

            present = bool(state.get('present'))
            is_default = bool(state.get('default'))
            description = state.get('description') or endpoint.node_name

            if present:
                ready_count += 1
                self._set_state_label(state_label, 'Ready / Default' if is_default else 'Ready')
                detail_label.setText(f'Virtual output present: {description}')
            else:
                missing_count += 1
                self._set_state_label(state_label, 'Missing')
                detail_label.setText('Created when a supported headset and PulseAudio/PipeWire-pulse are available.')

        if endpoint_states:
            self.routing_status_label.setText(f'{ready_count} virtual outputs ready, {missing_count} missing.')
        elif self.dbus_wrapper:
            self.routing_status_label.setText('No endpoint state received yet. Use refresh after connecting a headset.')
        else:
            self.routing_status_label.setText('Demo mode: endpoint state needs the D-Bus service.')

        self.refresh_routing_button.setEnabled(bool(self.dbus_wrapper))

    def _on_refresh_routing_clicked(self) -> None:
        if not self.dbus_wrapper:
            self.routing_status_label.setText('D-Bus service is required to refresh endpoint state.')
            return

        self.routing_status_label.setText('Refresh requested.')
        self.dbus_wrapper.request_settings()

    def _refresh_routing_overview(self, settings: dict) -> None:
        summary = routing_overview_summary(settings)
        for key in ('outputs', 'apps', 'planned'):
            value_label = self.routing_overview_value_labels.get(key)
            detail_label = self.routing_overview_detail_labels.get(key)
            if value_label:
                self._set_state_label(value_label, summary[f'{key}_value'])
            if detail_label:
                detail_label.setText(summary[f'{key}_detail'])

    def _refresh_route_map(self, settings: dict) -> None:
        for item in endpoint_route_map(settings):
            state_label = self.route_map_state_labels.get(item['key'])
            detail_label = self.route_map_detail_labels.get(item['key'])
            if state_label:
                self._set_state_label(state_label, item['state'])
            if detail_label:
                detail_label.setText(item['detail'])

    def _refresh_application_routes(self, settings: dict) -> None:
        routes = settings.get('application_routes', [])
        endpoint_states = settings.get('audio_endpoints', [])
        if not isinstance(routes, list):
            routes = []
        if not isinstance(endpoint_states, list):
            endpoint_states = []

        valid_routes = [
            route
            for route in routes
            if isinstance(route, dict) and isinstance(route.get('stream_index'), int)
        ]
        available_endpoints = [
            endpoint
            for endpoint in endpoint_states
            if isinstance(endpoint, dict)
            and endpoint.get('kind') == 'sink'
            and endpoint.get('implemented') is True
            and endpoint.get('present') is True
            and isinstance(endpoint.get('node_name'), str)
        ]
        route_rows = application_route_rows({'application_routes': valid_routes})

        self.route_app_stream_combo.clear()
        if route_rows:
            for route in route_rows:
                self.route_app_stream_combo.addItem(f"{route['title']} -> {route['current']}", route['stream_index'])
        else:
            self.route_app_stream_combo.addItem('No active app streams', -1)

        self.route_endpoint_combo.clear()
        if available_endpoints:
            for endpoint in available_endpoints:
                self.route_endpoint_combo.addItem(f"{endpoint.get('label', endpoint['node_name'])} ({endpoint['node_name']})", endpoint['node_name'])
        else:
            self.route_endpoint_combo.addItem('No virtual outputs ready', '')

        controls_enabled = bool(self.dbus_wrapper) and bool(valid_routes) and bool(available_endpoints)
        self.route_app_stream_combo.setEnabled(controls_enabled)
        self.route_endpoint_combo.setEnabled(controls_enabled)
        self.assign_route_button.setEnabled(controls_enabled)
        self._refresh_application_route_rows(route_rows)

        if not self.dbus_wrapper:
            self.application_route_status_label.setText('Demo mode: app routing needs the D-Bus service.')
        elif not valid_routes:
            self.application_route_status_label.setText('No active application streams are currently available to route.')
        elif not available_endpoints:
            self.application_route_status_label.setText('No implemented virtual outputs are ready yet.')
        else:
            self.application_route_status_label.setText(f'{len(valid_routes)} active app stream(s) can be assigned.')

    def _refresh_application_route_rows(self, route_rows: list[dict[str, str | int]]) -> None:
        self._clear_layout(self.application_route_rows_layout)
        self.application_route_row_titles = []
        self.application_route_row_details = []
        self.application_route_row_current_labels = []

        if not route_rows:
            self.application_route_list_status_label.setText('No active playback streams reported yet.')
            self.application_route_rows_container.setVisible(False)
            return

        self.application_route_rows_container.setVisible(True)
        count = len(route_rows)
        label = 'active playback stream' if count == 1 else 'active playback streams'
        self.application_route_list_status_label.setText(f'{count} {label} reported by PulseAudio/PipeWire-pulse.')
        for route in route_rows:
            self.application_route_rows_layout.addWidget(self._application_route_row(
                str(route['title']),
                str(route['detail']),
                str(route['current']),
            ))

    def _on_assign_route_clicked(self) -> None:
        if not self.dbus_wrapper:
            self.application_route_status_label.setText('D-Bus service is required to assign app routes.')
            return

        stream_index = self.route_app_stream_combo.currentData()
        endpoint_node_name = self.route_endpoint_combo.currentData()
        if not isinstance(stream_index, int) or stream_index < 0 or not endpoint_node_name:
            self.application_route_status_label.setText('Choose an active stream and a ready virtual output first.')
            return

        self.application_route_status_label.setText('Route assignment requested.')
        self.dbus_wrapper.move_application_route(stream_index, endpoint_node_name)

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
                font-size: 20px;
                font-weight: 700;
            }
            #brandTagline, #sidebarNotice, #pageSubtitle, #mutedText {
                color: #91a4b7;
            }
            #pageTitle {
                color: #f8fafc;
                font-size: 28px;
                font-weight: 700;
            }
            #pageSubtitle {
                font-size: 13px;
            }
            #headerChip {
                background: #121b24;
                border: 1px solid #263241;
                border-radius: 8px;
            }
            #headerChipTitle {
                color: #91a4b7;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
            }
            #headerChipValue {
                color: #f8fafc;
                font-size: 13px;
                font-weight: 700;
            }
            #headerChipValue[state="ready"] {
                color: #a7f3d0;
            }
            #headerChipValue[state="warning"] {
                color: #f8d775;
            }
            #headerChipValue[state="missing"] {
                color: #ffc5cc;
            }
            #headerChipValue[state="planned"], #headerChipValue[state="demo"] {
                color: #bfdbfe;
            }
            #headerChipValue[state="waiting"], #headerChipValue[state="neutral"] {
                color: #dbe7f3;
            }
            #navButton {
                background: transparent;
                border: 0;
                border-radius: 8px;
                color: #cbd5e1;
                font-size: 14px;
                padding: 9px 10px;
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
            #primaryAction, #secondaryAction, #profileNameInput, #profileCombo, #routeCombo {
                border-radius: 8px;
                font-size: 13px;
                min-height: 34px;
                padding: 6px 10px;
            }
            #primaryAction {
                background: #5fb3f3;
                border: 1px solid #7bc4ff;
                color: #08111a;
                font-weight: 700;
            }
            #secondaryAction {
                background: #1c2733;
                border: 1px solid #34465a;
                color: #dbe7f3;
                font-weight: 700;
            }
            #primaryAction:disabled, #secondaryAction:disabled {
                background: #1c2733;
                border: 1px solid #2e3c4d;
                color: #7f92a5;
            }
            #profileNameInput, #profileCombo, #routeCombo {
                background: #0f1419;
                border: 1px solid #34465a;
                color: #edf2f7;
            }
            #profileNameInput:disabled, #profileCombo:disabled, #routeCombo:disabled {
                color: #7f92a5;
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
            #routeState, #endpointState, #setupState {
                background: #1b2530;
                border: 1px solid #34465a;
                border-radius: 7px;
                color: #dbe7f3;
                font-size: 13px;
                font-weight: 700;
                padding: 4px 8px;
            }
            #routeState {
                font-size: 14px;
            }
            #routeState[state="ready"], #endpointState[state="ready"], #setupState[state="ready"] {
                background: #14362f;
                border-color: #2f7d66;
                color: #a7f3d0;
            }
            #routeState[state="warning"], #endpointState[state="warning"], #setupState[state="warning"] {
                background: #3a2d12;
                border-color: #8c6b24;
                color: #f8d775;
            }
            #routeState[state="missing"], #endpointState[state="missing"], #setupState[state="missing"] {
                background: #3a1d22;
                border-color: #7f3540;
                color: #ffc5cc;
            }
            #routeState[state="planned"], #endpointState[state="planned"], #setupState[state="planned"] {
                background: #1d2f46;
                border-color: #466b9a;
                color: #bfdbfe;
            }
            #routeState[state="demo"], #endpointState[state="demo"], #setupState[state="demo"] {
                background: #183342;
                border-color: #4a809c;
                color: #bae6fd;
            }
            #routeState[state="optional"], #endpointState[state="optional"], #setupState[state="optional"] {
                background: #1d2d2a;
                border-color: #456c62;
                color: #c7f7e5;
            }
            #routeState[state="waiting"], #endpointState[state="waiting"], #setupState[state="waiting"],
            #routeState[state="neutral"], #endpointState[state="neutral"], #setupState[state="neutral"] {
                background: #18212b;
                border-color: #2b3a49;
                color: #aab8c7;
            }
            #appRouteRow {
                background: #101820;
                border: 1px solid #263241;
                border-radius: 6px;
            }
            #appRouteTitle {
                color: #f8fafc;
                font-size: 13px;
                font-weight: 700;
            }
            #appRouteCurrent {
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
            }
            #settingsSectionTitle, #statusGroupTitle {
                color: #f8fafc;
                font-size: 14px;
                font-weight: 700;
            }
            #settingRow, #statusGroup {
                background: #101820;
                border: 1px solid #263241;
                border-radius: 6px;
            }
            #settingLabel, #statusKey {
                color: #dbe7f3;
                font-size: 13px;
                font-weight: 700;
            }
            #settingValue, #statusValue {
                color: #ffffff;
                font-size: 13px;
                font-weight: 700;
            }
            #setupTitle {
                color: #f8fafc;
                font-size: 13px;
                font-weight: 700;
            }
            #mixerValue {
                color: #ffffff;
                font-size: 19px;
                font-weight: 700;
            }
            #summaryValue {
                color: #ffffff;
                font-size: 21px;
                font-weight: 700;
            }
            #summaryDetail {
                color: #91a4b7;
                font-size: 12px;
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
