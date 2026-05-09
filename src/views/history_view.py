import flet as ft
from core.theme import Colors, AppTheme, ThemeManager
import json
from core.localization import t


async def get_history_view(page: ft.Page) -> ft.Column:
    # ── HEADER ─────────────────────────────────────────────────────────────
    title_text = ft.Text(t("history_title"), size=28, color=AppTheme.PRIMARY_TEAL, weight="w500")
    subtitle_text = ft.Text(t("history_subtitle"), size=14, color=AppTheme.TEXT_HINT)

    history_header = ft.Container(
        padding=ft.Padding.only(left=20, right=20, top=60, bottom=10),
        content=ft.Column(
            spacing=2,
            controls=[title_text, subtitle_text]
        )
    )

    # ── EMPTY STATE ────────────────────────────────────────────────────────
    empty_icon_container = ft.Container(
        width=72, height=72, border_radius=36, bgcolor=AppTheme.LIGHT_TEAL, alignment=ft.Alignment(0, 0),
        content=ft.Icon(icon=ft.icons.Icons.HISTORY, color=AppTheme.PRIMARY_TEAL, size=36)
    )
    empty_title = ft.Text(t("no_sessions"), size=18, color=AppTheme.PRIMARY_TEAL, weight="w600")
    empty_subtitle = ft.Text(t("no_sessions_desc"), size=14, color=AppTheme.TEXT_MUTED, text_align=ft.TextAlign.CENTER)

    empty_state = ft.Container(
        padding=ft.Padding.only(top=60),
        alignment=ft.Alignment(0, 0),
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=12,
            controls=[empty_icon_container, empty_title, empty_subtitle]
        )
    )

    history_list = ft.Column(spacing=10, controls=[])
    _current_history_data = []

    def build_history_items():
        history_list.controls.clear()
        if not _current_history_data:
            history_list.controls.append(empty_state)
            return

        for entry in _current_history_data:
            day = entry.get("day", "")
            date = entry.get("date", "")
            hours = str(entry.get("hours", "0"))
            mins = str(entry.get("mins", "0"))

            icon_c = ft.Container(
                width=40, height=40, border_radius=20, bgcolor=AppTheme.ICON_BG, alignment=ft.Alignment(0, 0),
                content=ft.Icon(icon=ft.icons.Icons.CHECK, color=AppTheme.PRIMARY_TEAL, size=20)
            )
            
            day_t = t(day.lower()) if day else ""
            date_t = date
            if date:
                parts = date.split(" ")
                if len(parts) == 2:
                    short_map = {"Jan": "january", "Feb": "february", "Mar": "march", "Apr": "april", "May": "may", "Jun": "june", "Jul": "july", "Aug": "august", "Sep": "september", "Oct": "october", "Nov": "november", "Dec": "december"}
                    full_m = short_map.get(parts[0], parts[0].lower())
                    date_t = f"{t(full_m)} {parts[1]}"
            
            text_day = ft.Text(day_t, size=16, color=AppTheme.TEXT_DARK, weight="w600")
            text_date = ft.Text(date_t, size=13, color=AppTheme.TEXT_MUTED)

            h_val = ft.Text(hours, size=18, color=AppTheme.PRIMARY_TEAL, weight="bold")
            h_lbl = ft.Text("h", size=14, color=AppTheme.MID_TEAL, weight="w500")
            m_val = ft.Text(mins, size=18, color=AppTheme.PRIMARY_TEAL, weight="bold")
            m_lbl = ft.Text("m", size=14, color=AppTheme.MID_TEAL, weight="w500")

            item_card = ft.Container(
                bgcolor=AppTheme.SURFACE,
                border=ft.Border.all(1, AppTheme.CARD_BORDER),
                border_radius=20,
                padding=15,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Row(spacing=15, controls=[icon_c, ft.Column(spacing=2, controls=[text_day, text_date])]),
                        ft.Row(spacing=2, controls=[h_val, h_lbl, ft.Container(width=4), m_val, m_lbl])
                    ]
                )
            )
            history_list.controls.append(item_card)

    async def refresh_history(initial: bool = False):
        nonlocal _current_history_data
        raw_history = await page.prefs.get("usage_history")
        _current_history_data = json.loads(raw_history) if raw_history else []
        build_history_items()
        if not initial:
            history_list.update()

    await refresh_history(initial=True)

    # ── THEME REPAINT CALLBACK ──────────────────────────────────────────
    def repaint():
        C = AppTheme
        title_text.color = C.PRIMARY_TEAL
        subtitle_text.color = C.TEXT_HINT
        title_text.value = t("history_title")
        subtitle_text.value = t("history_subtitle")

        empty_icon_container.bgcolor = C.LIGHT_TEAL
        empty_icon_container.content.color = C.PRIMARY_TEAL
        empty_title.color = C.PRIMARY_TEAL
        empty_subtitle.color = C.TEXT_MUTED
        empty_title.value = t("no_sessions")
        empty_subtitle.value = t("no_sessions_desc")

        # Rebuild history items so new instances get the latest C.* colors
        build_history_items()

    ThemeManager.register(repaint)

    # ── ASSEMBLE ───────────────────────────────────────────────────────────
    history_view = ft.Column(
        expand=True,
        scroll="hidden",
        controls=[
            history_header,
            ft.Container(
                padding=ft.Padding.only(left=20, right=20, bottom=20),
                content=history_list
            )
        ],
        visible=False
    )

    history_view.data = {"refresh": refresh_history}
    return history_view
