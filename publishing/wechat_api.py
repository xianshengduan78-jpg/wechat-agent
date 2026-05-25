"""微信公众号 API 封装。

access_token → 素材上传 → 草稿创建/更新。
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

import requests

from config.settings import (
    WECHAT_APPID, WECHAT_APPSECRET,
    TOKEN_URL, MATERIAL_URL, UPLOAD_IMG_URL,
    DRAFT_ADD_URL, DRAFT_GET_URL, DRAFT_UPDATE_URL,
)

logger = logging.getLogger(__name__)


class WeChatClient:
    """微信公众平台 API 客户端。"""

    def __init__(self, appid: str = None, appsecret: str = None):
        self.appid = appid or WECHAT_APPID
        self.appsecret = appsecret or WECHAT_APPSECRET
        self._token = None
        self._token_expires = 0

    # ── Token ────────────────────────────────────────

    def get_access_token(self) -> str:
        """获取 access_token（自动缓存和刷新）。"""
        if self._token and time.time() < self._token_expires - 60:
            return self._token

        if not self.appid or not self.appsecret:
            raise ValueError("WECHAT_APPID 和 WECHAT_APPSECRET 未设置")

        try:
            resp = requests.get(TOKEN_URL, params={
                "grant_type": "client_credential",
                "appid": self.appid,
                "secret": self.appsecret,
            }, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            if "access_token" in data:
                self._token = data["access_token"]
                self._token_expires = time.time() + data.get("expires_in", 7200)
                logger.info("access_token 获取成功")
                return self._token
            else:
                raise RuntimeError(f"微信 API 错误: {data}")
        except Exception as e:
            logger.error("access_token 获取失败: %s", e)
            raise

    # ── 素材上传 ──────────────────────────────────────

    def upload_thumb_material(self, image_path: str, file_type: str = "image") -> Optional[str]:
        """上传封面图到永久素材，返回 thumb_media_id。"""
        token = self.get_access_token()
        try:
            with open(image_path, "rb") as f:
                files = {"media": (Path(image_path).name, f, "image/png")}
                resp = requests.post(
                    MATERIAL_URL,
                    params={"access_token": token, "type": file_type},
                    files=files,
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                if "media_id" in data:
                    logger.info("素材上传成功: %s", data["media_id"])
                    return data["media_id"]
                else:
                    logger.error("素材上传失败: %s", data)
                    return None
        except Exception as e:
            logger.error("素材上传异常: %s", e)
            return None

    def upload_article_image(self, image_path: str) -> Optional[str]:
        """上传正文图片，返回微信图片 URL。"""
        token = self.get_access_token()
        try:
            with open(image_path, "rb") as f:
                files = {"media": (Path(image_path).name, f, "image/png")}
                resp = requests.post(
                    UPLOAD_IMG_URL,
                    params={"access_token": token},
                    files=files,
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                if "url" in data:
                    logger.info("正文图片上传成功")
                    return data["url"]
                else:
                    logger.error("正文图片上传失败: %s", data)
                    return None
        except Exception as e:
            logger.error("正文图片上传异常: %s", e)
            return None

    # ── 草稿管理 ──────────────────────────────────────

    def create_draft(self, articles: list) -> Optional[str]:
        """创建草稿，返回 media_id。"""
        token = self.get_access_token()
        body = {"articles": articles}
        try:
            resp = requests.post(
                DRAFT_ADD_URL,
                params={"access_token": token},
                json=body,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            if "media_id" in data:
                logger.info("草稿创建成功: %s", data["media_id"])
                return data["media_id"]
            else:
                logger.error("草稿创建失败: %s", data)
                return None
        except Exception as e:
            logger.error("草稿创建异常: %s", e)
            return None

    def update_draft(self, media_id: str, articles: list) -> bool:
        """更新草稿。"""
        token = self.get_access_token()
        body = {"media_id": media_id, "articles": articles}
        try:
            resp = requests.post(
                DRAFT_UPDATE_URL,
                params={"access_token": token},
                json=body,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode") == 0:
                logger.info("草稿更新成功: %s", media_id)
                return True
            else:
                logger.error("草稿更新失败: %s", data)
                return False
        except Exception as e:
            logger.error("草稿更新异常: %s", e)
            return False
