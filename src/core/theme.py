import flet as ft

# ── Accent palettes (Light & Dark for MD3) ───────────────────────────────────
# Format: (primary, light_bg, mid, icon_bg, dark_card, progress_bg)
ACCENT_PALETTES = {
    "Teal": {
        "light": ("#10675B", "#e5efee", "#4A9488", "#CDE6DF", "#10675B", "#CCE7E1"),
        "dark":  ("#80CBC4", "#182624", "#4DB6AC", "#004D40", "#00695C", "#00332E"),
    },
    "Blue": {
        "light": ("#1565C0", "#E3F2FD", "#1E88E5", "#BDD7F9", "#1565C0", "#BDD7F9"),
        "dark":  ("#90CAF9", "#1A212D", "#64B5F6", "#0D47A1", "#1565C0", "#092A5E"),
    },
    "Purple": {
        "light": ("#6A1B9A", "#F3E5F5", "#AB47BC", "#DFC5EF", "#6A1B9A", "#DFC5EF"),
        "dark":  ("#CE93D8", "#251B2D", "#BA68C8", "#4A148C", "#6A1B9A", "#300D5A"),
    },
    "Rose": {
        "light": ("#AD1457", "#FCE4EC", "#E91E63", "#F9BAD0", "#AD1457", "#F9BAD0"),
        "dark":  ("#F48FB1", "#2D1A22", "#F06292", "#880E4F", "#AD1457", "#560932"),
    },
    "Orange": {
        "light": ("#E65100", "#FFF3E0", "#FB8C00", "#FFCCAA", "#E65100", "#FFCCAA"),
        "dark":  ("#FFCC80", "#2D2016", "#FFB74D", "#E65100", "#F57C00", "#802D00"),
    },
    "Slate": {
        "light": ("#37474F", "#ECEFF1", "#607D8B", "#CFD8DC", "#37474F", "#CFD8DC"),
        "dark":  ("#B0BEC5", "#1A1D1F", "#90A4AE", "#263238", "#37474F", "#192125"),
    },
}

# ── Light / Dark base colours ──────────────────────────────────────────────────
_LIGHT = {
    "BACKGROUND":      "#F4F6F8",
    "SURFACE":         "#FFFFFF", # Light Card backgrounds
    "ON_PRIMARY":      "#FFFFFF", # Text on active/primary buttons
    "TEXT_DARK":       "#1A1A1A",
    "TEXT_MUTED":      "#6B7D7A",
    "TEXT_HINT":       "#4A5C59",
    "CARD_BORDER":     "#E5EAEA",
    "HEALTH_TIP_BG":   "#FAFCFB",
    "HEALTH_TIP_DOT":  "#4A9488",
    "HEALTH_TIP_TEXT": "#4A5D5A",
    "PROGRESS_BG":     "#E5EAEA",
}

_DARK = {
    "BACKGROUND":      "#121413", # MD3 dark neutral surface
    "SURFACE":         "#1E201F", # MD3 surface container (for light cards in dark mode)
    "ON_PRIMARY":      "#E1E3E1", # MD3 on-primary (text on dark primary cards)
    "TEXT_DARK":       "#E1E3E1", # MD3 on-surface
    "TEXT_MUTED":      "#8F918F", # MD3 on-surface-variant
    "TEXT_HINT":       "#717573", 
    "CARD_BORDER":     "#3F4140", # MD3 outline-variant
    "HEALTH_TIP_BG":   "#181A19", 
    "HEALTH_TIP_DOT":  "#80CBC4", # Will be overridden by mid color
    "HEALTH_TIP_TEXT": "#C3C7C5",
    "PROGRESS_BG":     "#2D312F",
}


class AppTheme:
    """Mutable singleton that holds the current theme state."""
    is_dark: bool = False
    accent_name: str = "Teal"

    # ── Resolved colours (updated by apply()) ──────────────────────────────────
    PRIMARY_TEAL:    str = "#10675B"
    SECONDARY_TEAL:  str = "#1A8275"
    LIGHT_TEAL:      str = "#e5efee"
    ICON_BG:         str = "#CDE6DF"
    MID_TEAL:        str = "#4A9488"
    DARK_CARD:       str = "#10675B"
    PROGRESS_BG:     str = "#CCE7E1"

    BACKGROUND:      str = "#F4F6F8"
    SURFACE:         str = "#FFFFFF"
    ON_PRIMARY:      str = "#FFFFFF"  
    WHITE:           str = "#FFFFFF" # Kept for backward compat but deprecated
    TEXT_DARK:       str = "#1A1A1A"
    TEXT_MUTED:      str = "#6B7D7A"
    TEXT_HINT:       str = "#4A5C59"
    CARD_BORDER:     str = "#E5EAEA"
    HEALTH_TIP_BG:   str = "#FAFCFB"
    HEALTH_TIP_DOT:  str = "#4A9488"
    HEALTH_TIP_TEXT: str = "#4A5D5A"

    @classmethod
    def apply(cls, page: ft.Page | None = None) -> None:
        """Recalculate all colour tokens and optionally push them to the Flet page."""
        base = _DARK if cls.is_dark else _LIGHT
        mode = "dark" if cls.is_dark else "light"
        
        pal_dict = ACCENT_PALETTES.get(cls.accent_name, ACCENT_PALETTES["Teal"])
        pal = pal_dict[mode]

        cls.PRIMARY_TEAL   = pal[0]
        cls.LIGHT_TEAL     = pal[1]
        cls.MID_TEAL       = pal[2]
        cls.ICON_BG        = pal[3]
        cls.DARK_CARD      = pal[4]
        cls.PROGRESS_BG    = pal[5]
        cls.SECONDARY_TEAL = pal[0]

        cls.BACKGROUND      = base["BACKGROUND"]
        cls.SURFACE         = base["SURFACE"]
        cls.ON_PRIMARY      = base["ON_PRIMARY"]
        cls.WHITE           = base["SURFACE"] # Legacy compat
        cls.TEXT_DARK       = base["TEXT_DARK"]
        cls.TEXT_MUTED      = base["TEXT_MUTED"]
        cls.TEXT_HINT       = base["TEXT_HINT"]
        cls.CARD_BORDER     = base["CARD_BORDER"]
        cls.HEALTH_TIP_BG   = base["HEALTH_TIP_BG"]
        cls.HEALTH_TIP_DOT  = pal[2] # Use mid color for the dot
        cls.HEALTH_TIP_TEXT = base["HEALTH_TIP_TEXT"]

        if page is not None:
            page.bgcolor = cls.BACKGROUND
            page.theme_mode = ft.ThemeMode.DARK if cls.is_dark else ft.ThemeMode.LIGHT
            page.theme = ft.Theme(color_scheme_seed=cls.PRIMARY_TEAL)
            page.dark_theme = ft.Theme(color_scheme_seed=cls.PRIMARY_TEAL)


Colors = AppTheme

class ThemeManager:
    """Registry of per-view repaint callbacks. Call notify_all() after AppTheme.apply()."""
    _callbacks: list = []

    @classmethod
    def register(cls, fn) -> None:
        cls._callbacks.append(fn)

    @classmethod
    def clear(cls) -> None:
        cls._callbacks.clear()

    @classmethod
    def notify_all(cls, page: "ft.Page") -> None:
        AppTheme.apply(page)
        for cb in cls._callbacks:
            try:
                cb()
            except Exception as e:
                print(f"Theme repaint error: {e}")
        page.update()

class Layouts:
    CENTER = ft.Alignment(0.0, 0.0)
