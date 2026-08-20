from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QTabWidget, QMainWindow, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QGraphicsView, QVBoxLayout, QHBoxLayout, QSpacerItem, QPlainTextEdit, QSizePolicy, QGraphicsOpacityEffect, QFileDialog, QComboBox, QMenu, QTabBar
from PyQt6.QtCore import QSize, Qt, QTimer, QPropertyAnimation, QRegularExpression, pyqtSignal, QPoint, QEasingCurve, QSequentialAnimationGroup, QParallelAnimationGroup, QRect, QThread, QMutex, QUrl
from PyQt6.QtGui import QRegularExpressionValidator, QFont, QPainter, QPixmap, QIcon, QColor, QCursor, QIntValidator, QDesktopServices, QClipboard
from playerokapi.account import *
from playerokapi.listener.listener import *
from pathlib import Path
from playerokapi.types import *
from playerokapi.exceptions import *
from PyQt6.QtSvg import QSvgRenderer
from fake_useragent import UserAgent
from qasync import QApplication, QEventLoop
import platform 
import subprocess
import sys
import configparser
import os
import asyncio
import string

def svgToIcon(svgPath, size=QSize(32, 32)):
    renderer = QSvgRenderer(svgPath)
    pixmap = QPixmap(size)
    pixmap.fill(Qt.GlobalColor.transparent)
    
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    
    return QIcon(pixmap)


class CustomWidgetItem(QListWidgetItem):
    def __init__(self, item: Item, parent=None):
        super().__init__(parent)
        self.item_data = item
        self.item_status = item.status

        self.widget = QWidget()
        self.widget.setObjectName(str(item.id))
        self.layout = QHBoxLayout(self.widget)
        self.layout.setContentsMargins(10, 5, 10, 5)
        
        self.color_label = QLabel()
        self.layout.addWidget(self.color_label, 0, Qt.AlignmentFlag.AlignLeft)

        self.label = QLabel(self.item_data.name)
        self.layout.addWidget(self.label, 1, Qt.AlignmentFlag.AlignLeft)

        self.setData(Qt.ItemDataRole.UserRole, self.item_data)
        self.setData(Qt.ItemDataRole.DisplayRole, self.item_data.name)
        
        self.update_color(self.item_status)
        self.setSizeHint(self.widget.sizeHint())
    
    def update_color(self, status=None, custom_color=None):
        """Обновляет цвет индикатора"""
        if status is not None:
            self.item_status = status
        
        # Создаем новый pixmap
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        if painter.isActive():
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Выбираем цвет
            if custom_color:
                painter.setBrush(custom_color)
            elif self.item_status == ItemStatuses.APPROVED:
                painter.setBrush(QColor(0, 128, 0)) 
            elif self.item_status == ItemStatuses.BLOCKED:
                painter.setBrush(QColor(128, 0, 0)) 
            elif self.item_status in [ItemStatuses.DECLINED, ItemStatuses.DRAFT, ItemStatuses.EXPIRED]:
                painter.setBrush(QColor(128, 128, 128)) 
            elif self.item_status in [ItemStatuses.PENDING_APPROVAL, ItemStatuses.PENDING_MODERATION]:
                painter.setBrush(QColor(255, 215, 0)) 
            elif self.item_status == ItemStatuses.SOLD:
                painter.setBrush(QColor(70, 130, 180))
            else:
                painter.setBrush(QColor(128, 128, 128))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(2, 2, 16, 16)
            painter.end()
        
        self.color_label.setPixmap(pixmap)


class Animations:
    @staticmethod
    def minimize_window(widget, duration=400):
        """Анимация минимизации окна (для окон с WindowFlag)"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        
        start_rect = widget.geometry()
        end_rect = QRect(
            start_rect.x() + start_rect.width() // 2 - 5,
            start_rect.y(),
            10, 10
        )
        
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(QEasingCurve.Type.InBack)
        animation.finished.connect(lambda: widget.hide())
        return animation

    @staticmethod
    def fade_out_window(widget, duration=500):
        """Fade out для окон"""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        animation = QPropertyAnimation(effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.InCubic)
        
        def hide_and_remove():
            widget.hide()
            # Важно удалить effect после анимации
            widget.setGraphicsEffect(None)
        
        animation.finished.connect(hide_and_remove)
        return animation

    @staticmethod
    def slide_out_window(widget, direction="top", duration=400):
        """Анимация выезда окна в указанном направлении"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        
        start_rect = widget.geometry()
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        
        if direction == "top":
            end_rect = QRect(
                start_rect.x(),
                -start_rect.height(),
                start_rect.width(),
                start_rect.height()
            )
        elif direction == "bottom":
            end_rect = QRect(
                start_rect.x(),
                screen_geometry.height(),
                start_rect.width(),
                start_rect.height()
            )
        elif direction == "left":
            end_rect = QRect(
                -start_rect.width(),
                start_rect.y(),
                start_rect.width(),
                start_rect.height()
            )
        elif direction == "right":
            end_rect = QRect(
                screen_geometry.width(),
                start_rect.y(),
                start_rect.width(),
                start_rect.height()
            )
        
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(QEasingCurve.Type.InCubic)
        animation.finished.connect(lambda: widget.hide())
        return animation

    @staticmethod
    def fade_in(widget, duration=500):
        """Плавное появление виджета"""
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(0)
        animation.setEndValue(1)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        return animation

    @staticmethod
    def fade_out(widget, duration=500):
        """Плавное исчезновение виджета"""
        animation = QPropertyAnimation(widget, b"windowOpacity")
        animation.setDuration(duration)
        animation.setStartValue(1)
        animation.setEndValue(0)
        animation.setEasingCurve(QEasingCurve.Type.InCubic)
        return animation

    @staticmethod
    def slide_in_from_left(widget, duration=400):
        """Слайд-ин слева"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        start_rect = widget.geometry()
        end_rect = start_rect
        start_rect.moveLeft(-start_rect.width())
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(QEasingCurve.Type.OutBack)
        return animation

    @staticmethod
    def slide_in_from_right(widget, duration=400):
        """Слайд-ин справа"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        start_rect = widget.geometry()
        end_rect = start_rect
        start_rect.moveLeft(widget.parent().width() if widget.parent() else start_rect.width())
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(QEasingCurve.Type.OutBack)
        return animation

    @staticmethod
    def slide_in_from_top(widget, duration=400):
        """Слайд-ин сверху"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        start_rect = widget.geometry()
        end_rect = start_rect
        start_rect.moveTop(-start_rect.height())
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(QEasingCurve.Type.OutBack)
        return animation

    @staticmethod
    def slide_in_from_bottom(widget, duration=400):
        """Слайд-ин снизу"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        start_rect = widget.geometry()
        end_rect = start_rect
        parent_height = widget.parent().height() if widget.parent() else start_rect.height()
        start_rect.moveTop(parent_height)
        animation.setStartValue(start_rect)
        animation.setEndValue(end_rect)
        animation.setEasingCurve(QEasingCurve.Type.OutBack)
        return animation

    @staticmethod
    def scale_up(widget, duration=400):
        """Увеличение масштаба"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        start_rect = widget.geometry()
        center = start_rect.center()
        
        # Начальный размер - маленький
        start_rect.setWidth(10)
        start_rect.setHeight(10)
        start_rect.moveCenter(center)
        
        animation.setStartValue(start_rect)
        animation.setEndValue(widget.geometry())
        animation.setEasingCurve(QEasingCurve.Type.OutBack)
        return animation

    @staticmethod
    def bounce(widget, duration=600):
        """Прыгающая анимация"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        original_rect = widget.geometry()
        
        # Создаем ключевые кадры для bounce эффекта
        animation.setKeyValueAt(0, original_rect)
        animation.setKeyValueAt(0.3, original_rect.translated(0, -30))
        animation.setKeyValueAt(0.5, original_rect.translated(0, -15))
        animation.setKeyValueAt(0.7, original_rect.translated(0, -5))
        animation.setKeyValueAt(1, original_rect)
        
        animation.setEasingCurve(QEasingCurve.Type.OutBounce)
        return animation

    @staticmethod
    def shake(widget, duration=500):
        """Анимация тряски (для ошибок)"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        original_rect = widget.geometry()
        
        animation.setKeyValueAt(0, original_rect)
        animation.setKeyValueAt(0.1, original_rect.translated(-8, 0))
        animation.setKeyValueAt(0.2, original_rect.translated(8, 0))
        animation.setKeyValueAt(0.3, original_rect.translated(-8, 0))
        animation.setKeyValueAt(0.4, original_rect.translated(8, 0))
        animation.setKeyValueAt(0.5, original_rect.translated(-8, 0))
        animation.setKeyValueAt(0.6, original_rect.translated(8, 0))
        animation.setKeyValueAt(0.7, original_rect.translated(-4, 0))
        animation.setKeyValueAt(0.8, original_rect.translated(4, 0))
        animation.setKeyValueAt(0.9, original_rect.translated(-2, 0))
        animation.setKeyValueAt(1, original_rect)
        
        return animation

    @staticmethod
    def pulse(widget, duration=1000):
        """Пульсирующая анимация"""
        group = QParallelAnimationGroup()
        
        # Анимация размера
        size_anim = QPropertyAnimation(widget, b"geometry")
        size_anim.setDuration(duration)
        size_anim.setLoopCount(-1)  # Бесконечное повторение
        
        original_rect = widget.geometry()
        center = original_rect.center()
        
        # Создаем эффект пульсации
        size_anim.setKeyValueAt(0, original_rect)
        size_anim.setKeyValueAt(0.5, QWidget.geometry(widget).adjusted(-5, -5, 5, 5))
        size_anim.setKeyValueAt(1, original_rect)
        
        # Анимация прозрачности
        opacity_anim = QPropertyAnimation(widget, b"windowOpacity")
        opacity_anim.setDuration(duration)
        opacity_anim.setLoopCount(-1)
        opacity_anim.setKeyValueAt(0, 1)
        opacity_anim.setKeyValueAt(0.5, 0.7)
        opacity_anim.setKeyValueAt(1, 1)
        
        group.addAnimation(size_anim)
        group.addAnimation(opacity_anim)
        return group

    @staticmethod
    def flip_horizontal(widget, duration=800):
        """Анимация переворота по горизонтали (эффект 3D)"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        
        original_rect = widget.geometry()
        center_x = original_rect.center().x()
        
        # Имитация 3D переворота через изменение ширины
        animation.setKeyValueAt(0, original_rect)
        animation.setKeyValueAt(0.5, QWidget.geometry(widget).adjusted(20, 0, -20, 0))
        animation.setKeyValueAt(1, original_rect)
        
        animation.setEasingCurve(QEasingCurve.Type.InOutBack)
        return animation

    @staticmethod
    def color_change(widget, start_color, end_color, duration=500):
        """Плавное изменение цвета фона через стили CSS"""
        animation = QPropertyAnimation(widget, b"styleSheet")
        animation.setDuration(duration)
        
        start_style = f"background-color: {start_color};"
        end_style = f"background-color: {end_color};"
        
        animation.setStartValue(start_style)
        animation.setEndValue(end_style)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        return animation

    @staticmethod
    def rotate_3d(widget, duration=1000):
        """3D-вращение виджета"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        
        original_rect = widget.geometry()
        
        # Имитация 3D вращения через последовательное изменение размеров
        animation.setKeyValueAt(0, original_rect)
        animation.setKeyValueAt(0.25, original_rect.adjusted(10, 5, -10, -5))
        animation.setKeyValueAt(0.5, original_rect.adjusted(20, 2, -20, -2))
        animation.setKeyValueAt(0.75, original_rect.adjusted(10, 5, -10, -5))
        animation.setKeyValueAt(1, original_rect)
        
        animation.setEasingCurve(QEasingCurve.Type.InOutBack)
        return animation

    @staticmethod
    def typing_effect(widget, text, duration=1000):
        """Эффект печатания текста (для QLabel)"""
        animation = QPropertyAnimation(widget, b"text")
        animation.setDuration(duration)
        
        # Создаем эффект постепенного появления текста
        full_text = text
        steps = len(full_text)
        step_duration = duration / steps
        
        for i in range(steps + 1):
            animation.setKeyValueAt(i/steps, full_text[:i])
        
        return animation

    @staticmethod
    def morph_into(widget, target_geometry, duration=600):
        """Плавное преобразование в другую геометрию"""
        animation = QPropertyAnimation(widget, b"geometry")
        animation.setDuration(duration)
        animation.setStartValue(widget.geometry())
        animation.setEndValue(target_geometry)
        animation.setEasingCurve(QEasingCurve.Type.InOutQuart)
        return animation

    @staticmethod
    def staggered_children_animation(parent_widget, animation_type='fade_in', delay=100):
        """Анимация дочерних виджетов с задержкой (каскадный эффект)"""
        group = QSequentialAnimationGroup()
        
        for i, child in enumerate(parent_widget.findChildren(QWidget)):
            if animation_type == 'fade_in':
                anim = Animations.fade_in(child, 300)
            elif animation_type == 'slide_up':
                anim = Animations.slide_in_from_bottom(child, 400)
            elif animation_type == 'scale':
                anim = Animations.scale_up(child, 500)
            else:
                anim = Animations.fade_in(child, 300)
            
            group.addPause(delay * i)
            group.addAnimation(anim)
        
        return group

class NotificationManager:
    _instance = None
    _notifications = []
    _spacing = 10
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def add_notification(self, notification):
        self._notifications.append(notification)
        self._update_positions()
    
    def remove_notification(self, notification):
        if notification in self._notifications:
            self._notifications.remove(notification)
            self._update_positions()
    
    def _update_positions(self):
        y_pos = 40
        for notification in self._notifications:
            notification.target_y = y_pos
            notification._move_to_position()
            y_pos += notification.height() + self._spacing

class GnomeToast(QLabel):
    def __init__(self, message="", duration=3000, parent_widget=None):
        super().__init__()
        self.parent_widget = parent_widget
        self._setup_window()
        self._setup_style()
        self._setup_content(message)
        self._setup_animations(duration)
    
    def _setup_window(self):
        # Ключевые флаги для показа поверх всех окон
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.ToolTip
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    
    def _setup_style(self):
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                padding: 15px;
                border-radius: 8px;
                font-size: 14px;
            }
        """)
    
    def _setup_content(self, message):
        self.setText(message)
        self.adjustSize()
        self._calculate_position()
    
    def _calculate_position(self):
        if self.parent_widget:
            # Позиция относительно родительского виджета
            parent_global_pos = self.parent_widget.mapToGlobal(QPoint(0, 0))
            self.start_x = parent_global_pos.x() + self.parent_widget.width()
            self.target_x = parent_global_pos.x() + self.parent_widget.width() - self.width() - 10
            self.base_y = parent_global_pos.y()
        else:
            # Позиция на экране
            screen = QApplication.primaryScreen().availableGeometry()
            self.start_x = screen.width()
            self.target_x = screen.width() - self.width() - 20
            self.base_y = 40
        
        self.move(self.start_x, self.base_y)
        self.manager = NotificationManager()
    
    def _setup_animations(self, duration):
        self.slide_animation = QPropertyAnimation(self, b"pos")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(200)
        self.fade_animation.finished.connect(self.close)
        
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._hide_toast)
        
        self.duration = duration
    
    def show_toast(self):
        self.manager.add_notification(self)
        self.show()
        
        self.slide_animation.setStartValue(QPoint(self.start_x, self.target_y))
        self.slide_animation.setEndValue(QPoint(self.target_x, self.target_y))
        self.slide_animation.start()
        
        self.timer.start(self.duration)
    
    def _move_to_position(self):
        self.slide_animation.setStartValue(QPoint(self.target_x, self.y()))
        self.slide_animation.setEndValue(QPoint(self.target_x, self.target_y))
        self.slide_animation.start()
    
    @property
    def target_y(self):
        return self._target_y
    
    @target_y.setter
    def target_y(self, value):
        self._target_y = self.base_y + value
    
    def _hide_toast(self):
        self.fade_animation.setStartValue(1.0)
        self.fade_animation.setEndValue(0.0)
        self.fade_animation.start()
    
    def close(self):
        self.manager.remove_notification(self)
        super().close()
        self.deleteLater()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor(0, 0, 0, 180))  # Полупрозрачный черный
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 8, 8)
        super().paintEvent(event)

