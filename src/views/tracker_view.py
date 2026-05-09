import flet as ft
from core.theme import Colors, AppTheme, ThemeManager, Layouts
import time
import asyncio
from datetime import datetime, timedelta
import json
from core.localization import Locales, t

def _get_current_date_str() -> str:
    now = datetime.now()
    day = now.day
    day_name = t(now.strftime("%A").lower())
    month_name = t(now.strftime("%B").lower())
    if Locales.current_lang == "en":
        suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return f"{day_name}, {month_name} {day}{suffix}"
    else:
        return f"{day_name}, {day} {month_name}"

async def get_tracker_view(page: ft.Page) -> ft.Column:

    # ── HEADER ─────────────────────────────────────────────────────────────
    title_part1 = ft.Text("Lens", size=24, color=AppTheme.PRIMARY_TEAL, weight="w500")
    title_part2 = ft.Text("Track", size=24, color=AppTheme.PRIMARY_TEAL, weight="w900")
    date_text = ft.Text(_get_current_date_str(), size=13, color=AppTheme.TEXT_MUTED)

    timer_icon = ft.Icon(icon=ft.icons.Icons.TIMER_OUTLINED, color=AppTheme.PRIMARY_TEAL)
    timer_icon_container = ft.Container(
        width=50, height=50,
        bgcolor=AppTheme.ICON_BG,
        border_radius=25,
        alignment=Layouts.CENTER,
        content=timer_icon,
        ink=True,
        on_click=lambda e: open_time_picker(e),
    )

    header = ft.Container(
        padding=ft.Padding.only(left=20, right=20, top=60, bottom=10),
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Row(spacing=0, controls=[title_part1, title_part2]),
                        date_text
                    ]
                ),
                timer_icon_container
            ]
        )
    )

    # ── SESSION TIMER ──────────────────────────────────────────────────────
    def create_digit_stack(digit_val):
        t = ft.Text(str(digit_val), size=48, color=AppTheme.PRIMARY_TEAL, weight="w600", font_family="Varela Round", text_align="center")
        dot = ft.Container(
            width=10, height=10, border_radius=5, bgcolor=AppTheme.PRIMARY_TEAL,
            visible=True
        )
        return ft.Stack(
            width=40, height=64,
            controls=[
                ft.Container(content=t, width=40, height=64, alignment=Layouts.CENTER),
                ft.Container(content=dot, width=40, height=64, alignment=Layouts.CENTER)
            ]
        )

    timer_digits = [create_digit_stack("0") for _ in range(6)]

    def update_timer_ui(hours, mins, secs):
        h_str = f"{hours:02d}"
        m_str = f"{mins:02d}"
        s_str = f"{secs:02d}"
        timer_digits[0].controls[0].content.value = h_str[0]
        timer_digits[1].controls[0].content.value = h_str[1]
        timer_digits[2].controls[0].content.value = m_str[0]
        timer_digits[3].controls[0].content.value = m_str[1]
        timer_digits[4].controls[0].content.value = s_str[0]
        timer_digits[5].controls[0].content.value = s_str[1]
        page.update()

    def toggle_dots(visible):
        for digit in timer_digits:
            digit.controls[1].content.visible = visible
        page.update()

    def btn_hover(e):
        e.control.scale = 0.95 if e.data == "true" else 1.0
        e.control.update()

    # Session State
    is_session_active = False
    session_elapsed_seconds = 0
    start_time_epoch = 0.0
    raw_start_time = await page.prefs.get("session_start_time")
    if raw_start_time:
        start_time_epoch = float(json.loads(raw_start_time))

    # Time Picker
    async def handle_time_picker_change(e):
        nonlocal session_elapsed_seconds, start_time_epoch
        if time_picker.value:
            selected_time = time_picker.value
            total_seconds = selected_time.hour * 3600 + selected_time.minute * 60
            if is_session_active:
                start_time_epoch = time.time() - total_seconds
                await page.prefs.set("session_start_time", json.dumps(start_time_epoch))
            else:
                session_elapsed_seconds = total_seconds
                update_timer_ui(selected_time.hour, selected_time.minute, 0)
                toggle_dots(False)
        page.update()

    time_picker = ft.TimePicker(confirm_text="OK", cancel_text="Cancel", help_text="Enter time", on_change=handle_time_picker_change)
    page.overlay.append(time_picker)

    def open_time_picker(e):
        time_picker.open = True
        page.update()

    async def timer_loop():
        nonlocal session_elapsed_seconds, start_time_epoch
        while is_session_active:
            current = time.time()
            session_elapsed_seconds = int(current - start_time_epoch)
            hours, mins, secs = session_elapsed_seconds // 3600, (session_elapsed_seconds % 3600) // 60, session_elapsed_seconds % 60
            
            raw_reminder = await page.prefs.get("daily_reminder")
            daily_reminder = json.loads(raw_reminder) if raw_reminder else False
            if hours == 10 and mins == 0 and secs == 0 and daily_reminder:
                page.snack_bar = ft.SnackBar(ft.Text(t("ten_hours_snack")))
                page.snack_bar.open = True
                try:
                    await page.notifications.show_notification(
                        notification_id=1,
                        title="LensTrack",
                        body=t("ten_hours_snack")
                    )
                except Exception:
                    pass

            update_timer_ui(hours, mins, secs)
            update_health_tip(hours_worn=hours, days_remaining=remaining_days)
            await asyncio.sleep(1)

    if start_time_epoch > 0:
        is_session_active = True
        toggle_dots(False)
        # page.run_task(timer_loop) moved to end of function to avoid NameError

    session_btn_icon = ft.Icon(icon=ft.icons.Icons.PLAY_ARROW_ROUNDED, color=AppTheme.ON_PRIMARY, size=26)
    session_btn_text = ft.Text(t("start_session"), color=AppTheme.ON_PRIMARY, size=18, weight="w500")

    async def toggle_session(e):
        nonlocal is_session_active, start_time_epoch, session_elapsed_seconds
        if not is_session_active:
            is_session_active = True
            start_time_epoch = time.time() - session_elapsed_seconds
            await page.prefs.set("session_start_time", json.dumps(start_time_epoch))
            session_btn_container.bgcolor = "#E57373"
            session_btn_icon.icon = ft.icons.Icons.STOP_ROUNDED
            session_btn_text.value = t("stop_session")
            toggle_dots(False)
            page.update()
            page.run_task(timer_loop)
        else:
            page.dialog = stop_session_dialog
            stop_session_dialog.open = True
            page.update()

    async def confirm_stop_session(e):
        nonlocal is_session_active, start_time_epoch, session_elapsed_seconds
        stop_session_dialog.open = False
        is_session_active = False
        
        if start_time_epoch > 0:
            session_elapsed_seconds = int(time.time() - start_time_epoch)
            
        raw_history = await page.prefs.get("usage_history")
        history = json.loads(raw_history) if raw_history else []
        today = datetime.now()
        hours = session_elapsed_seconds // 3600
        mins = (session_elapsed_seconds % 3600) // 60
        history.insert(0, {"day": today.strftime("%A"), "date": today.strftime("%b %d"), "hours": str(hours), "mins": str(mins)})
        await page.prefs.set("usage_history", json.dumps(history))
        
        await page.prefs.remove("session_start_time")
        start_time_epoch = 0
        session_elapsed_seconds = 0
        update_timer_ui(0, 0, 0)
        toggle_dots(True)
        
        session_btn_container.bgcolor = AppTheme.DARK_CARD
        session_btn_icon.icon = ft.icons.Icons.PLAY_ARROW_ROUNDED
        session_btn_text.value = t("start_session")
        update_health_tip(hours_worn=0, days_remaining=remaining_days)
        page.update()

    def cancel_stop_session(e):
        stop_session_dialog.open = False
        page.update()

    stop_session_dialog = ft.AlertDialog(
        modal=True, title=ft.Text(t("stop_session_title")), content=ft.Text(t("stop_session_content")),
        actions=[ft.TextButton(t("yes"), on_click=confirm_stop_session), ft.TextButton(t("no"), on_click=cancel_stop_session)],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(stop_session_dialog)

    session_btn_container = ft.Container(
        bgcolor=AppTheme.DARK_CARD, border_radius=20, height=60, alignment=Layouts.CENTER, ink=True,
        on_click=toggle_session, on_hover=btn_hover, animate_scale=ft.Animation(200, "easeOut"), scale=1.0,
        content=ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=10, controls=[session_btn_icon, session_btn_text])
    )

    if is_session_active:
        session_btn_container.bgcolor = "#E57373"
        session_btn_icon.icon = ft.icons.Icons.STOP_ROUNDED
        session_btn_text.value = t("stop_session")

    daily_wear_label = ft.Text(t("daily_wear_time"), color=AppTheme.MID_TEAL, weight="bold", size=13)
    colon1 = ft.Container(content=ft.Text(":", size=40, color=AppTheme.TEXT_MUTED, weight="w600", text_align="center"), width=16, alignment=Layouts.CENTER)
    colon2 = ft.Container(content=ft.Text(":", size=40, color=AppTheme.TEXT_MUTED, weight="w600", text_align="center"), width=16, alignment=Layouts.CENTER)

    daily_wear_card = ft.Container(
        bgcolor=AppTheme.LIGHT_TEAL, border_radius=25, padding=25,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=25,
            controls=[
                daily_wear_label,
                ft.Row(alignment=ft.MainAxisAlignment.CENTER, spacing=4, controls=[
                    timer_digits[0], timer_digits[1], colon1, timer_digits[2], timer_digits[3], colon2, timer_digits[4], timer_digits[5]
                ]),
                session_btn_container
            ]
        )
    )

    # ── REPLACEMENT CARD ───────────────────────────────────────────────────
    async def try_schedule_replacement_alert():
        raw_alert = await page.prefs.get("replacement_alert")
        if not (json.loads(raw_alert) if raw_alert else False):
            return
            
        raw_start = await page.prefs.get("lens_start_date")
        st = json.loads(raw_start) if raw_start else ""
        raw_dur = await page.prefs.get("lens_duration_days")
        dur = int(json.loads(raw_dur)) if raw_dur else 14
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

    async def calculate_replacement():
        raw_start = await page.prefs.get("lens_start_date")
        start_date_str = json.loads(raw_start) if raw_start else ""
        raw_dur = await page.prefs.get("lens_duration_days")
        duration = int(json.loads(raw_dur)) if raw_dur else 14
        if not start_date_str:
            return duration, duration
        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            today = datetime.now().date()
            elapsed = (today - start_date).days
            return duration, max(0, duration - elapsed)
        except:
            return duration, duration
            
    total_days, remaining_days = await calculate_replacement()
    elapsed_days = total_days - remaining_days
    remaining_text = ft.Text(str(remaining_days), color=AppTheme.ON_PRIMARY, size=32, weight="bold")
    progress_val = elapsed_days / total_days if total_days > 0 else 0.0

    percent_text = ft.Text(f"{int(progress_val*100)}%", color=AppTheme.ON_PRIMARY, size=12, weight="w500")
    replacement_label = ft.Text(t("replacement"), color=AppTheme.ON_PRIMARY, size=12, weight="w300")
    days_left_label = ft.Text(t("days_left"), color=AppTheme.ON_PRIMARY, size=14)
    
    progress_ring = ft.ProgressRing(width=60, height=60, stroke_width=4, color=AppTheme.LIGHT_TEAL, bgcolor=AppTheme.PROGRESS_BG, value=progress_val)

    replacement_card = ft.Container(
        bgcolor=AppTheme.DARK_CARD, border_radius=25, padding=20, height=150, expand=3,
        content=ft.Column(
            spacing=10,
            controls=[
                replacement_label,
                ft.Row(
                    spacing=15,
                    controls=[
                        ft.Stack(width=60, height=60, controls=[progress_ring, ft.Container(width=60, height=60, alignment=Layouts.CENTER, content=percent_text)]),
                        ft.Column(spacing=0, controls=[ft.Row(spacing=5, controls=[remaining_text]), days_left_label])
                    ]
                )
            ]
        )
    )

    # ── REPLACE ACTION ─────────────────────────────────────────────────────
    async def handle_replace_confirm(e):
        replace_dialog.open = False
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        await page.prefs.set("lens_start_date", json.dumps(current_date_str))
        await try_schedule_replacement_alert()
        tot, rem = await calculate_replacement()
        elapsed = tot - rem
        remaining_text.value = str(rem)
        progress_val = elapsed / tot if tot > 0 else 0.0
        progress_ring.value = progress_val
        percent_text.value = f"{int(progress_val*100)}%"
        update_health_tip(hours_worn=session_elapsed_seconds // 3600, days_remaining=rem)
        page.update()

    replace_dialog = ft.AlertDialog(
        modal=True, title=ft.Text(t("replace_dialog_title")), content=ft.Text(t("replace_dialog_content")),
        actions=[ft.TextButton(t("yes"), on_click=handle_replace_confirm), ft.TextButton(t("no"), on_click=lambda e: setattr(replace_dialog, 'open', False) or page.update())],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(replace_dialog)

    # ── ACTIVE / PAUSED ACTION ─────────────────────────────────────────────
    raw_paused = await page.prefs.get("lens_is_paused")
    is_paused = json.loads(raw_paused) if raw_paused else False

    async def on_active_toggle(e):
        nonlocal is_paused
        is_paused = not is_paused
        await page.prefs.set("lens_is_paused", json.dumps(is_paused))
        
        err_bg = "#5C1D1D" if AppTheme.is_dark else "#f8d7d5"
        err_fg = "#FFB4AB" if AppTheme.is_dark else "#E54545"

        if is_paused:
            active_btn_container.bgcolor = err_bg
            active_btn_icon.icon = ft.icons.Icons.PLAY_ARROW_ROUNDED
            active_btn_icon.color = err_fg 
            active_btn_text.value = t("paused")
            active_btn_text.color = err_fg
            active_btn_container.border = ft.Border.all(1, err_bg)
        else:
            active_btn_container.bgcolor = AppTheme.SURFACE
            active_btn_icon.icon = ft.icons.Icons.PAUSE
            active_btn_icon.color = AppTheme.PRIMARY_TEAL
            active_btn_text.value = t("active")
            active_btn_text.color = AppTheme.PRIMARY_TEAL
            active_btn_container.border = ft.Border.all(1, AppTheme.CARD_BORDER)
        page.update()

    def active_btn_hover(e):
        e.control.scale = 0.95 if e.data == "true" else 1.0
        err_bg = "#5C1D1D" if AppTheme.is_dark else "#f8d7d5"
        err_bg_hover = "#7A2727" if AppTheme.is_dark else "#f8b6ae"
        if is_paused:
            e.control.bgcolor = err_bg_hover if e.data == "true" else err_bg
        e.control.update()

    err_bg_init = "#5C1D1D" if AppTheme.is_dark else "#f8d7d5"
    err_fg_init = "#FFB4AB" if AppTheme.is_dark else "#E54545"

    active_btn_icon = ft.Icon(icon=ft.icons.Icons.PLAY_ARROW_ROUNDED if is_paused else ft.icons.Icons.PAUSE, 
                              color=err_fg_init if is_paused else AppTheme.PRIMARY_TEAL, size=24)
    active_btn_text = ft.Text(t("paused") if is_paused else t("active"), 
                              color=err_fg_init if is_paused else AppTheme.PRIMARY_TEAL, size=11, weight="w600")
    active_btn_container = ft.Container(
        bgcolor=err_bg_init if is_paused else AppTheme.SURFACE, 
        border=ft.Border.all(1, err_bg_init if is_paused else AppTheme.CARD_BORDER), 
        border_radius=25, height=70, alignment=Layouts.CENTER, ink=True,
        on_click=on_active_toggle, on_hover=active_btn_hover, animate_scale=ft.Animation(200, "easeOut"), scale=1.0,
        content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3, controls=[active_btn_icon, active_btn_text])
    )

    replace_btn_icon = ft.Icon(icon=ft.icons.Icons.RESTORE, color=AppTheme.PRIMARY_TEAL, size=24)
    replace_btn_text = ft.Text(t("replace"), color=AppTheme.PRIMARY_TEAL, size=11, weight="w600")
    replace_btn_container = ft.Container(
        bgcolor=AppTheme.HEALTH_TIP_BG, border_radius=25, height=70, alignment=Layouts.CENTER, ink=True,
        on_click=lambda e: setattr(replace_dialog, 'open', True) or page.update(), on_hover=btn_hover, animate_scale=ft.Animation(200, "easeOut"), scale=1.0,
        content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3, controls=[replace_btn_icon, replace_btn_text])
    )

    action_buttons = ft.Column(spacing=10, expand=2, controls=[replace_btn_container, active_btn_container])

    # ── FIRST RUN ONBOARDING ─────────────────────────────────────────────
    raw_lens_start = await page.prefs.get("lens_start_date")
    lens_start_date_val = json.loads(raw_lens_start) if raw_lens_start else ""
    is_first_run = (lens_start_date_val == "")

    async def on_start_tracking(e):
        nonlocal is_first_run, lens_start_date_val
        is_first_run = False
        lens_start_date_val = datetime.now().strftime("%Y-%m-%d")
        await page.prefs.set("lens_start_date", json.dumps(lens_start_date_val))
        await try_schedule_replacement_alert()
        tot, rem = await calculate_replacement()
        elapsed = tot - rem
        remaining_text.value = str(rem)
        pv = elapsed / tot if tot > 0 else 0.0
        progress_ring.value = pv
        percent_text.value = f"{int(pv*100)}%"
        start_tracking_btn.visible = False
        action_buttons.visible = True
        page.update()

    start_tracking_btn_icon = ft.Icon(icon=ft.icons.Icons.PLAY_CIRCLE_OUTLINE, color=AppTheme.ON_PRIMARY, size=32)
    start_tracking_btn_text = ft.Text(t("start_tracking"), color=AppTheme.ON_PRIMARY, size=13, weight="w600", text_align=ft.TextAlign.CENTER)
    start_tracking_btn = ft.Container(
        visible=is_first_run, bgcolor=AppTheme.PRIMARY_TEAL, border_radius=25, height=150, expand=2, alignment=Layouts.CENTER, ink=True,
        on_click=on_start_tracking, on_hover=btn_hover, animate_scale=ft.Animation(200, "easeOut"), scale=1.0,
        content=ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8, controls=[start_tracking_btn_icon, start_tracking_btn_text])
    )

    action_buttons.visible = not is_first_run
    stats_row = ft.Row(spacing=10, vertical_alignment=ft.CrossAxisAlignment.START, controls=[replacement_card, start_tracking_btn, action_buttons])

    # ── HEALTH TIP ───────────────────────────────────────────────────────
    health_tip_dot = ft.Container(width=8, height=8, border_radius=4, bgcolor=AppTheme.HEALTH_TIP_DOT)
    health_tip_label = ft.Text(t("health_tip"), color=AppTheme.HEALTH_TIP_DOT, size=12, weight="bold")
    health_tip_body = ft.Text(t("health_tip_body"), color=AppTheme.HEALTH_TIP_TEXT, size=14)
    health_tip_column = ft.Column(spacing=10, controls=[ft.Row(spacing=8, controls=[health_tip_dot, health_tip_label]), health_tip_body])
    health_tip = ft.Container(bgcolor=AppTheme.HEALTH_TIP_BG, border=ft.Border.all(1, AppTheme.CARD_BORDER), border_radius=20, padding=20, content=health_tip_column)

    def update_health_tip(hours_worn: int, days_remaining: int, initial: bool = False):
        wear_exceeded = hours_worn >= 10
        days_exceeded = days_remaining == 0 and lens_start_date_val != ""
        if wear_exceeded or days_exceeded:
            msg = t("health_tip_wear_exceeded", hours=hours_worn) if wear_exceeded else t("health_tip_days_exceeded")
            err_fg = "#FFB4AB" if AppTheme.is_dark else "#B3261E"
            err_bg = "#5C1D1D" if AppTheme.is_dark else "#FCE8E8"
            health_tip_dot.bgcolor = err_fg
            health_tip_label.value = t("limit_exceeded")
            health_tip_label.color = err_fg
            health_tip_body.value = msg
            health_tip_body.color = err_fg
            health_tip.border = ft.Border.all(1, err_bg)
            health_tip.bgcolor = err_bg
        else:
            health_tip_dot.bgcolor = AppTheme.HEALTH_TIP_DOT
            health_tip_label.value = t("health_tip")
            health_tip_label.color = AppTheme.HEALTH_TIP_DOT
            health_tip_body.value = t("health_tip_body")
            health_tip_body.color = AppTheme.HEALTH_TIP_TEXT
            health_tip.border = ft.Border.all(1, AppTheme.CARD_BORDER)
            health_tip.bgcolor = AppTheme.HEALTH_TIP_BG
        if not initial:
            try:
                health_tip_column.update()
                health_tip.update()
            except Exception:
                pass

    update_health_tip(hours_worn=session_elapsed_seconds // 3600, days_remaining=remaining_days, initial=True)

    # ── THEME REPAINT CALLBACK ──────────────────────────────────────────
    def repaint():
        C = AppTheme
        # Header
        title_part1.color = C.PRIMARY_TEAL
        title_part2.color = C.PRIMARY_TEAL
        date_text.color = C.TEXT_MUTED
        timer_icon_container.bgcolor = C.ICON_BG
        timer_icon.color = C.PRIMARY_TEAL

        # Daily Wear Card
        daily_wear_card.bgcolor = C.LIGHT_TEAL
        daily_wear_label.color = C.MID_TEAL
        colon1.content.color = C.TEXT_MUTED
        colon2.content.color = C.TEXT_MUTED
        for digit in timer_digits:
            digit.controls[0].content.color = C.PRIMARY_TEAL
            digit.controls[1].content.bgcolor = C.PRIMARY_TEAL

        if not is_session_active:
            session_btn_container.bgcolor = C.DARK_CARD
        session_btn_text.color = C.ON_PRIMARY
        session_btn_icon.color = C.ON_PRIMARY

        # Replacement Card
        replacement_card.bgcolor = C.DARK_CARD
        replacement_label.color = C.ON_PRIMARY
        remaining_text.color = C.ON_PRIMARY
        days_left_label.color = C.ON_PRIMARY
        percent_text.color = C.ON_PRIMARY
        progress_ring.color = C.LIGHT_TEAL
        progress_ring.bgcolor = C.PROGRESS_BG

        # Replace Button
        replace_btn_container.bgcolor = C.HEALTH_TIP_BG
        replace_btn_icon.color = C.PRIMARY_TEAL
        replace_btn_text.color = C.PRIMARY_TEAL

        # Active Toggle Button
        err_bg = "#5C1D1D" if C.is_dark else "#f8d7d5"
        err_fg = "#FFB4AB" if C.is_dark else "#E54545"
        if not is_paused:
            active_btn_container.bgcolor = C.SURFACE
            active_btn_container.border = ft.Border.all(1, C.CARD_BORDER)
            active_btn_icon.color = C.PRIMARY_TEAL
            active_btn_text.color = C.PRIMARY_TEAL
        else:
            active_btn_container.bgcolor = err_bg
            active_btn_container.border = ft.Border.all(1, err_bg)
            active_btn_icon.color = err_fg
            active_btn_text.color = err_fg

        # Start Tracking Button
        start_tracking_btn.bgcolor = C.PRIMARY_TEAL
        start_tracking_btn_icon.color = C.ON_PRIMARY
        start_tracking_btn_text.color = C.ON_PRIMARY

        # Text strings for i18n
        date_text.value = _get_current_date_str()
        daily_wear_label.value = t("daily_wear_time")
        session_btn_text.value = t("stop_session") if is_session_active else t("start_session")
        stop_session_dialog.title.value = t("stop_session_title")
        stop_session_dialog.content.value = t("stop_session_content")
        stop_session_dialog.actions[0].text = t("yes")
        stop_session_dialog.actions[1].text = t("no")
        replacement_label.value = t("replacement")
        days_left_label.value = t("days_left")
        replace_dialog.title.value = t("replace_dialog_title")
        replace_dialog.content.value = t("replace_dialog_content")
        replace_dialog.actions[0].text = t("yes")
        replace_dialog.actions[1].text = t("no")
        replace_btn_text.value = t("replace")
        active_btn_text.value = t("paused") if is_paused else t("active")
        start_tracking_btn_text.value = t("start_tracking")

        # Health Tip
        health_tip.bgcolor = C.HEALTH_TIP_BG
        health_tip.border = ft.Border.all(1, C.CARD_BORDER)
        # Re-trigger update_health_tip to inherit correct colors and texts without logic duplication
        update_health_tip(hours_worn=session_elapsed_seconds // 3600, days_remaining=remaining_days, initial=True)

    ThemeManager.register(repaint)

    tracker_view = ft.Column(expand=True, scroll="hidden", controls=[
        header,
        ft.Container(padding=ft.Padding.only(left=20, right=20, bottom=20), content=ft.Column(spacing=15, controls=[daily_wear_card, stats_row, health_tip]))
    ])

    if is_session_active:
        page.run_task(timer_loop)

    return tracker_view
