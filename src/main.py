# Copyright (C) 2026 anndrwww
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License v3.0

import flet as ft
import json
from core.theme import Colors, AppTheme, ThemeManager
from views.tracker_view import get_tracker_view
from views.history_view import get_history_view
from views.settings_view import get_settings_view
from core.localization import Locales, t
from flet_android_notifications import FletAndroidNotifications

async def main(page: ft.Page):
    page.title = "LensTrack"
    page.padding = 0
    ThemeManager.clear()
    
    # Initialize Android Notifications Service
    page.notifications = FletAndroidNotifications()
    
    # Load Custom Font
    page.fonts = {
        "Varela Round": "https://raw.githubusercontent.com/google/fonts/main/ofl/varelaround/VarelaRound-Regular.ttf"
    }



    # Initialize SharedPreferences service (required since Flet 0.90+)
    page.prefs = ft.SharedPreferences()

    # Initialize Local Storage Defaults
    if (await page.prefs.get("lens_duration_days")) is None:
        await page.prefs.set("lens_duration_days", json.dumps(14))
    
    if (await page.prefs.get("lens_start_date")) is None:
        await page.prefs.set("lens_start_date", json.dumps(""))

    if (await page.prefs.get("daily_reminder")) is None:
        await page.prefs.set("daily_reminder", json.dumps(False))

    if (await page.prefs.get("replacement_alert")) is None:
        await page.prefs.set("replacement_alert", json.dumps(False))

    if (await page.prefs.get("usage_history")) is None:
        await page.prefs.set("usage_history", json.dumps([]))

    # Load Theme Preferences before building views
    raw_is_dark = await page.prefs.get("theme_is_dark")
    AppTheme.is_dark = json.loads(raw_is_dark) if raw_is_dark else False

    raw_accent = await page.prefs.get("theme_accent")
    AppTheme.accent_name = json.loads(raw_accent) if raw_accent else "Teal"

    raw_lang = await page.prefs.get("app_language")
    Locales.current_lang = json.loads(raw_lang) if raw_lang else "en"

    # Resolve colors and inject into page before views render
    AppTheme.apply(page)

    # Load View Controls
    tracker_view = await get_tracker_view(page)
    history_view = await get_history_view(page)
    settings_view = await get_settings_view(page)

    main_container = ft.Stack(
        expand=True,
        controls=[
            tracker_view,
            history_view,
            settings_view
        ]
    )

    async def on_nav_change(e):
        index = e.control.selected_index
        tracker_view.visible = (index == 0)
        history_view.visible = (index == 1)
        settings_view.visible = (index == 2)
        # Refresh history list whenever user switches to the History tab
        if index == 1 and history_view.data and "refresh" in history_view.data:
            await history_view.data["refresh"]()
        # Refresh settings (e.g. Current Lens Start) when user switches to Settings tab
        if index == 2 and settings_view.data and "refresh" in settings_view.data:
            await settings_view.data["refresh"]()
        page.update()

    nav_bar = ft.NavigationBar(
        selected_index=0,
        on_change=on_nav_change,
        bgcolor=AppTheme.SURFACE,
        destinations=[
            ft.NavigationBarDestination(icon=ft.icons.Icons.TIMER_OUTLINED, selected_icon=ft.icons.Icons.TIMER, label=t("tracker")),
            ft.NavigationBarDestination(icon=ft.icons.Icons.HISTORY, label=t("history")),
            ft.NavigationBarDestination(icon=ft.icons.Icons.SETTINGS_OUTLINED, selected_icon=ft.icons.Icons.SETTINGS, label=t("settings")),
        ]
    )
    page.navigation_bar = nav_bar

    def repaint_main():
        nav_bar.bgcolor = AppTheme.SURFACE
        nav_bar.destinations[0].label = t("tracker")
        nav_bar.destinations[1].label = t("history")
        nav_bar.destinations[2].label = t("settings")
        # page.update is called by ThemeManager.notify_all automatically

    ThemeManager.register(repaint_main)
    
    #await page.shared_preferences.clear() # стирка для тестов
    page.add(main_container)

if __name__ == "__main__":
    # Updated to run() for flet 0.81.0, to prevent app() DeprecationWarning
    try:
        ft.run(main) # flet 0.81.0 preferred entrypoint
    except Exception as e:
        print(f"Error launching Flet: {e}")