def show_gnome_notification(message, duration=3000, parent_widget=None):
    GnomeToast(message, duration, parent_widget).show_toast()


class BuyStarsFragment(QThread): 
    result = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, username: str, count_stars: str, token: str, deal_id: str, acc: Account):
        super().__init__()
        self.username = username
        self.count_stars = count_stars
        self.token = token
        self.deal_id = deal_id
        self.acc = acc
        self.mutex = QMutex()
        self.acc = None
        self._initialized = True

    def __del__(self):
        try:
            if hasattr(self, '_initialized') and self._initialized:
                if self.isRunning():
                    self.quit()
                    self.wait(1000)
        except (RuntimeError, AttributeError):
            pass

    def run(self):
        if not self.mutex.tryLock():
            return
        
        try:
            url = "https://api.fragment-api.com/v1/order/stars/"

            payload = {
                "username": self.username,
                "quantity": int(self.count_stars),
                "show_sender": False
            }
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"JWT {self.token}"
            }

            response = requests.post(url, json=payload, headers=headers)
            success = response.json().get("success")

            Account.update_deal(self.acc, deal_id=self.deal_id, new_status=ItemDealStatuses.SENT)

            self.result.emit([success, self.username])
            
        except Exception as e:
            error_msg = f"Внезапная ошибка: {str(e)}"
            self.error.emit(error_msg)
        finally:
            self.mutex.unlock()

class AuthFragment(QThread): 
    result = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, phone: str, mnemonics: str, apikey: str, version: str):
        super().__init__()
        self.mnemonics = mnemonics
        self.phone_number = phone
        self.apikey = apikey
        self.version = version
        self.mutex = QMutex()
        self.acc = None
        self._initialized = True

    def __del__(self):
        try:
            if hasattr(self, '_initialized') and self._initialized:
                if self.isRunning():
                    self.quit()
                    self.wait(1000)
        except (RuntimeError, AttributeError):
            pass

    def run(self):
        if not self.mutex.tryLock():
            return
        
        try:
            url = "https://api.fragment-api.com/v1/auth/authenticate/"

            payload = {
                "api_key": self.apikey,
                "phone_number": f"{self.phone_number.replace('+', '').strip()}",
                "version": self.version,
                "mnemonics": [mn.strip() for mn in self.mnemonics.split()]}
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers)
            token = response.json().get('token')

            self.result.emit([token, self.apikey, self.phone_number])
            
        except Exception as e:
            error_msg = f"Внезапная ошибка: {str(e)}"
            self.error.emit(error_msg)
        finally:
            self.mutex.unlock()

class SessionListener(QThread):
    new_msg = pyqtSignal(str)
    new_deal = pyqtSignal(list)
    item_paid = pyqtSignal(str)
    new_review = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, token, user_agent):
        super().__init__()
        self.token = token
        self.user_agent = user_agent
        self.mutex = QMutex()
        self.acc = None
        self.listener = None

    def run(self):
        try:
            self.acc = Account(self.token, self.user_agent, requests_timeout=5, request_max_retries=3)
            self.listener = EventListener(self.acc)
            
            for event in self.listener.listen(requests_delay=2):
                if not self.mutex.tryLock():
                    break
                try:
                    if event.type is EventTypes.NEW_MESSAGE:
                        if event.chat.id not in [self.acc.support_chat_id, self.acc.system_chat_id] and event.message.user.id != self.acc.id:
                            msg = f"[СООБЩЕНИЕ]{event.message.user.username}: {event.message.text}."
                            self.new_msg.emit(msg)
                    elif event.type is EventTypes.NEW_DEAL:
                        if event.deal.user.id == self.acc.id:
                            return
                        msg = f"{event.deal.user.username} начал сделку на {event.deal.item.price} рублей."
                        data = event.deal.obtaining_fields
                        count = self.acc.get_item(event.deal.item.id).attributes.get('amount')
                        username = str(getattr(*data, 'value')).replace('@', '').strip()
                        self.new_deal.emit([msg, username, count, event.deal.id, self.acc])
                    elif event.type is EventTypes.ITEM_PAID:
                        if event.deal.user.id == self.acc.id:
                            return
                        msg = f"{event.deal.user.username} оплатил [{event.deal.item.name}]"
                        self.item_paid.emit(msg)
                    elif event.type is EventTypes.NEW_REVIEW:
                        if event.deal.user.id == self.acc.id:
                            return
                        review = f"{'⭐' * event.deal.review.rating}{event.deal.review.creator.username}: {event.deal.review.text}"
                        self.new_review.emit(review)

                except Exception as e:
                    self.error.emit(f"Ошибка обработки события: {str(e)}")
                finally:
                    self.mutex.unlock()
                    
        except UnauthorizedError as e:
            error_msg = "Не удалось подключиться к аккаунту Playerok"
            self.error.emit(error_msg)
        except RequestError as e:
            error_msg = f"Возникла ошибка при отправке запроса: {str(e)}"
            self.error.emit(error_msg)
        except RequestFailedError as e:
            error_msg = "Код ответа не равен 200"
            self.error.emit(error_msg)
        except CloudflareDetectedException as e:
            error_msg = "Ошибка обнаружения Cloudflare защиты при отправке запроса"
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Внезапная ошибка: {str(e)}"
            self.error.emit(error_msg)

    def stop(self):
        self.mutex.lock()
        self.quit()
        self.wait(5000)
        self.mutex.unlock()


