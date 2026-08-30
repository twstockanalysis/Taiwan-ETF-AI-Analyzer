"""GoodCat 角色狀態與初學者共用呈現元件。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import streamlit as st


GOODCAT_ASSET_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "assets"
    / "goodcat"
)


class GoodCatState(str, Enum):
    """與計算邏輯無關的 GoodCat 畫面狀態。"""

    IDLE = "IDLE"
    ATTENTIVE = "ATTENTIVE"
    WORKING = "WORKING"
    READY = "READY"
    REWARD = "REWARD"
    CAUTION = "CAUTION"


@dataclass(frozen=True)
class GoodCatPresentation:
    """單一 GoodCat 狀態的公開呈現資料。"""

    state: GoodCatState
    label: str
    accessibility_text: str
    default_message: str
    asset_path: Path


def _presentation(
    state: GoodCatState,
    *,
    label: str,
    accessibility_text: str,
    default_message: str,
    asset_filename: str | None = None,
) -> GoodCatPresentation:
    return GoodCatPresentation(
        state=state,
        label=label,
        accessibility_text=(
            accessibility_text
        ),
        default_message=default_message,
        asset_path=(
            GOODCAT_ASSET_DIRECTORY
            / (
                asset_filename
                or (
                    "goodcat-"
                    f"{state.value.lower()}.png"
                )
            )
        ),
    )


GOODCAT_PRESENTATIONS = {
    GoodCatState.IDLE: _presentation(
        GoodCatState.IDLE,
        label="陪主人慢慢想",
        accessibility_text=(
            "灰白 GoodCat 趴在前腳上，"
            "用沒睡飽的慵懶眼神陪主人開始規劃。"
        ),
        default_message=(
            "主人慢慢來，咪會陪你把目標整理清楚。"
        ),
    ),
    GoodCatState.ATTENTIVE: _presentation(
        GoodCatState.ATTENTIVE,
        label="正在等主人",
        accessibility_text=(
            "灰白 GoodCat 抬起頭香箱坐，"
            "睜圓眼睛並將耳朵向前，"
            "有精神地聽主人輸入條件。"
        ),
        default_message=(
            "告訴咪領息月份、目標與現有持股就可以囉。"
        ),
        asset_filename="goodcat-attentive-v3.png",
    ),
    GoodCatState.WORKING: _presentation(
        GoodCatState.WORKING,
        label="正在仔細計算",
        accessibility_text=(
            "灰白 GoodCat 低下身查看前腳間的紙張，"
            "表示系統正在計算。"
        ),
        default_message=(
            "咪正在核對 ETF、整數股數與所需資金。"
        ),
    ),
    GoodCatState.READY: _presentation(
        GoodCatState.READY,
        label="結果準備好了",
        accessibility_text=(
            "灰白 GoodCat 站起並自然豎起尾巴，"
            "表示配置結果已完成。"
        ),
        default_message=(
            "算好囉！一起看看配置、理由與風險。"
        ),
    ),
    GoodCatState.REWARD: _presentation(
        GoodCatState.REWARD,
        label="工作完成，等主人獎勵",
        accessibility_text=(
            "灰白 GoodCat 開心睜大眼睛、豎起尾巴並抬起前腳，"
            "表示已完成計算，正期待主人給予獎勵；畫面不顯示食物。"
        ),
        default_message=(
            "咪完成工作囉！一起看結果，也別忘了咪的獎勵。"
        ),
        asset_filename="goodcat-reward-hero.png",
    ),
    GoodCatState.CAUTION: _presentation(
        GoodCatState.CAUTION,
        label="先注意這件事",
        accessibility_text=(
            "灰白 GoodCat 側放耳朵並用尾巴包住腳，"
            "平靜提醒有缺少資料、風險或尚缺金額。"
        ),
        default_message=(
            "這裡需要主人多留意，咪會把原因說清楚。"
        ),
    ),
}


def get_goodcat_presentation(
    state: GoodCatState | str,
) -> GoodCatPresentation:
    """取得穩定的角色呈現資料。"""

    try:
        normalized_state = (
            state
            if isinstance(state, GoodCatState)
            else GoodCatState(
                str(state).strip().upper()
            )
        )
    except ValueError as exc:
        raise ValueError(
            f"未知 GoodCat 狀態：{state}"
        ) from exc

    return GOODCAT_PRESENTATIONS[
        normalized_state
    ]


def render_goodcat_companion(
    state: GoodCatState | str,
    message: str | None = None,
    *,
    key: str | None = None,
    image_width: int = 148,
) -> None:
    """以原生 Streamlit 元件顯示有文字替代的角色卡。"""

    if image_width < 80:
        raise ValueError(
            "GoodCat 圖片寬度不可小於 80"
        )

    presentation = (
        get_goodcat_presentation(state)
    )
    rendered_message = (
        message.strip()
        if message is not None
        and message.strip()
        else presentation.default_message
    )

    with st.container(
        border=True,
        horizontal=True,
        vertical_alignment="center",
        gap="medium",
        key=key,
    ):
        st.image(
            presentation.asset_path,
            caption=None,
            width=image_width,
            output_format="PNG",
        )
        with st.container(gap="xsmall"):
            st.caption(
                presentation.label
            )
            st.markdown(
                f"**{rendered_message}**"
            )


def render_beginner_card(
    title: str,
    body: str,
    *,
    caption: str | None = None,
    icon: str | None = None,
    key: str | None = None,
) -> None:
    """顯示一次只說明一件事的初學者資訊卡。"""

    normalized_title = title.strip()
    normalized_body = body.strip()

    if not normalized_title:
        raise ValueError("資訊卡標題不可空白")

    if not normalized_body:
        raise ValueError("資訊卡內容不可空白")

    heading = (
        f"{icon} {normalized_title}"
        if icon
        else normalized_title
    )

    with st.container(border=True, key=key):
        st.subheader(heading)
        st.write(normalized_body)

        if caption and caption.strip():
            st.caption(caption.strip())
