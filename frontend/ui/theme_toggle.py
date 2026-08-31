"""GoodCat 白天與深夜模式單鍵切換。"""

from __future__ import annotations

import streamlit as st


THEME_TOGGLE_HTML = """
<button id="goodcat-theme-toggle" type="button"></button>
"""


THEME_TOGGLE_CSS = """
#goodcat-theme-toggle {
    min-height: 2.25rem;
    padding: 0.35rem 0.75rem;
    border: 1px solid var(--st-widget-border-color);
    border-radius: var(--st-button-radius);
    color: var(--st-text-color);
    background: var(--st-background-color);
    font: inherit;
    font-size: 0.875rem;
    line-height: 1.2;
    white-space: nowrap;
    cursor: pointer;
}

#goodcat-theme-toggle:hover {
    color: var(--st-primary-color);
    border-color: var(--st-primary-color);
}

#goodcat-theme-toggle:focus-visible {
    outline: 2px solid var(--st-primary-color);
    outline-offset: 2px;
}
"""


THEME_TOGGLE_JS = r"""
export default function (component) {
  const { parentElement } = component
  const button = parentElement.querySelector("#goodcat-theme-toggle")
  if (!button) return

  const pageIsDark = () => {
    const channels = getComputedStyle(document.body)
      .backgroundColor.match(/[\d.]+/g)
      ?.slice(0, 3)
      .map(Number)
    if (!channels || channels.length !== 3) return false

    const [red, green, blue] = channels
    return (red * 0.299 + green * 0.587 + blue * 0.114) < 128
  }

  let nextTarget = pageIsDark() ? "Light" : "Dark"

  const updateButton = () => {
    const targetsDark = nextTarget === "Dark"
    const label = targetsDark ? "深夜模式" : "白天模式"
    const icon = targetsDark ? "☾" : "☀"
    const ariaLabel = `切換為${label}`

    button.textContent = `${icon} ${label}`
    button.setAttribute("aria-label", ariaLabel)
    button.title = ariaLabel
  }

  updateButton()

  button.onclick = () => {
    const url = new URL(window.location.href)
    const retainedEmbedOptions = url.searchParams
      .getAll("embed_options")
      .filter(
        (value) => value !== "light_theme" && value !== "dark_theme"
      )
    url.searchParams.delete("embed_options")
    retainedEmbedOptions.forEach((value) => {
      url.searchParams.append("embed_options", value)
    })
    url.searchParams.append(
      "embed_options",
      nextTarget === "Dark" ? "dark_theme" : "light_theme"
    )
    window.location.replace(url.toString())
  }
}
"""


_THEME_TOGGLE = st.components.v2.component(
    "goodcat_theme_toggle",
    html=THEME_TOGGLE_HTML,
    css=THEME_TOGGLE_CSS,
    js=THEME_TOGGLE_JS,
)


def render_theme_toggle() -> None:
    """呈現不依賴主選單的 Streamlit 原生模式切換。"""

    _THEME_TOGGLE(
        key="goodcat-theme-toggle",
        width="content",
        height="content",
        on_changed_change=lambda: None,
    )