class ItemDelete(QThread): 
    result = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, token, user_agent, item):
        super().__init__()
        self.token = token
        self.user_agent = user_agent
        self.mutex = QMutex()
        self.item = item 
        self.acc = None
        self._initialized = True

    def __del__(self):
        try:
            if hasattr(self, '_initialized') and self._initialized:
                if self.isRunning():
                    self.quit()
                    self.wait(1000)
        except (RuntimeError, AttributeError):
            pass

    def run(self):
        if not self.mutex.tryLock():
            return
        
        try:
            self.acc = Account(
                token=self.token, 
                user_agent=self.user_agent, 
                requests_timeout=5, 
                request_max_retries=3
            )

            result_ = Account.remove_item(self.acc, self.item.id)

            self.result.emit([result_, self.item])
            
        except UnauthorizedError as e:
            error_msg = "Не удалось подключиться к аккаунту Playerok"
            self.error.emit(error_msg)
        except RequestError as e:
            error_msg = "Возникла ошибка при отправке запроса"
            self.error.emit(error_msg)
        except RequestFailedError as e:
            error_msg = "Код ответа не равен 200"
            self.error.emit(error_msg)
        except CloudflareDetectedException as e:
            error_msg = "Ошибка обнаружения Cloudflare защиты при отправке запроса"
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Внезапная ошибка: {str(e)}"
            self.error.emit(error_msg)
        finally:
            self.mutex.unlock()

class ItemsStatusUpdate(QThread):
    result = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, token, user_agent):
        super().__init__()
        self.token = token
        self.user_agent = user_agent
        self.mutex = QMutex()
        self.items = None
        self.acc = None
        self._initialized = True

    def __del__(self):
        try:
            if hasattr(self, '_initialized') and self._initialized:
                if self.isRunning():
                    self.quit()
                    self.wait(1000)
        except (RuntimeError, AttributeError):
            pass

    def run(self):
        if not self.mutex.tryLock():
            return
        
        try:
            self.acc = Account(
                token=self.token, 
                user_agent=self.user_agent, 
                requests_timeout=5, 
                request_max_retries=3
            )

            account_data = self.acc.get()
            user_profile = self.acc.get_user(id=account_data.id)
            items_data = user_profile.get_items()
            self.items = items_data.items

            if len(self.items)==0:
                text="Не найдено предметов"
                self.error.emit(text)
            else:
                self.result.emit(self.items)
            
        except UnauthorizedError as e:
            error_msg = "Не удалось подключиться к аккаунту Playerok"
            self.error.emit(error_msg)
        except RequestError as e:
            error_msg = "Возникла ошибка при отправке запроса"
            self.error.emit(error_msg)
        except RequestFailedError as e:
            error_msg = "Код ответа не равен 200"
            self.error.emit(error_msg)
        except CloudflareDetectedException as e:
            error_msg = "Ошибка обнаружения Cloudflare защиты при отправке запроса"
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Внезапная ошибка: {str(e)}"
            self.error.emit(error_msg)
        finally:
            self.mutex.unlock()

class ItemPublishAll(QThread):
    result = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, token, user_agent):
        super().__init__()
        self.token = token
        self.user_agent = user_agent
        self.mutex = QMutex()
        self.items = None
        self.acc = None
        self._initialized = True

    def __del__(self):
        try:
            if hasattr(self, '_initialized') and self._initialized:
                if self.isRunning():
                    self.quit()
                    self.wait(1000)
        except (RuntimeError, AttributeError):
            pass

    def run(self):
        if not self.mutex.tryLock():
            return
        
        try:
            self.acc = Account(
                token=self.token, 
                user_agent=self.user_agent, 
                requests_timeout=5, 
                request_max_retries=3
            )

            account_data = self.acc.get()
            user_profile = self.acc.get_user(id=account_data.id)
            items_data = user_profile.get_items()
            self.items = items_data.items

            if len(self.items)==0:
                text="Не найдено предметов"
                self.error.emit(text)
            else:
                items_ = []
                for item in self.items:
                    if item.status==ItemStatuses.DRAFT:
                        priorities = self.acc.get_item_priority_statuses(
                            item_id=item.id, 
                            item_price=item.price
                        )

                        priority = [priority for priority in priorities if priority.name == "Обычный"][0]
                        result_ = Account.publish_item(self.acc, item.id, priority_status_id=priority.id)
                        items_.append(result_)
                        self.msleep(100)
                if len(items_)==0:
                    text="Не найдено предметов в черновике"
                    self.error.emit(text)
                else:
                    self.result.emit(items_)
            
        except UnauthorizedError as e:
            error_msg = "Не удалось подключиться к аккаунту Playerok"
            self.error.emit(error_msg)
        except RequestError as e:
            error_msg = "Возникла ошибка при отправке запроса"
            self.error.emit(error_msg)
        except RequestFailedError as e:
            error_msg = "Код ответа не равен 200"
            self.error.emit(error_msg)
        except CloudflareDetectedException as e:
            error_msg = "Ошибка обнаружения Cloudflare защиты при отправке запроса"
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Внезапная ошибка: {str(e)}"
            self.error.emit(error_msg)
        finally:
            self.mutex.unlock()

class ItemPublish(QThread):
    result = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, token, user_agent, item):
        super().__init__()
        self.token = token
        self.user_agent = user_agent
        self.mutex = QMutex()
        self.item = item 
        self.acc = None
        self._initialized = True

    def __del__(self):
        try:
            if hasattr(self, '_initialized') and self._initialized:
                if self.isRunning():
                    self.quit()
                    self.wait(1000)
        except (RuntimeError, AttributeError):
            pass

    def run(self):
        if not self.mutex.tryLock():
            return
        
        try:
            self.acc = Account(
                token=self.token, 
                user_agent=self.user_agent, 
                requests_timeout=5, 
                request_max_retries=3
            )

            priorities = self.acc.get_item_priority_statuses(
                item_id=self.item.id, 
                item_price=self.item.price
            )
            priority = [priority for priority in priorities if priority.name == "Обычный"][0]
            result_ = Account.publish_item(self.acc, self.item.id, priority_status_id=priority.id)
            self.result.emit([result_, self.item])
            
        except UnauthorizedError as e:
            error_msg = "Не удалось подключиться к аккаунту Playerok"
            self.error.emit(error_msg)
        except RequestError as e:
            error_msg = "Возникла ошибка при отправке запроса"
            self.error.emit(error_msg)
        except RequestFailedError as e:
            error_msg = "Код ответа не равен 200"
            self.error.emit(error_msg)
        except CloudflareDetectedException as e:
            error_msg = "Ошибка обнаружения Cloudflare защиты при отправке запроса"
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Внезапная ошибка: {str(e)}"
            self.error.emit(error_msg)
        finally:
            self.mutex.unlock()

class ItemsLoadOnStart(QThread):
    result = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, token, user_agent):
        super().__init__()
        self.token = token
        self.user_agent = user_agent
        self.mutex = QMutex()
        self.items_load = None
        self.acc = None

    def __del__(self):
        self.wait()

    def run(self):
        if not self.mutex.tryLock():
            return
        try:
            self.acc = Account(token=self.token, user_agent=self.user_agent, requests_timeout=5, request_max_retries=3)
            account_data = self.acc.get()
            user_profile = self.acc.get_user(id=account_data.id)
            items_list = user_profile.get_items()
            self.result.emit(items_list.items)
        except UnauthorizedError as e:
            error_msg = "Не удалось подключиться к аккаунту Playerok"
            self.error.emit(error_msg)
        except RequestError as e:
            error_msg = "Возникла ошибка при отправке запроса"
            self.error.emit(error_msg)
        except RequestFailedError as e:
            error_msg = "Код ответа не равен 200"
            self.error.emit(error_msg)
        except CloudflareDetectedException as e:
            error_msg = "Ошибка обнаружения Cloudflare защиты при отправке запроса"
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Внезапная ошибка: {str(e)}"
            self.error.emit(error_msg)
        finally:
            self.mutex.unlock()

def Create_item(acc: Account, item_name: str, item_price: int, jpg: str, item_stars_count: str, 
                item_description: str = "Выдача осуществляется без захода на ваш аккаунт", 
                item_commentary: str = "Напишу вам в ТГ после оформления заказа"):
    try:
        game = acc.get_game(slug="telegram")
        

        stars_categories = [category for category in game.categories if category.name == "Звезды"]
        if not stars_categories:
            raise ValueError("Категория 'Звезды' не найдена в игре Telegram")
        game_category = acc.get_game_category(stars_categories[0].id)
        

        obtaining_type_list = acc.get_game_category_obtaining_types(game_category.id)
        username_obtaining_types = [obtaining_type for obtaining_type in obtaining_type_list.obtaining_types if obtaining_type.name == "По @username"]
        if not username_obtaining_types:
            raise "Тип получения 'По @username' не найден"
        gift_obtaining_type = username_obtaining_types[0]
        

        data_field_list = acc.get_game_category_data_fields(game_category.id, gift_obtaining_type.id)
        commentary_fields = [data_field for data_field in data_field_list.data_fields if data_field.label == "Комментарий"]
        if not commentary_fields:
            raise "Поле 'Комментарий' не найдено"
        commentary_data_field = commentary_fields[0]
        commentary_data_field.value = item_commentary


        selected_option_data = [gift_type for gift_type in game_category.options if gift_type.label == item_stars_count][0]
        selected_option_data.label = item_stars_count
        

        if not os.path.exists(jpg):
            raise f"Файл {jpg} не найден"
        
        banner_attachment = jpg


        item = acc.create_item(
            game_category_id=game_category.id,
            obtaining_type_id=gift_obtaining_type.id,
            name=item_name,
            price=item_price,
            description=item_description,
            data_fields=[commentary_data_field],  
            options=[selected_option_data],
            attachments=[banner_attachment]
        )

    except Exception as e:
        raise f"Не получилось создать предмет: {e}"
            
    return item



