import flet as ft
import json
from core.theme import Colors, AppTheme, ThemeManager, ACCENT_PALETTES
from core.localization import Locales, t
import os
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
license_path = os.path.join(current_dir, "LICENSE")
with open(license_path, "r", encoding="utf-8") as f:
    license_text = f.read()


async def get_settings_view(page: ft.Page) -> ft.Column:
    # ── helpers ───────────────────────────────────────────────────────────────
    def btn_hover(e):
        e.control.scale = 0.98 if e.data == "true" else 1.0
        e.control.update()

    # ================================================================
    # PRIVACY FULL PAGE
    # ================================================================
    privacy_body_col = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        controls=[
            ft.Text(
                license_text,
                size=14,
                selectable=True
            )
        ]
    )

    privacy_topbar_title = ft.Text(t("privacy_data"), size=20, color=Colors.PRIMARY_TEAL, weight="bold")
    privacy_topbar = ft.Container(
        bgcolor=AppTheme.SURFACE,
        padding=ft.Padding.only(left=10, right=20, top=50, bottom=10),
        content=ft.Row(controls=[
            ft.IconButton(
                icon=ft.icons.Icons.ARROW_BACK,
                icon_color=Colors.PRIMARY_TEAL,
                on_click=lambda e: close_privacy_page(),
            ),
            privacy_topbar_title
        ])
    )

    privacy_page = ft.Container(
        visible=False,
        expand=True,
        bgcolor=Colors.BACKGROUND,
        content=ft.Column(expand=True, controls=[
            privacy_topbar,
            ft.Container(
                expand=True,
                padding=ft.Padding.symmetric(horizontal=20, vertical=16),
                content=privacy_body_col
            )
        ])
    )

    def open_privacy_page(e):
        privacy_page.visible = True
        settings_scroll_col.visible = False
        settings_view.update()

    def close_privacy_page():
        privacy_page.visible = False
        settings_scroll_col.visible = True
        settings_view.update()

    # ================================================================
    # LENS PROFILE
    # ================================================================
    raw_duration = await page.prefs.get("lens_duration_days")
    saved_duration = json.loads(raw_duration) if raw_duration else 14
    duration_text = ft.Text(f"{saved_duration} {t('days_short')}", size=13,
                             color=Colors.PRIMARY_TEAL, weight="bold")

    duration_badge = ft.Container(
        bgcolor=AppTheme.PROGRESS_BG,
        padding=ft.Padding.symmetric(horizontal=12, vertical=6),
        border_radius=15,
        content=duration_text
    )

    async def handle_duration_change(e):
        selected_val = e.control.value
        if selected_val:
            days = int(selected_val)
            await page.prefs.set("lens_duration_days", json.dumps(days))
            duration_text.value = f"{days} {t('days_short')}"
            page.update()

    profile_radio = ft.RadioGroup(
        value=str(saved_duration),
        on_change=handle_duration_change,
        content=ft.Column([
            ft.Radio(value="7", label=f"7 {t('days')}"),
            ft.Radio(value="14", label=f"14 {t('days')}"),
            ft.Radio(value="30", label=f"30 {t('days')}"),
        ])
    )

    profile_dialog = ft.AlertDialog(
        modal=False,
        title=ft.Text(t("select_lens_duration")),
        content=ft.Container(padding=10, content=profile_radio),
        actions=[ft.TextButton(t("close"), on_click=lambda e: close_profile_dialog())],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(profile_dialog)

    def close_profile_dialog():
        profile_dialog.open = False
        page.update()

    def open_profile_dialog(e):
        profile_dialog.open = True
        page.update()

    raw_start = await page.prefs.get("lens_start_date")
    saved_start_date = json.loads(raw_start) if raw_start else ""
    start_date_text = ft.Text(
        saved_start_date if saved_start_date else t("not_started"),
        size=14, color=Colors.TEXT_DARK, weight="bold"
    )

    lens_profile_icon = ft.Icon(icon=ft.icons.Icons.REMOVE_RED_EYE_OUTLINED,
                                 color=Colors.PRIMARY_TEAL, size=20)
    lens_profile_title = ft.Text(t("lens_profile"), size=16, color=Colors.PRIMARY_TEAL, weight="bold")
    max_wear_label = ft.Text(t("max_wear_duration"), size=14, color=Colors.TEXT_HINT)
    lens_start_label = ft.Text(t("current_lens_start"), size=14, color=Colors.TEXT_HINT)
    lens_profile_divider = ft.Divider(color="#DCEAE7", height=1)

    settings_lens_profile = ft.Container(
        bgcolor=Colors.LIGHT_TEAL,
        border_radius=20,
        padding=20,
        ink=True,
        on_click=open_profile_dialog,
        on_hover=btn_hover,
        animate_scale=ft.Animation(200, "easeOut"),
        scale=1.0,
        content=ft.Column(spacing=15, controls=[
            ft.Row(spacing=10, controls=[lens_profile_icon, lens_profile_title]),
            ft.Container(height=5),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                   controls=[max_wear_label, duration_badge]),
            lens_profile_divider,
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                   controls=[lens_start_label, start_date_text])
        ])
    )

    # ================================================================
    # NOTIFICATIONS
    # ================================================================
    async def handle_daily_reminder(e):
        if daily_reminder_switch.value:
            has_perm = await page.notifications.request_permissions()
            if not has_perm:
                daily_reminder_switch.value = False
        await page.prefs.set("daily_reminder", json.dumps(daily_reminder_switch.value))
        page.update()

    async def handle_replacement_alert(e):
        if replacement_alert_switch.value:
            has_perm_1 = await page.notifications.request_permissions()
            has_perm_2 = await page.notifications.request_exact_alarm_permission()
            if not has_perm_1 or not has_perm_2:
                replacement_alert_switch.value = False
        
        await page.prefs.set("replacement_alert", json.dumps(replacement_alert_switch.value))
        page.update()

        if replacement_alert_switch.value:
            # Schedule if there's an active lens
            raw_duration = await page.prefs.get("lens_duration_days")
            dur = json.loads(raw_duration) if raw_duration else 14
            raw_start = await page.prefs.get("lens_start_date")
            st = json.loads(raw_start) if raw_start else ""
            if st:
                try:
                    start_dt = datetime.strptime(st, "%Y-%m-%d")
                    target_dt = start_dt + timedelta(days=dur)
                    target_dt = target_dt.replace(hour=7, minute=0, second=0, microsecond=0)
                    await page.notifications.cancel(2)
                    if target_dt > datetime.now():
                        await page.notifications.schedule_notification(
                            notification_id=2, 
                            title="LensTrack",
                            body=t("health_tip_days_exceeded"), 
                            scheduled_time=target_dt
                        )
                except Exception:
                    pass
        else:
            await page.notifications.cancel(2)

    raw_daily = await page.prefs.get("daily_reminder")
    daily_reminder_switch = ft.Switch(
        value=json.loads(raw_daily) if raw_daily else False,
        active_color=Colors.PRIMARY_TEAL,
        on_change=handle_daily_reminder
    )

    raw_alert = await page.prefs.get("replacement_alert")
    replacement_alert_switch = ft.Switch(
        value=json.loads(raw_alert) if raw_alert else False,
        active_color=Colors.PRIMARY_TEAL,
        on_change=handle_replacement_alert
    )

    notif_icon = ft.Icon(icon=ft.icons.Icons.NOTIFICATIONS_OUTLINED,
                          color=Colors.PRIMARY_TEAL, size=20)
    notif_title = ft.Text(t("notifications"), size=16, color=Colors.PRIMARY_TEAL, weight="bold")
    daily_label = ft.Text(t("daily_reminder"), size=14, color=Colors.TEXT_HINT)
    alert_label = ft.Text(t("replacement_alert"), size=14, color=Colors.TEXT_HINT)

    settings_notifications = ft.Container(
        bgcolor=AppTheme.SURFACE,
        border=ft.Border.all(1, Colors.CARD_BORDER),
        border_radius=20,
        padding=20,
        content=ft.Column(spacing=15, controls=[
            ft.Row(spacing=10, controls=[notif_icon, notif_title]),
            ft.Container(height=5),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                   controls=[daily_label, daily_reminder_switch]),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                   controls=[alert_label, replacement_alert_switch])
        ])
    )

    # ================================================================
    # APPEARANCE
    # ================================================================
    raw_is_dark = await page.prefs.get("theme_is_dark")
    AppTheme.is_dark = json.loads(raw_is_dark) if raw_is_dark else False

    raw_accent = await page.prefs.get("theme_accent")
    AppTheme.accent_name = json.loads(raw_accent) if raw_accent else "Teal"

    # Apply initial theme values without page.update (not yet on page)
    AppTheme.apply()

    # Theme toggle button
    theme_label = ft.Text(
        t("dark") if AppTheme.is_dark else t("light"),
        size=13, color=Colors.PRIMARY_TEAL, weight="bold"
    )
    theme_icon = ft.Icon(
        icon=ft.icons.Icons.DARK_MODE if AppTheme.is_dark else ft.icons.Icons.LIGHT_MODE_OUTLINED,
        color=Colors.PRIMARY_TEAL, size=16
    )

    async def toggle_theme(e):
        AppTheme.is_dark = not AppTheme.is_dark
        await page.prefs.set("theme_is_dark", json.dumps(AppTheme.is_dark))
        ThemeManager.notify_all(page)   # repaints everything

    theme_btn = ft.Container(
        bgcolor=Colors.LIGHT_TEAL,
        padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        border_radius=15,
        ink=True,
        on_hover=btn_hover,
        animate_scale=ft.Animation(200, "easeOut"),
        scale=1.0,
        on_click=toggle_theme,
        content=ft.Row(spacing=6, controls=[theme_icon, theme_label])
    )

    # Accent color picker
    accent_label = ft.Text(
        AppTheme.accent_name, size=13, color=Colors.PRIMARY_TEAL, weight="bold"
    )
    accent_icon = ft.Icon(icon=ft.icons.Icons.PALETTE_OUTLINED,
                           color=Colors.PRIMARY_TEAL, size=16)

    def build_accent_chips():
        chips = []
        mode = "dark" if AppTheme.is_dark else "light"
        for name, pal in ACCENT_PALETTES.items():
            curr_pal = pal[mode]
            is_sel = (name == AppTheme.accent_name)
            chip = ft.Container(
                width=44, height=44,
                border_radius=22,
                bgcolor=curr_pal[0],
                border=ft.Border.all(4, curr_pal[2]) if is_sel else ft.Border.all(2, AppTheme.WHITE),
                ink=True,
                tooltip=name,
                # use sync on_click that schedules the async task
                on_click=lambda e, n=name: page.run_task(select_accent, n),
            )
            chips.append(chip)
        return chips

    accent_chips_row = ft.Row(spacing=10, wrap=True, alignment=ft.MainAxisAlignment.CENTER, controls=build_accent_chips())

    async def select_accent(name: str):
        AppTheme.accent_name = name
        await page.prefs.set("theme_accent", json.dumps(name))
        # Rebuild chips immediately so selection indicator updates
        accent_chips_row.controls = build_accent_chips()
        accent_label.value = name
        ThemeManager.notify_all(page)

    accent_dialog_desc = ft.Text(t("select_palette"), size=13, color=Colors.TEXT_HINT, text_align=ft.TextAlign.CENTER)
    accent_dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text(t("choose_accent")),
        content=ft.Container(
            width=300,
            padding=10,
            content=ft.Column(spacing=16, horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[
                accent_dialog_desc,
                accent_chips_row,
            ])
        ),
        actions=[ft.TextButton(t("done"), on_click=lambda e: close_accent_dialog())],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(accent_dialog)

    def close_accent_dialog():
        accent_dialog.open = False
        page.update()

    def open_accent_dialog(e):
        accent_dialog.open = True
        page.update()

    accent_btn = ft.Container(
        bgcolor=Colors.LIGHT_TEAL,
        padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        border_radius=15,
        ink=True,
        on_hover=btn_hover,
        animate_scale=ft.Animation(200, "easeOut"),
        scale=1.0,
        on_click=open_accent_dialog,
        content=ft.Row(spacing=6, controls=[accent_icon, accent_label])
    )

    # Language Picker
    raw_lang = await page.prefs.get("app_language")
    saved_lang = json.loads(raw_lang) if raw_lang else "en"
    lang_map = {"en": "English", "ru": "Русский", "fr": "Français", "de": "Deutsch"}
    lang_label = ft.Text(lang_map.get(saved_lang, "English"), size=13, color=Colors.PRIMARY_TEAL, weight="bold")
    lang_icon = ft.Icon(icon=ft.icons.Icons.LANGUAGE, color=Colors.PRIMARY_TEAL, size=16)

    async def save_language(e):
        val = e.control.value
        if val:
            await page.prefs.set("app_language", json.dumps(val))
            Locales.current_lang = val
            lang_label.value = lang_map.get(val, "English")
            ThemeManager.notify_all(page)

    lang_radio = ft.RadioGroup(
        value=saved_lang,
        on_change=save_language,
        content=ft.Column([
            ft.Radio(value="en", label="English"),
            ft.Radio(value="ru", label="Русский"),
            ft.Radio(value="fr", label="Français"),
            ft.Radio(value="de", label="Deutsch"),
        ])
    )

    lang_dialog = ft.AlertDialog(
        modal=False,
        title=ft.Text(t("select_language")),
        content=ft.Container(padding=10, content=lang_radio),
        actions=[ft.TextButton(t("close"), on_click=lambda e: setattr(lang_dialog, 'open', False) or page.update())],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(lang_dialog)

    lang_btn = ft.Container(
        bgcolor=Colors.LIGHT_TEAL,
        padding=ft.Padding.symmetric(horizontal=14, vertical=8),
        border_radius=15,
        ink=True,
        on_hover=btn_hover,
        animate_scale=ft.Animation(200, "easeOut"),
        scale=1.0,
        on_click=lambda e: setattr(lang_dialog, 'open', True) or page.update(),
        content=ft.Row(spacing=6, controls=[lang_icon, lang_label])
    )

    appear_icon = ft.Icon(icon=ft.icons.Icons.PALETTE_OUTLINED, color=Colors.PRIMARY_TEAL, size=20)
    appear_title = ft.Text(t("appearance"), size=16, color=Colors.PRIMARY_TEAL, weight="bold")
    theme_row_label = ft.Text(t("theme"), size=14, color=Colors.TEXT_HINT)
    accent_row_label = ft.Text(t("accent_color"), size=14, color=Colors.TEXT_HINT)
    lang_row_label = ft.Text(t("language"), size=14, color=Colors.TEXT_HINT)
    appear_divider_1 = ft.Divider(color="#DCEAE7", height=1)
    appear_divider_2 = ft.Divider(color="#DCEAE7", height=1)

    settings_appearance = ft.Container(
        bgcolor=AppTheme.SURFACE,
        border=ft.Border.all(1, Colors.CARD_BORDER),
        border_radius=20,
        padding=20,
        content=ft.Column(spacing=15, controls=[
            ft.Row(spacing=10, controls=[appear_icon, appear_title]),
            ft.Container(height=5),
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[theme_row_label, theme_btn]),
            appear_divider_1,
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[accent_row_label, accent_btn]),
            appear_divider_2,
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[lang_row_label, lang_btn])
        ])
    )

    # ================================================================
    # PRIVACY ROW
    # ================================================================
    privacy_icon = ft.Icon(icon=ft.icons.Icons.SECURITY,
                            color=Colors.PRIMARY_TEAL, size=20)
    privacy_title = ft.Text(t("privacy_data"), size=16, color=Colors.PRIMARY_TEAL, weight="bold")
    privacy_arrow = ft.Icon(icon=ft.icons.Icons.ARROW_FORWARD,
                             color=Colors.PRIMARY_TEAL, size=20)

    settings_privacy = ft.Container(
        bgcolor=AppTheme.SURFACE,
        border=ft.Border.all(1, Colors.CARD_BORDER),
        border_radius=20,
        padding=20,
        ink=True,
        on_click=open_privacy_page,
        on_hover=btn_hover,
        animate_scale=ft.Animation(200, "easeOut"),
        scale=1.0,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=10, controls=[privacy_icon, privacy_title]),
                privacy_arrow
            ]
        )
    )

    # ================================================================
    # REPAINT — called by ThemeManager when theme/accent changes
    # ================================================================
    def repaint():
        C = AppTheme

        # Settings page background
        settings_scroll_col.bgcolor = C.BACKGROUND
        privacy_page.bgcolor = C.BACKGROUND

        # Lens Profile card
        settings_lens_profile.bgcolor = C.LIGHT_TEAL
        lens_profile_icon.color = C.PRIMARY_TEAL
        lens_profile_title.color = C.PRIMARY_TEAL
        max_wear_label.color = C.TEXT_HINT
        lens_start_label.color = C.TEXT_HINT
        duration_text.color = C.PRIMARY_TEAL
        start_date_text.color = C.TEXT_DARK
        duration_badge.bgcolor = C.PROGRESS_BG

        # Notifications
        settings_notifications.bgcolor = C.SURFACE
        settings_notifications.border = ft.Border.all(1, C.CARD_BORDER)
        notif_icon.color = C.PRIMARY_TEAL
        notif_title.color = C.PRIMARY_TEAL
        daily_label.color = C.TEXT_HINT
        alert_label.color = C.TEXT_HINT
        daily_reminder_switch.active_color = C.PRIMARY_TEAL
        replacement_alert_switch.active_color = C.PRIMARY_TEAL

        # Appearance
        settings_appearance.bgcolor = C.SURFACE
        settings_appearance.border = ft.Border.all(1, C.CARD_BORDER)
        appear_icon.color = C.PRIMARY_TEAL
        appear_title.color = C.PRIMARY_TEAL
        theme_row_label.color = C.TEXT_HINT
        accent_row_label.color = C.TEXT_HINT
        lang_row_label.color = C.TEXT_HINT
        theme_btn.bgcolor = C.LIGHT_TEAL
        theme_label.color = C.PRIMARY_TEAL
        theme_label.value = "Dark" if C.is_dark else "Light"
        theme_icon.color = C.PRIMARY_TEAL
        theme_icon.icon = (ft.icons.Icons.DARK_MODE if C.is_dark
                           else ft.icons.Icons.LIGHT_MODE_OUTLINED)
        accent_btn.bgcolor = C.LIGHT_TEAL
        accent_icon.color = C.PRIMARY_TEAL
        accent_label.color = C.PRIMARY_TEAL
        accent_chips_row.controls = build_accent_chips()
        
        lang_btn.bgcolor = C.LIGHT_TEAL
        lang_icon.color = C.PRIMARY_TEAL
        lang_label.color = C.PRIMARY_TEAL

        # Privacy row
        settings_privacy.bgcolor = C.SURFACE
        settings_privacy.border = ft.Border.all(1, C.CARD_BORDER)
        privacy_icon.color = C.PRIMARY_TEAL
        privacy_title.color = C.PRIMARY_TEAL
        privacy_arrow.color = C.PRIMARY_TEAL
        privacy_topbar.bgcolor = C.SURFACE

        # Header texts
        settings_header_title.color = C.PRIMARY_TEAL
        settings_header_subtitle.color = C.TEXT_HINT
        
        # Translate dynamically
        privacy_topbar_title.value = t("privacy_data")
        duration_text.value = f"{profile_radio.value} {t('days_short')}"
        if start_date_text.value in ["Not Started", "Не начато", "Non démarré", "Nicht gestartet"]:
            start_date_text.value = t("not_started")
        
        lens_profile_title.value = t("lens_profile")
        max_wear_label.value = t("max_wear_duration")
        lens_start_label.value = t("current_lens_start")
        profile_radio.content.controls[0].label = f"7 {t('days')}"
        profile_radio.content.controls[1].label = f"14 {t('days')}"
        profile_radio.content.controls[2].label = f"30 {t('days')}"
        profile_dialog.title.value = t("select_lens_duration")
        profile_dialog.actions[0].text = t("close")

        notif_title.value = t("notifications")
        daily_label.value = t("daily_reminder")
        alert_label.value = t("replacement_alert")
        
        appear_title.value = t("appearance")
        theme_row_label.value = t("theme")
        accent_row_label.value = t("accent_color")
        lang_row_label.value = t("language")
        
        theme_label.value = t("dark") if C.is_dark else t("light")
        accent_dialog.title.value = t("choose_accent")
        accent_dialog_desc.value = t("select_palette")
        accent_dialog.actions[0].text = t("done")

        lang_dialog.title.value = t("select_language")
        lang_dialog.actions[0].text = t("close")

        privacy_title.value = t("privacy_data")
        settings_header_title.value = t("settings_title")
        settings_header_subtitle.value = t("settings_desc")

    ThemeManager.register(repaint)

    # ================================================================
    # REFRESH (lens start date — called by main.py on tab switch)
    # ================================================================
    async def refresh_settings():
        raw_s = await page.prefs.get("lens_start_date")
        val_s = json.loads(raw_s) if raw_s else ""
        start_date_text.value = val_s if val_s else t("not_started")
        start_date_text.update()

    # ================================================================
    # ASSEMBLE
    # ================================================================
    settings_header_title = ft.Text(t("settings_title"), size=28,
                                     color=Colors.PRIMARY_TEAL, weight="w500")
    settings_header_subtitle = ft.Text(t("settings_desc"), size=14,
                                        color=Colors.TEXT_HINT)

    settings_scroll_col = ft.Column(
        expand=True,
        scroll="hidden",
        controls=[
            ft.Container(
                padding=ft.Padding.only(left=20, right=20, top=60, bottom=10),
                content=ft.Column(spacing=2, controls=[
                    settings_header_title,
                    settings_header_subtitle
                ])
            ),
            ft.Container(
                padding=ft.Padding.only(left=20, right=20, bottom=20),
                content=ft.Column(spacing=15, controls=[
                    settings_lens_profile,
                    settings_notifications,
                    settings_appearance,
                    settings_privacy
                ])
            )
        ]
    )

    settings_view = ft.Stack(
        expand=True,
        visible=False,
        controls=[
            settings_scroll_col,
            privacy_page,
        ]
    )

    settings_view.data = {"refresh": refresh_settings}
    return settings_view