class ItemCreator(QThread):
    result = pyqtSignal(Item)
    error = pyqtSignal(str)
    process = pyqtSignal(str)

    def __init__(self, item_data, token, user_agent):
        super().__init__()
        self.token = token
        self.user_agent = user_agent
        self.item_data = item_data
        self.mutex = QMutex()
        self.item_creator = None
        self.acc = None

    def __del__(self):
        self.wait()

    def run(self):
        if not self.mutex.tryLock():
            self.process.emit("Уже выполняется создание предмета")
            return
        try:
            self.acc = Account(token=self.token, user_agent=self.user_agent, requests_timeout=5, request_max_retries=3)
            self.item_creator = Create_item(self.acc, **self.item_data)
            self.result.emit(self.item_creator)
        except UnauthorizedError as e:
            error_msg = "Не удалось подключиться к аккаунту Playerok"
            self.error.emit(error_msg)
        except RequestError as e:
            error_msg = "Возникла ошибка при отправке запроса"
            self.error.emit(error_msg)
        except RequestFailedError as e:
            error_msg = "Код ответа не равен 200"
            self.error.emit(error_msg)
        except CloudflareDetectedException as e:
            error_msg = "Ошибка обнаружения Cloudflare защиты при отправке запроса"
            self.error.emit(error_msg)
        except Exception as e:
            error_msg = f"Внезапная ошибка: {str(e)}"
            self.error.emit(error_msg)
        finally:
            self.mutex.unlock()



class UserProfile():
    def __init__(self, parent_, name_, dict_, tabs):
        self.name_ = name_
        self.profileMain = QWidget(parent=parent_)
        self.profileMain.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.profileMain.setObjectName(name_)
        self.profileMain.setFixedSize(QSize(920, 500))
        self.profileMain.setStyleSheet(f"QWidget#{name_}{{ border: 2px solid #e0e0e0; border-radius: 6px; }}")
        
        # Основной вертикальный layout
        self.mainLayout = QVBoxLayout(self.profileMain)
        self.mainLayout.setContentsMargins(15, 15, 15, 15)
        self.mainLayout.setSpacing(15)
        
        self._createHeaderSection()
        self._createTokenSection()
        self._createUserAgentSection()
        
        # Горизонтальный layout для нижней части (настройки + сессия)
        self.bottomLayout = QHBoxLayout()
        self.bottomLayout.setSpacing(20)
        
        self._createSettingsSection()
        self._createSessionSection()
        
        self.mainLayout.addLayout(self.bottomLayout)
        self.mainLayout.addStretch(1)
        
        # Связываем кнопку выхода
        self.exitButton.clicked.connect(lambda: self.exitOnClick(name_, dict_, tabs))
        
        # Скрываем другие окна и показываем текущее
        for wind in dict_.keys():
            self.profileMain.parent().findChild(QWidget, wind).hide()
        self.profileMain.show()

        for btn in self.profileMain.findChildren(QPushButton):
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def itemsLoad(self, items):
        count = 0

        for item in items:
            try:
                itemWidget = CustomWidgetItem(item=item)
                self.itemsArr.addItem(itemWidget)
                self.itemsArr.setItemWidget(itemWidget, itemWidget.widget)
                show_gnome_notification(f"Загружен предмет {item.name}")
                count = count + 1
            except Exception as e:
                show_gnome_notification(f"Ошибка при загрузке предмета: {e}")
        
        show_gnome_notification(f"Загружено {count} предметов")

    def itemsError(self, error):
        show_gnome_notification(f"Ошибка при загрузке предметов: {error}")
        print(f"Ошибка при загрузке предметов: {error}")

    def _createHeaderSection(self):
        """Создание заголовка и кнопок управления"""
        headerLayout = QHBoxLayout()
        headerLayout.setSpacing(0)
        
        # Заголовок профиля
        nameMainFont = QFont("Arial")
        nameMainFont.setBold(True)
        
        self.nameMain = QLabel(text=self.profileMain.objectName())
        self.nameMain.setFixedHeight(30)
        self.nameMain.setFont(nameMainFont)
        self.nameMain.setStyleSheet("font-size: 25px;")
        self.nameMain.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        
        # Растягивающееся пространство между заголовком и кнопками
        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        
        # Кнопки управления (свернуть и выход)
        self.minimizeButton = QPushButton()
        self.minimizeButton.setFixedSize(QSize(35, 35))
        self.minimizeButton.setIcon(svgToIcon("minimize.svg", size=QSize(35, 35)))
        self.minimizeButton.clicked.connect(self.minimizeOnClick)
        
        self.exitButton = QPushButton()
        self.exitButton.setFixedSize(QSize(35, 35))
        self.exitButton.setIcon(svgToIcon("exit.svg", size=QSize(35, 35)))
        self.exitButton.setProperty("class", "danger")
        
        headerLayout.addWidget(self.nameMain)
        headerLayout.addItem(spacer)
        headerLayout.addWidget(self.minimizeButton)
        headerLayout.addWidget(self.exitButton)
        
        self.mainLayout.addLayout(headerLayout)

    def _createTokenSection(self):
        """Создание секции для токена"""
        tokenLayout = QHBoxLayout()
        tokenLayout.setSpacing(10)
        
        # Метка токена
        tokenLabelFont = QFont("Arial")
        tokenLabelFont.setBold(True)
        
        self.tokenLabel = QLabel("Токен")
        self.tokenLabel.setFixedSize(QSize(60, 35))
        self.tokenLabel.setFont(tokenLabelFont)
        self.tokenLabel.setStyleSheet("font-size: 15px;")
        tokenLayout.addWidget(self.tokenLabel)
        
        # Поле ввода токена
        self.tokenString = QLineEdit()
        self.tokenString.setFixedHeight(35)
        self.tokenString.setObjectName("token")
        self.tokenString.textEdited.connect(self.tokenStringPressed)
        tokenLayout.addWidget(self.tokenString, 1)
        
        # Кнопка блокировки токена
        self.tokenStringLock = QPushButton()
        self.tokenStringLock.setFixedSize(QSize(35, 35))
        self.tokenStringLock.setIcon(svgToIcon("lock.svg", size=QSize(35, 35)))
        self.tokenStringLock.setCheckable(True)
        self.tokenStringLock.setObjectName("tokenLock")
        self.tokenStringLock.toggled.connect(self.tokenStringLocked)
        tokenLayout.addWidget(self.tokenStringLock)
        
        self.mainLayout.addLayout(tokenLayout)

    def _createUserAgentSection(self):
        """Создание секции для User Agent"""
        userAgentLayout = QHBoxLayout()
        userAgentLayout.setSpacing(10)
        
        # Метка User Agent
        userAgentLabelFont = QFont("Arial")
        userAgentLabelFont.setBold(True)
        
        self.userAgentLabel = QLabel("Юзер Агент")
        self.userAgentLabel.setFixedSize(QSize(100, 35))
        self.userAgentLabel.setFont(userAgentLabelFont)
        self.userAgentLabel.setStyleSheet("font-size: 15px;")
        userAgentLayout.addWidget(self.userAgentLabel)
        
        # Поле ввода User Agent
        self.userAgentString = QLineEdit()
        self.userAgentString.setFixedHeight(35)
        self.userAgentString.setObjectName("useragent")
        self.userAgentString.setText(UserAgent(os="Windows").random)
        self.userAgentString.textEdited.connect(self.userAgentStringPressed)
        self.userAgentString.setObjectName("useragent")
        self.userAgentString.textEdited.connect(self.userAgentStringPressed)
        userAgentLayout.addWidget(self.userAgentString, 1)
        
        # Кнопка блокировки User Agent
        self.userAgentStringLock = QPushButton()
        self.userAgentStringLock.setFixedSize(QSize(35, 35))
        self.userAgentStringLock.setIcon(svgToIcon("lock.svg", size=QSize(35, 35)))
        self.userAgentStringLock.setCheckable(True)
        self.userAgentStringLock.setObjectName("userAgentLock")
        self.userAgentStringLock.toggled.connect(self.userAgentStringLocked)
        userAgentLayout.addWidget(self.userAgentStringLock)
        
        # Кнопка случайного User Agent
        self.userAgentStringRandom = QPushButton()
        self.userAgentStringRandom.setFixedSize(QSize(35, 35))
        self.userAgentStringRandom.setIcon(svgToIcon("load.svg", size=QSize(35, 35)))
        self.userAgentStringRandom.setObjectName("userAgentRandom")
        self.userAgentStringRandom.pressed.connect(self.userAgentStringRandomed)
        userAgentLayout.addWidget(self.userAgentStringRandom)
        
        self.mainLayout.addLayout(userAgentLayout)

    def _createSettingsSection(self):
        settingsContainer = QWidget()
        settingsLayout = QVBoxLayout(settingsContainer)
        settingsLayout.setSpacing(10)
        

        settingsFont = QFont("Arial")
        settingsFont.setBold(True)
        
        settingsLabel = QLabel("Настройки")
        settingsLabel.setFont(settingsFont)
        settingsLabel.setStyleSheet("font-size: 16px; margin-bottom: 10px;")
        settingsLayout.addWidget(settingsLabel)
        
        # Кнопка сообщений
        self.setts_layout = QHBoxLayout()
        settingsLayout.addLayout(self.setts_layout)

        self.textToSay = QPushButton("Предмет")
        self.textToSay.setFixedSize(QSize(120, 35))
        self.textToSay.setFont(settingsFont)
        self.textToSay.setStyleSheet("font-size: 14px;")
        self.setts_layout.addWidget(self.textToSay)

        # Виджет для сообщений
        self.textToSayWidget = QWidget()
        self.textToSayWidget.setObjectName("textToSayWidget")
        self.textToSayWidget.setWindowTitle("Настройка")
        self.textToSayWidget.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.SplashScreen)
        self.textToSayWidget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.textToSayWidget.setFixedSize(QSize(400, 600))

        self.mainContainer = QWidget(self.textToSayWidget)
        self.mainContainer.setFixedSize(QSize(400, 600))
        self.mainContainer.setObjectName(f"conrainer{self.name_}")

        with open(r"style.qss", "r", encoding='utf-8') as f:
            self.mainContainer.setStyleSheet(f.read())
        self.mainContainer.setStyleSheet(f"QWidget#conrainer{self.name_}{{ border: 2px solid #e0e0e0; border-radius: 6px; }}")
        
        widgetLayout = QVBoxLayout(self.textToSayWidget)
        widgetLayout.setContentsMargins(0, 0, 0, 0)
        widgetLayout.addWidget(self.mainContainer)
        
        # Внутренний layout для содержимого

        contentLayout = QVBoxLayout(self.mainContainer)
        
        onTopLayout = QHBoxLayout()
        contentLayout.addLayout(onTopLayout)

        self.widgetName = QLabel("Настройка предмета")
        self.widgetName.setProperty("class", "title")
        self.widgetName.setStyleSheet("border: 0px")
        onTopLayout.addWidget(self.widgetName, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        
        self.minimizeButtonWidget = QPushButton()
        self.minimizeButtonWidget.setIcon(svgToIcon("minimize.svg", size=QSize(35, 35)))
        self.minimizeButtonWidget.setFixedSize(QSize(35,35))
        self.minimizeButtonWidget.clicked.connect(lambda: self.textToSayWidget.hide())
        onTopLayout.addWidget(self.minimizeButtonWidget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        self.itemNameLine = QLineEdit()
        self.itemNameLine.setFixedSize(QSize(300,35))
        self.itemNameLine.setPlaceholderText("Название предмета (от 10 символов)")
        contentLayout.addWidget(self.itemNameLine, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.itemPriceLine = QLineEdit()
        self.itemPriceLine.setFixedSize(QSize(300,35))
        self.itemPriceLine.setPlaceholderText("Цена (от 90 до 100000)")
        contentLayout.addWidget(self.itemPriceLine, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.validatorTextPrice = QRegularExpression(r"[0-9]*")
        self.itemPriceLineValidator = QRegularExpressionValidator(self.validatorTextPrice)
        self.itemPriceLine.setValidator(self.itemPriceLineValidator)
        self.itemPriceLine.setValidator(QIntValidator(90, 100000))

        self.itemStarsCountLine = QComboBox()
        self.itemStarsCountLine.setFixedSize(QSize(300,35))
        self.itemStarsCountLine.addItems(['50 звёзд', '75 звёзд', '85 звёзд', '100 звёзд', '150 звёзд', '200 звёзд', '250 звёзд', '300 звёзд', '350 звёзд', '400 звёзд', '500 звёзд', '600 звёзд', '700 звёзд', '800 звёзд', '900 звёзд', '1000 звёзд', '1500 звёзд', '2500 звёзд', '5000 звёзд', '10000 звёзд', '25000 звёзд', '35000 звёзд', '50000 звёзд'])
        contentLayout.addWidget(self.itemStarsCountLine, 3, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.itemStarsCountLine.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        itemIconLayout = QHBoxLayout()
        contentLayout.addLayout(itemIconLayout)

        self.itemIconPathLine = QLineEdit()
        self.itemIconPathLine.setFixedSize(QSize(200,35))
        self.itemIconPathLine.setPlaceholderText("Картинка для предмета")
        itemIconLayout.addWidget(self.itemIconPathLine, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.itemIconPath = QPushButton("Файл")
        self.itemIconPath.setFixedSize(QSize(70,35))
        itemIconLayout.addWidget(self.itemIconPath, 0, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.itemIconPath.clicked.connect(lambda: self.itemGetIconPath())

        self.itemDescriptionLine = QPlainTextEdit()
        self.itemDescriptionLine.setFixedSize(QSize(350,150))
        self.itemDescriptionLine.setPlaceholderText("Описание предмета (от 10 символов)")
        contentLayout.addWidget(self.itemDescriptionLine, 4, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.itemCommentaryLine = QPlainTextEdit()
        self.itemCommentaryLine.setFixedSize(QSize(350,150))
        self.itemCommentaryLine.setPlaceholderText("Комментарий к предмету (от 2 символов)")
        contentLayout.addWidget(self.itemCommentaryLine, 5, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.createItem = QPushButton("Создать предмет")
        self.createItem.adjustSize()
        self.createItem.clicked.connect(lambda: self.createItemClicked())
        contentLayout.addWidget(self.createItem, 6, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        for btn in self.textToSayWidget.findChildren(QPushButton):
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        

        contentLayout.addStretch(1)
        
        self.textToSayWidget.hide()


        # Кнопка настроек

        self.itemsSetts = QPushButton("Взаимодействия")
        self.itemsSetts.adjustSize()
        self.itemsSetts.setFont(settingsFont)
        self.itemsSetts.setStyleSheet("font-size: 14px;")
        self.setts_layout.addWidget(self.itemsSetts)

        # Виджет для сообщений
    
        self.itemsSettsWidget = QWidget()
        self.itemsSettsWidget.setObjectName("itemsSettsWidget")
        self.itemsSettsWidget.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.SplashScreen)
        self.itemsSettsWidget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.itemsSettsWidget.adjustSize()

        self.mainContainerItems = QWidget(self.itemsSettsWidget)
        self.mainContainerItems.setFixedSize(QSize(400, 600))
        self.mainContainerItems.setObjectName(f"conrainerItems{self.name_}")

        with open(r"style.qss", "r", encoding='utf-8') as f:
            self.mainContainerItems.setStyleSheet(f.read())
        self.mainContainerItems.setStyleSheet(f"QWidget#conrainerItems{self.name_}{{ border: 2px solid #e0e0e0; border-radius: 6px; }}")
        
        widgetLayoutItems = QVBoxLayout(self.itemsSettsWidget)
        widgetLayoutItems.setContentsMargins(0, 0, 0, 0)
        widgetLayoutItems.addWidget(self.mainContainerItems)

        contentLayoutItems = QVBoxLayout(self.mainContainerItems)

        self.minimizeButtonWidgetItems = QPushButton()
        self.minimizeButtonWidgetItems.setIcon(svgToIcon("minimize.svg", size=QSize(35, 35)))
        self.minimizeButtonWidgetItems.setFixedSize(QSize(35,35))
        self.minimizeButtonWidgetItems.clicked.connect(lambda: self.itemsSettsWidget.hide())
        contentLayoutItems.addWidget(self.minimizeButtonWidgetItems, alignment=Qt.AlignmentFlag.AlignRight)

        self.itemsPublishing = QPushButton("Выставить предметы")
        self.itemsPublishing.adjustSize()
        self.itemsPublishing.clicked.connect(lambda: self.itemsPublishingConnect())
        contentLayoutItems.addWidget(self.itemsPublishing)

        self.itemsStatusUpdate = QPushButton("Обновить состояние предметов")
        self.itemsStatusUpdate.adjustSize()
        self.itemsStatusUpdate.clicked.connect(lambda: self.itemsStatusUpdateConnect())
        contentLayoutItems.addWidget(self.itemsStatusUpdate)

        for btn in self.itemsSettsWidget.findChildren(QPushButton):
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        contentLayoutItems.addStretch(1)
        
        self.itemsSettsWidget.hide()

        self.textToSay.clicked.connect(lambda: self.openTextWidget(self.textToSayWidget))
        self.itemsSetts.clicked.connect(lambda: self.openItemsSetts(self.itemsSettsWidget))
        
        settingsLayout.addStretch(1)

        self.itemArrLabel = QLabel("Список предметов")
        settingsLayout.addWidget(self.itemArrLabel)

        self.itemsArr = QListWidget()
        self.itemsArr.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.itemsArr.customContextMenuRequested.connect(lambda pos: self.show_context_menu_arr(pos))
        self.itemsArr.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        settingsLayout.addWidget(self.itemsArr)
        
        self.bottomLayout.addWidget(settingsContainer, 1)


        self.textToSayWidget.dragging = False
        self.textToSayWidget.drag_position = QPoint()

        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.textToSayWidget.dragging = True
                self.textToSayWidget.drag_position = event.globalPosition().toPoint() - self.textToSayWidget.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(event):
            if self.textToSayWidget.dragging and event.buttons() & Qt.MouseButton.LeftButton:
                self.textToSayWidget.move(event.globalPosition().toPoint() - self.textToSayWidget.drag_position)
                event.accept()
        
        def mouseReleaseEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.textToSayWidget.dragging = False
                event.accept()


        self.textToSayWidget.mousePressEvent = mousePressEvent
        self.textToSayWidget.mouseMoveEvent = mouseMoveEvent
        self.textToSayWidget.mouseReleaseEvent = mouseReleaseEvent


        self.itemsSettsWidget.dragging = False
        self.itemsSettsWidget.drag_position = QPoint()

        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.itemsSettsWidget.dragging = True
                self.itemsSettsWidget.drag_position = event.globalPosition().toPoint() - self.itemsSettsWidget.frameGeometry().topLeft()
                event.accept()

        def mouseMoveEvent(event):
            if self.itemsSettsWidget.dragging and event.buttons() & Qt.MouseButton.LeftButton:
                self.itemsSettsWidget.move(event.globalPosition().toPoint() - self.itemsSettsWidget.drag_position)
                event.accept()
        
        def mouseReleaseEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.itemsSettsWidget.dragging = False
                event.accept()


        self.itemsSettsWidget.mousePressEvent = mousePressEvent
        self.itemsSettsWidget.mouseMoveEvent = mouseMoveEvent
        self.itemsSettsWidget.mouseReleaseEvent = mouseReleaseEvent

    def _createSessionSection(self):
        """Создание секции сессии"""
        sessionContainer = QWidget()
        sessionLayout = QVBoxLayout(sessionContainer)
        sessionLayout.setSpacing(10)
        
        # Заголовок секции сессии
        sessionFont = QFont("Arial")
        sessionFont.setBold(True)
        
        sessionLabel = QLabel("Управление сессией")
        sessionLabel.setFont(sessionFont)
        sessionLabel.setStyleSheet("font-size: 16px; margin-bottom: 10px;")
        sessionLayout.addWidget(sessionLabel)
        
        # Кнопка начала сессии
        self.startSessionButton = QPushButton("Старт")
        self.startSessionButton.setFixedSize(QSize(140, 35))
        self.startSessionButton.setFont(sessionFont)
        self.startSessionButton.setStyleSheet("font-size: 14px;")
        self.startSessionButton.clicked.connect(lambda: self.startSessionFunc())
        sessionLayout.addWidget(self.startSessionButton)
        
        # Экран сессии
        self.sessionScreen = QPlainTextEdit()
        self.sessionScreen.setObjectName("sessionscreen")
        self.sessionScreen.setReadOnly(True)
        self.sessionScreen.setFixedSize(QSize(500, 200))
        self.sessionScreen.setPlaceholderText("Здесь будет отображаться ход сессии...")
        sessionLayout.addWidget(self.sessionScreen)
    
        
        # растягивающееся пространство
        sessionLayout.addStretch(1)
        
        self.bottomLayout.addWidget(sessionContainer, 2)

    def exitOnClick(self, profileName, dict_, tabs):
        
        self.warn = QMessageBox()
        self.warn.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.warn.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        centralWidget = QGraphicsView(self.warn)
        centralWidget.setStyleSheet("border-radius: 6px; border-color: lightgray; border-style: solid; border-width: 2px;")
        centralWidget.lower()
        centralWidget.resize(QSize(195, 100))
        self.warn.resize(QSize(500, 100))
        self.warn.setWindowTitle(" ")
        self.warn.setText("Удалить профиль???")
        self.warn.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        self.warn.setDefaultButton(QMessageBox.StandardButton.No)

        for btn in self.warn.findChildren(QPushButton):
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.warn.dragging = False
        self.warn.drag_position = QPoint()

        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.warn.dragging = True
                self.warn.drag_position = event.globalPosition().toPoint() - self.warn.frameGeometry().topLeft()
                event.accept()
    
        def mouseMoveEvent(event):
            if self.warn.dragging and event.buttons() & Qt.MouseButton.LeftButton:
                self.warn.move(event.globalPosition().toPoint() - self.warn.drag_position)
                event.accept()
        
        def mouseReleaseEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.warn.dragging = False
                event.accept()

        self.warn.mousePressEvent = mousePressEvent
        self.warn.mouseMoveEvent = mouseMoveEvent
        self.warn.mouseReleaseEvent = mouseReleaseEvent
        
        answer = self.warn.exec()
        if answer == QMessageBox.StandardButton.Yes:
            self.profileMain.deleteLater()
            del dict_[profileName]
            item = tabs.findItems(profileName, Qt.MatchFlag.MatchExactly)
            tabs.takeItem(tabs.row(item[0]))
            configProfiler = configparser.ConfigParser()
            configProfiler.read("profiles.ini")
            configProfiler.remove_section(profileName)
            with open("profiles.ini", "w") as configFile:
                configProfiler.write(configFile)

    def openItemsSetts(self, widget):
        if widget.isHidden():
            widget.show()
            widget.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        else:
            widget.hide()

    # СЕССИЯ ##############################################################################################################################################
    def startSessionFunc(self):
        if self.startSessionButton.text() == "Старт":
            try:
                self.sessionFunc = SessionListener(token=self.tokenString.text(), user_agent=self.userAgentString.text())
                self.sessionFunc.new_msg.connect(self.newMsg)
                self.sessionFunc.new_deal.connect(self.newDeal)
                self.sessionFunc.item_paid.connect(self.itemPaid)
                self.sessionFunc.new_review.connect(self.newReview)
                self.sessionFunc.error.connect(self.itemError)
                self.sessionFunc.start()
                show_gnome_notification("Запуск сессии...")
                self.startSessionButton.setText("Стоп")
                self.startSessionButton.setDisabled(True)
                QTimer.singleShot(5000, self.startButtonHide)
            except Exception as e:
                show_gnome_notification(f"Внезапная ошибка: {e}")
                print(f"Внезапная ошибка: {e}")
        else:
            try:
                self.sessionFunc.stop()
                show_gnome_notification("Остановка сессии...")
                self.startSessionButton.setText("Старт")
                self.startSessionButton.setDisabled(True)
                QTimer.singleShot(5000, self.startButtonHide)
            except Exception as e:
                show_gnome_notification(f"Внезапная ошибка: {e}")
                print(f"Внезапная ошибка: {e}")

    def startButtonHide(self):
        self.startSessionButton.setEnabled(True)
    
    def newMsg(self, msg):
        self.sessionScreen.appendPlainText(msg)

    def newDeal(self, data):
        msg, username_, count_, deal_id = data
        self.sessionScreen.appendPlainText(msg)
        try:
            configProfiler = configparser.ConfigParser()
            configProfiler.read("fragmentapi.ini")
            token_ = configProfiler.get("SETTINGS", 'token')
            self.buy = BuyStarsFragment(username=username_, count_stars=count_, token=token_, deal_id=deal_id, acc=self.acc)
            self.buy.result.connect(self.BuyStarsSignal)
            self.buy.error.connect(self.itemError)
            self.buy.start()
        except Exception as e:
                show_gnome_notification(f"Внезапная ошибка: {e}")
                print(f"Внезапная ошибка: {e}")

    def itemPaid(self, msg):
        self.sessionScreen.appendPlainText(msg)

    def newReview(self, msg):
        self.sessionScreen.appendPlainText(msg)

    def BuyStarsSignal(self, result):
        result_bool, username_ = result
        if result_bool:
            show_gnome_notification(f"Успешно прошла оплата для {username_}")
            self.sessionScreen.appendPlainText(f"Успешно прошла оплата для {username_}")

    def itemsPublishingConnect(self):
        try:
            self.itemsPublishAll=ItemPublishAll(token=self.tokenString.text(), user_agent=self.userAgentString.text())
            self.itemsPublishAll.result.connect(self.itemPublishingAll)
            self.itemsPublishAll.error.connect(self.itemError)
            self.itemsPublishAll.start()
            show_gnome_notification(f"Пробуем выставить предметы...")
                        
        except Exception as e:
            show_gnome_notification(f"Внезапная ошибка: {e}")
            print(f"Внезапная ошибка: {e}")

    def itemPublishingAll(self, items):
        for item in items:
            try:
                found_items = self.itemsArr.findItems(item.name, Qt.MatchFlag.MatchExactly)
                if not found_items:
                    return
                    
                list_item = found_items[0]
            
                if hasattr(list_item, 'update_color'):
                    list_item.update_color(custom_color=QColor(255, 215, 0))
                    show_gnome_notification(f"Предмет {item.name} выставлен на проверку модерации!")
                else:
                    print("Элемент не поддерживает изменение цвета")
                    
            except Exception as e:
                print(f"Ошибка при обновлении цвета: {e}")
    
    def itemsStatusUpdateConnect(self):
        try:
            self.itemsStatuses=ItemsStatusUpdate(token=self.tokenString.text(), user_agent=self.userAgentString.text())
            self.itemsStatuses.result.connect(self.itemStatusesUpdate)
            self.itemsStatuses.error.connect(self.itemError)
            self.itemsStatuses.start()
            show_gnome_notification(f"Пробуем обновить предметы...")
                        
        except Exception as e:
            show_gnome_notification(f"Внезапная ошибка: {e}")
            print(f"Внезапная ошибка: {e}")

    def itemStatusesUpdate(self, items):
        for item in items:
            try:
                found_items = self.itemsArr.findItems(item.name, Qt.MatchFlag.MatchExactly)
                if not found_items:
                    return
                    
                list_item = found_items[0]
            
                if hasattr(list_item, 'update_color'):
                    list_item.update_color(custom_color=QColor(255, 215, 0))

                    if item.status == ItemStatuses.APPROVED:
                        list_item.update_color(custom_color=QColor(0, 128, 0))
                    elif item.status == ItemStatuses.BLOCKED:
                        list_item.update_color(custom_color=QColor(128, 0, 0))
                    elif item.status in [ItemStatuses.DECLINED, ItemStatuses.DRAFT, ItemStatuses.EXPIRED]:
                        list_item.update_color(custom_color=QColor(128, 128, 128))
                    elif item.status in [ItemStatuses.PENDING_APPROVAL, ItemStatuses.PENDING_MODERATION]:
                        list_item.update_color(custom_color=QColor(255, 215, 0))
                    elif item.status == ItemStatuses.SOLD:
                        list_item.update_color(custom_color=QColor(70, 130, 180))
                    show_gnome_notification(f"Обновлен предмет {item.name}")
                    
            except Exception as e:
                print(f"Ошибка при обновлении цвета: {e}")

    def createItemClicked(self): 

        item_data = {
            'item_name': self.itemNameLine.text(),
            'item_price': self.itemPriceLine.text(),
            'item_stars_count': self.itemStarsCountLine.currentText(),
            'item_commentary': self.itemCommentaryLine.toPlainText(),
            'item_description': self.itemDescriptionLine.toPlainText(),
            'jpg': Path(self.itemIconPathLine.text()),
        }
        
        self.itemCreator = ItemCreator(item_data=item_data, user_agent=self.userAgentString.text(), token=self.tokenString.text())
        self.itemCreator.result.connect(self.itemResult)
        self.itemCreator.error.connect(self.itemError)
        self.itemCreator.process.connect(self.threadProcess)
        self.itemCreator.start()

    def itemResult(self, item):
        show_gnome_notification(f"Предмет создан: {item.name}")
        itemWidget = CustomWidgetItem(item=item)
        self.itemsArr.addItem(itemWidget)
        self.itemsArr.setItemWidget(itemWidget, itemWidget.widget)
        print(item)

    def itemError(self, error):
        show_gnome_notification(error)
        print(error)

    def threadProcess(self, text):
        show_gnome_notification(text)
        print(text)

    def show_context_menu_arr(self, position):
        item = self.itemsArr.itemAt(position)
        row = self.itemsArr.row(item)
        if item:
            item_data = item.data(Qt.ItemDataRole.UserRole)
            self.menu = QMenu(self.itemsArr)
            self.menu.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            self.menu.setStyleSheet("""
                QMenu {
                    background-color: white;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    padding: 5px;
                }
                QMenu::item {
                    padding: 5px 15px;
                    border-radius: 4px;
                }
                QMenu::item:selected {
                    background-color: #f8f9fa;
                    color: white;
                }
            """)
            action_delete = self.menu.addAction("Удалить предмет")
            action_publish = self.menu.addAction("Опубликовать предмет(модерация)")
            self.menu.addSeparator()
            action = self.menu.exec(self.itemsArr.viewport().mapToGlobal(position))

            if action == action_delete:
                try:
                    self.resultDel=ItemDelete(token=self.tokenString.text(), user_agent=self.userAgentString.text(), item=item_data)
                    self.resultDel.result.connect(self.itemDeleteResult)
                    self.resultDel.error.connect(self.itemError)
                    self.resultDel.start()
                    self.itemsArr.takeItem(row)
                except Exception as e:
                    show_gnome_notification(f"Ошибка при удалении предмета: {e}")
                    print(f"Ошибка при удалении предмета: {e}")

            elif action == action_publish:
                try:
                    self.itemPublish=ItemPublish(token=self.tokenString.text(), user_agent=self.userAgentString.text(), item=item_data)
                    self.itemPublish.result.connect(self.itemPublishing)
                    self.itemPublish.error.connect(self.itemError)
                    self.itemPublish.start()
                    show_gnome_notification(f"Пробуем выставить предмет({item_data.name})...")
                        
                except Exception as e:
                    show_gnome_notification(f"Внезапная ошибка: {e}")
                    print(f"Внезапная ошибка: {e}")

    def itemDeleteResult(self, result):
        if result[0]==True:
            show_gnome_notification(f"Предмет {result[1].name} удален")
        else:
            show_gnome_notification(f"Ошибка при удалении предмета {result[1].name}")

    def itemPublishing(self, item):
        """Обработка успешной публикации предмета"""
        try:
            found_items = self.itemsArr.findItems(item[1].name, Qt.MatchFlag.MatchExactly)
            if not found_items:
                return
                
            list_item = found_items[0]
        
            if hasattr(list_item, 'update_color'):
                list_item.update_color(custom_color=QColor(255, 215, 0))
                show_gnome_notification(f"Предмет {item[1].name} выставлен на проверку модерации!")
            else:
                print("Элемент не поддерживает изменение цвета")
                
        except Exception as e:
            print(f"Ошибка при обновлении цвета: {e}")


    def itemGetIconPath(self):
        filePath, _ = QFileDialog.getOpenFileName(self.itemIconPath, "Открыть файл", "", "JPG File (*.jpg);; PNG File(*.png)")
        self.itemIconPathLine.setText(filePath)

    def minimizeOnClick(self):
        self.profileMain.hide()

    def QWidgetForTab(self):
        return self.profileMain
    
    def tokenStringPressed(self):
        configProfiler = configparser.ConfigParser()
        configProfiler.read("profiles.ini")
        configProfiler.set(self.profileMain.objectName(), 'token', self.tokenString.text())
        with open('profiles.ini', 'w') as configFile:
            configProfiler.write(configFile)

    def tokenStringLocked(self, checked):
        configProfiler = configparser.ConfigParser()
        configProfiler.read("profiles.ini")
        if checked:
            self.tokenString.setDisabled(True)
            configProfiler.set(self.profileMain.objectName(), 'tokenlock', "False")
        else:
            self.tokenString.setEnabled(True)
            configProfiler.set(self.profileMain.objectName(), 'tokenlock', "True")
        with open('profiles.ini', 'w') as configFile:
            configProfiler.write(configFile)

    def userAgentStringPressed(self):
        configProfiler = configparser.ConfigParser()
        configProfiler.read("profiles.ini")
        configProfiler.set(self.profileMain.objectName(), 'userAgent', self.userAgentString.text())
        with open('profiles.ini', 'w') as configFile:
            configProfiler.write(configFile)

    def userAgentStringLocked(self, checked):
        configProfiler = configparser.ConfigParser()
        configProfiler.read("profiles.ini")
        if checked:
            self.userAgentString.setDisabled(True)
            configProfiler.set(self.profileMain.objectName(), 'userAgentlock', "False")
        else:
            self.userAgentString.setEnabled(True)
            configProfiler.set(self.profileMain.objectName(), 'userAgentlock', "True")
        with open('profiles.ini', 'w') as configFile:
            configProfiler.write(configFile)
        
    def userAgentStringRandomed(self):
        usRand = UserAgent(os="Windows")
        userAgent = usRand.random
        configProfiler = configparser.ConfigParser()
        configProfiler.read("profiles.ini")
        configProfiler.set(self.profileMain.objectName(), "useragent", userAgent)
        with open('profiles.ini', 'w') as configFile:
            configProfiler.write(configFile)
        self.userAgentString.setText(userAgent)

    def openTextWidget(self, widget):
        if widget.isHidden():
            widget.show()
            widget.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        else:
            widget.hide()
    
class AppManager:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.current_window = None
        self.app_close_event = asyncio.Event()
        
        with open(r"style.qss", "r", encoding='utf-8') as f:
            self.app.setStyleSheet(f.read())
        
        self.app.aboutToQuit.connect(self.app_close_event.set)
        
    def show_start_window(self):
        """Показать стартовое окно"""
        if self.current_window:
            self.current_window.close()
            
        self.current_window = OnStart(self)
        self.current_window.show()
        
    def show_main_window(self):
        """Показать главное окно"""
        if self.current_window:
            self.current_window.close()
            
        self.current_window = Main(self)
        self.current_window.show()
        
    async def run_async(self):
        """Асинхронный запуск приложения"""
        self.show_start_window()
        await self.app_close_event.wait()
        
    def run(self):
        """Запустить приложение"""
        asyncio.run(self.run_async(), loop_factory=QEventLoop)

class OnStart(QMainWindow):
    def __init__(self, app_manager=None):
        super().__init__()
        self.app_manager = app_manager
        self.setFixedSize(QSize(400, 300))
        self.setWindowTitle('Playerok Bot')
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.startPos = None

        self.mainExitButton = QPushButton()
        self.mainExitButton.setFixedSize(QSize(35,35))
        self.mainExitButton.setProperty("class", "danger")
        self.mainExitButton.setIcon(svgToIcon("exit.svg",size=QSize(35,35)))
        self.mainExitButton.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.mainExitButton.clicked.connect(self.mainExitButtonClicked)

        self.username = QLineEdit()
        self.username.setPlaceholderText("@username")
        self.username.setFixedHeight(35)

        self.switchToMainButton = QPushButton("Открыть бота")
        self.switchToMainButton.setFixedHeight(35)
        self.switchToMainButton.clicked.connect(lambda: self.checkUsername(self.username.text()))

        self.copyHWID = QPushButton("Получить HWID")
        self.copyHWID.setFixedHeight(35)
        self.copyHWID.clicked.connect(lambda: self.checkHWID())

        self.HWIDlabel = QLabel('')
        self.HWIDlabel.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)

        self.centralWidget = QWidget()
        self.centralWidget.setStyleSheet("border-radius: 6px;")
        self.setCentralWidget(self.centralWidget)

        windowLayout = QVBoxLayout(self.centralWidget)                
        windowLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        windowLayout.addWidget(self.mainExitButton, alignment=Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignLeft)
        windowLayout.addWidget(self.username, alignment=Qt.AlignmentFlag.AlignTop)
        windowLayout.addWidget(self.switchToMainButton, alignment=Qt.AlignmentFlag.AlignTop)
        windowLayout.addWidget(self.copyHWID, alignment=Qt.AlignmentFlag.AlignTop)
        windowLayout.addWidget(self.HWIDlabel, alignment=Qt.AlignmentFlag.AlignTop|Qt.AlignmentFlag.AlignHCenter)

        windowLayout.setSpacing(10) 

        for btn in self.findChildren(QPushButton):
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def checkHWID(self):
        hwid = str(subprocess.check_output('wmic csproduct get uuid', shell=True)).strip()
        hwid = hwid.replace(r"\r", "").split(r"\n")[1].strip()
        self.HWIDlabel.setText(hwid)
        self.HWIDlabel.show()

    def get_system_hwid():
        """
        Получает HWID системы разными способами в зависимости от ОС
        """
        system = platform.system()
        
        if system == "Windows":
            try:
                # Способ 1: через wmic (самый надежный для Windows)
                result = subprocess.check_output(
                    'wmic csproduct get uuid', 
                    shell=True, 
                    stderr=subprocess.STDOUT,
                    text=True
                )
                
                # Парсим вывод
                lines = result.strip().split('\n')
                if len(lines) > 1:
                    hwid = lines[1].strip()
                    if hwid and hwid != "":
                        return hwid
                
            except subprocess.CalledProcessError as e:
                print(f"Ошибка wmic: {e.output}")
            
            try:
                # Способ 2: через PowerShell
                result = subprocess.check_output(
                    'powershell -Command "(Get-WmiObject Win32_ComputerSystemProduct).UUID"',
                    shell=True,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                hwid = result.strip()
                if hwid and hwid != "":
                    return hwid
            except:
                pass
            
            try:
                # Способ 3: через реестр
                result = subprocess.check_output(
                    'reg query HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography /v MachineGuid',
                    shell=True,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                # Извлекаем GUID из вывода
                lines = result.strip().split('\n')
                for line in lines:
                    if 'MachineGuid' in line:
                        parts = line.split()
                        if len(parts) > 2:
                            return parts[-1].strip()
            except:
                pass
        
        elif system == "Linux":
            try:
                # Для Linux получаем machine-id
                with open('/etc/machine-id', 'r') as f:
                    return f.read().strip()
            except:
                try:
                    result = subprocess.check_output(['cat', '/etc/machine-id'], text=True)
                    return result.strip()
                except:
                    pass
        
        # Если ничего не сработало
        return None

    def checkUsername(self, target_name, value_column=2):
        """
        Упрощенная версия
        """
        try:
            # Сначала получаем HWID
            try:
                hwid = str(subprocess.check_output('wmic csproduct get uuid', shell=True)).strip()
                hwid = hwid.replace(r"\r", "").split(r"\n")[1].strip()
            except:
                show_gnome_notification("Ошибка получения HWID")
                return False
            
            print(f"HWID системы: '{hwid}'")
            
            # Затем таблицу
            sheet_url = 'https://docs.google.com/spreadsheets/d/11dKpBSFkRZY7EIkicYwHTXVZKouORJJExJf2DW8Cr4g/edit?usp=sharing'
            sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'
            
            import requests
            import pandas as pd
            from io import StringIO
            
            response = requests.get(csv_url)
            df = pd.read_csv(StringIO(response.text), header=None, dtype=str)
            
            target_name_clean = target_name.replace('@', '').strip().lower()
            
            for index, row in df.iterrows():
                if not pd.isna(row[0]):
                    row_name = str(row[0]).replace('@', '').strip().lower()
                    if row_name == target_name_clean:
                        if len(row) >= value_column and not pd.isna(row[value_column - 1]):
                            table_hwid = str(row[value_column - 1]).strip()
                            print(f"Найдено! HWID таблицы: '{table_hwid}'")
                            
                            if table_hwid.upper() == hwid.upper():
                                show_gnome_notification("Аутентификация пройдена")
                                QTimer.singleShot(100, self.switch_to_main)
                                return True
                            else:
                                show_gnome_notification("Неверный HWID")
                                return False
            
            show_gnome_notification("Продукт не найден")
            return False
            
        except Exception as e:
            show_gnome_notification(f"Ошибка: {e}")
            return False


    def switch_to_main(self):
        """Переключение на главное окно"""
        if self.app_manager:
            self.app_manager.show_main_window()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.startPos=event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.startPos=None
    
    def mouseMoveEvent(self, event):
        if not self.startPos:
            return
        delta=event.pos()-self.startPos
        self.move(self.pos() + delta)

    def mainExitButtonClicked(self):
        self.deleteLater()

class Main(QMainWindow):
    def __init__(self, app_manager=None):
        super().__init__()

        # НАСТРОЙКИ ОКНА #
        self.setObjectName("main")
        self.setMinimumSize(QSize(1000,700))
        self.setMaximumSize(QSize(1920, 1080))
        self.setWindowIcon(QIcon("logo.ico"))
        self.setWindowTitle('Playerok Bot')
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)
        self.app_manager = app_manager
        self.startPos = None


        self.mainExitButton = QPushButton()
        self.mainExitButton.setFixedSize(QSize(35,35))
        self.mainExitButton.setProperty("class", "danger")
        self.mainExitButton.setIcon(svgToIcon("exit.svg",size=QSize(35,35)))
        self.mainExitButton.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.mainExitButton.clicked.connect(self.mainExitButtonClicked)

        self.mainMinimizeButton = QPushButton()
        self.mainMinimizeButton.setFixedSize(QSize(35,35))
        self.mainMinimizeButton.setIcon(svgToIcon("minimize.svg",size=QSize(35,35)))
        self.mainMinimizeButton.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.mainMinimizeButton.clicked.connect(self.mainMinimizeButtonClicked)

        self.centralWidget = QGraphicsView()
        self.centralWidget.setStyleSheet("border-radius: 6px;")
        self.setCentralWidget(self.centralWidget)

        windowLayout = QHBoxLayout(self.centralWidget)
        mainButtonsLayout = QVBoxLayout()
        windowLayout.addLayout(mainButtonsLayout)
        mainButtonsLayout.addWidget(self.mainExitButton, 0, Qt.AlignmentFlag.AlignTop)
        mainButtonsLayout.addWidget(self.mainMinimizeButton, 1, Qt.AlignmentFlag.AlignTop)

        self.tabMain = QTabWidget()
        self.tabMain.setMouseTracking(True)
        self.tabMain.setStyleSheet("border-radius: 6px;")
        windowLayout.addWidget(self.tabMain, 0)

        # Хранилище для профилей
        self.userProfiles = {}

        # Playerok #
        self.playerokScreen = QWidget()
        self.playerokLayout = QVBoxLayout(self.playerokScreen)
        self.profileScreens = QWidget()
        self.playerokLayout.addWidget(self.profileScreens)

        enterStatusLayout = QHBoxLayout()
        self.playerokLayout.addLayout(enterStatusLayout)


        self.accountInputText = QLineEdit()
        self.accountInputText.setFixedSize(QSize(200,35))
        self.accountInputText.setMaxLength(20)
        self.validatorText = QRegularExpression(r"[a-zA-Z0-9]*")
        self.accountInputTextValidator = QRegularExpressionValidator(self.validatorText)
        self.accountInputText.setValidator(self.accountInputTextValidator)
        
        enterStatusLayout.addWidget(self.accountInputText, 2)

        self.accountList = QListWidget()
        self.accountList.setFixedSize(QSize(200,100))
        self.accountList.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
 
        
        enterStatusLayout.addWidget(self.accountList, 3, Qt.AlignmentFlag.AlignRight)

        self.accountInputText.returnPressed.connect(self.accountTextLineEnterPressed)
        self.accountList.itemDoubleClicked.connect(self.minimizeTab)

        self.tabMain.addTab(self.playerokScreen, 'Playerok')

        #способ оплаты

        self.oplataScreen = QWidget()
        self.oplataLayout = QVBoxLayout(self.oplataScreen)
        self.oplataLayout.setContentsMargins(10, 10, 10, 10)
        self.oplataLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.oplataScreens = QWidget()
        self.oplataLayout.addWidget(self.oplataScreens)

        self.linkToFragmentAPI = QLabel('<a href="https://fragment-api.com/">Ссылка на APIKEY</a>')
        self.linkToFragmentAPI.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.linkToFragmentAPI.linkActivated.connect(self.onLinkAPI)
        self.oplataLayout.addWidget(self.linkToFragmentAPI)

        self.addTokenLayout = QHBoxLayout()
        self.oplataLayout.addLayout(self.addTokenLayout)

        self.addTokenButton = QPushButton("Добавить токен")
        self.addTokenButton.setFixedSize(QSize(150,35))
        self.addTokenButton.clicked.connect(self.authFragmentAPIClicked)
        self.addTokenLayout.addWidget(self.addTokenButton)

        self.addTokenAPIKEY = QLineEdit("")
        self.addTokenAPIKEY.setPlaceholderText("APIKEY")
        self.addTokenAPIKEY.setFixedSize(QSize(150,35))
        self.addTokenLayout.addWidget(self.addTokenAPIKEY)

        self.addTokenPhone = QLineEdit("")
        self.addTokenPhone.setPlaceholderText("Номер телефона")
        self.addTokenPhone.setFixedSize(QSize(150,35))
        self.addTokenLayout.addWidget(self.addTokenPhone)

        self.addTokenVersion = QComboBox()
        self.addTokenVersion.setFixedSize(QSize(80,35))
        self.addTokenVersion.addItems(['W5', "V4R2"])
        self.addTokenLayout.addWidget(self.addTokenVersion)
        self.addTokenVersion.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self.addTokenMnemonics = QLineEdit()
        self.addTokenMnemonics.setFixedSize(QSize(312,35))
        self.addTokenMnemonics.setPlaceholderText("Секретная фраза")
        self.addTokenLayout.addWidget(self.addTokenMnemonics)

        self.addTokenLayout.addStretch(10)

        self.oplataTokenLayout = QHBoxLayout()
        self.oplataLayout.addLayout(self.oplataTokenLayout)

        self.labelTK = QLabel("Токен:")
        self.labelTK.setFixedSize(QSize(60,35))
        self.oplataTokenLayout.addWidget(self.labelTK)

        self.tokenFragment = QLineEdit('')
        self.tokenFragment.setFixedSize(QSize(800,35))
        self.tokenFragment.setReadOnly(True)
        self.oplataTokenLayout.addWidget(self.tokenFragment, alignment=Qt.AlignmentFlag.AlignLeft)

        self.APIKEYLayout = QHBoxLayout()
        self.oplataLayout.addLayout(self.APIKEYLayout)

        self.oplataAPIKEYlabel = QLabel("APIKEY:")
        self.oplataAPIKEYlabel.setFixedSize(QSize(60,35))
        self.APIKEYLayout.addWidget(self.oplataAPIKEYlabel)

        self.APIKEY = QLineEdit("")
        self.APIKEY.setFixedSize(QSize(800,35))
        self.APIKEY.setReadOnly(True)
        self.APIKEYLayout.addWidget(self.APIKEY, alignment=Qt.AlignmentFlag.AlignLeft)

        self.oplataLayout.addStretch()
        self.tabMain.addTab(self.oplataScreen, "Оплата")

        QTimer.singleShot(300, self.profilePreload) 

        for btn in self.findChildren(QPushButton):
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        for tab in self.tabMain.findChildren(QTabBar):
            tab.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))


    def profilePreload(self):
        configProfilerParser = configparser.ConfigParser()
        configProfilerParser.read("profiles.ini")
        profiles = configProfilerParser.sections()
        if len(profiles)==0:
            pass
        else:
            for profile in profiles:
                profileNew = UserProfile(parent_=self.profileScreens, name_=profile, dict_=self.userProfiles, tabs=self.accountList)
                self.userProfiles[profile] = profileNew
                accountProfile = QListWidgetItem(f"{profile}")
                self.accountList.addItem(accountProfile)
                profileNew.tokenString.setText(configProfilerParser.get(profile,"token"))
                profileNew.tokenString.setEnabled(configProfilerParser.getboolean(profile, "tokenlock"))
                profileNew.userAgentString.setText(configProfilerParser.get(profile,"useragent"))
                profileNew.userAgentString.setEnabled(configProfilerParser.getboolean(profile, "useragentlock"))
                if configProfilerParser.get(profile,"token")!="" and configProfilerParser.get(profile,"useragent")!="":
                    try:
                        items_ = ItemsLoadOnStart(token=configProfilerParser.get(profile,"token"), user_agent=configProfilerParser.get(profile,"useragent"))
                        items_.result.connect(profileNew.itemsLoad)
                        items_.error.connect(profileNew.itemsError)
                        items_.start()
                    except Exception as e:
                        print(f"Внезапная ошибка: {e}")
                        show_gnome_notification(f"Внезапная ошибка: {e}")
        try:
            configProfilerParser.read("fragmentapi.ini")
            self.tokenFragment.setText(configProfilerParser.get("SETTINGS", 'token'))
            self.APIKEY.setText(configProfilerParser.get("SETTINGS", 'apikey'))
        except:
            pass
                            

    def accountTextLineEnterPressed(self):
        text_ = self.accountInputText.text()
        configProfiler = configparser.ConfigParser()
        configProfiler.read("profiles.ini")
        if len(configProfiler.sections())<2 and text_ not in self.userProfiles.keys() and len(text_)>3:
            if len(text_) == 0 or text_[0] in string.digits:
                show_gnome_notification("Название профиля не может быть пустым или начинаться с цифры", 3000, self)
            else:
                accountProfile = QListWidgetItem(text_)
                self.accountList.addItem(accountProfile)
                
                profile = UserProfile(parent_=self.profileScreens, name_=text_, dict_=self.userProfiles, tabs=self.accountList)
                self.userProfiles[text_] = profile

                if profile.QWidgetForTab().objectName() not in configProfiler.sections():
                    configProfiler[profile.QWidgetForTab().objectName()] = {
                        "TOKEN": "",
                        "TOKENLOCK": True,
                        "useragent": "",
                        "useragentlock": True
                    }
                    with open('profiles.ini', 'r+') as configFile:
                        configProfiler.write(configFile)
                else:
                    show_gnome_notification("При создании профиля нельзя:\n" \
            "Называть профили одинаково\n" \
            "Создавать больше двух профилей\n" \
            "Давать название профилю короче, чем 4 символа", 3000, self)
                
                self.accountInputText.clear()
        else:
            show_gnome_notification("При создании профиля нельзя:\n" \
            "Называть профили одинаково\n" \
            "Создавать больше двух профилей\n" \
            "Давать название профилю короче, чем 4 символа", 3000, self)
    
    def onLinkAPI(self):
        QDesktopServices.openUrl(QUrl("https://fragment-api.com/dashboard"))

    def authFragmentAPIClicked(self):
        try:
            show_gnome_notification("Пробуем получить токен...")
            self.auth = AuthFragment(apikey=self.addTokenAPIKEY.text(), phone=self.addTokenPhone.text(), version=self.addTokenVersion.currentText(), mnemonics=self.addTokenMnemonics.text())
            self.auth.result.connect(self.authSignal)
            self.auth.error.connect(self.errorSignal)
            self.auth.start()
        except Exception as e:
            print(f"Внезапная ошибка: {e}")
            show_gnome_notification(f"Внезапная ошибка: {e}")

    def authSignal(self, result):
        token, apikey, phone = result
        self.tokenFragment.setText(token)
        self.APIKEY.setText(apikey)
        configProfiler = configparser.ConfigParser()
        configProfiler.read("fragmentapi.ini")
        configProfiler.add_section("SETTINGS")
        configProfiler.set('SETTINGS', 'token', token)
        configProfiler.set('SETTINGS', 'apikey', apikey)
        configProfiler.set('SETTINGS', 'phone', phone)
        with open('fragmentapi.ini', 'w') as configFile:
            configProfiler.write(configFile)
        show_gnome_notification("Успешно получен токен.")

    def errorSignal(self, error):
        show_gnome_notification(error)
        print(error)

    def minimizeTab(self, item):
        tab=self.userProfiles.get(item.text()).QWidgetForTab()
        if tab.isHidden():
            for wind in self.userProfiles.keys():
                tab.parent().findChild(QWidget, wind).hide()
            tab.show()
        else:
            tab.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.startPos=event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.startPos=None
    
    def mouseMoveEvent(self, event):
        if not self.startPos:
            return
        delta=event.pos()-self.startPos
        self.move(self.pos() + delta)

        

    def mainExitButtonClicked(self):
        self.deleteLater()

    def mainMinimizeButtonClicked(self):
        self.setWindowState(Qt.WindowState.WindowMinimized)

if __name__ == "__main__":
    manager = AppManager()
    manager.run()