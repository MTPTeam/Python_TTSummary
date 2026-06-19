from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPixmap, QColor, QBrush
from PyQt6.QtCore import Qt, QRectF
import os


class BlurredBackground(QWidget):
   """
   Paints the background image blurred and darkened so glass cards
   sitting on top actually look like frosted glass.
   blur_radius  — 0 = sharp, 1 = barely soft, 20 = very melted
   darken       — 0–255 alpha of black overlay (80 = subtle, 140 = moody)
   """
   def __init__(self, image_path: str, blur_radius: int = 20, darken: int = 255, parent=None):
       super().__init__(parent)
       self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
       self._raw = QPixmap(image_path)
       self._blur_radius = blur_radius
       self._darken = darken
       self._cached_bg = None
       self._cached_size = None
       #print(f"BlurredBackground loaded: {image_path}, null={self._raw.isNull()}")  # DEBUG


   def _build_cache(self):
       from PyQt6.QtGui import QImage
       size = self.size()
       scaled = self._raw.scaled(
           size,
           Qt.AspectRatioMode.KeepAspectRatioByExpanding,
           Qt.TransformationMode.SmoothTransformation,
       )
       x = (scaled.width()  - size.width())  // 2
       y = (scaled.height() - size.height()) // 2
       cropped = scaled.copy(x, y, size.width(), size.height())
       img = cropped.toImage().convertToFormat(QImage.Format.Format_ARGB32)
       r = self._blur_radius
       small = img.scaled(
           max(1, size.width()  // (r + 1)),
           max(1, size.height() // (r + 1)),
           Qt.AspectRatioMode.IgnoreAspectRatio,
           Qt.TransformationMode.SmoothTransformation,
       ).scaled(
           size.width(),
           size.height(),
           Qt.AspectRatioMode.IgnoreAspectRatio,
           Qt.TransformationMode.SmoothTransformation,
       )
       blurred = QPixmap.fromImage(small)
       if self._darken > 0:
           overlay = QPainter(blurred)
           overlay.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
           overlay.fillRect(blurred.rect(), QColor(10, 5, 0, self._darken))
           overlay.end()
       self._cached_bg   = blurred
       self._cached_size = size

   def resizeEvent(self, event):
       self._cached_bg = None
       super().resizeEvent(event)
       
   def paintEvent(self, event):
       #print(f"BlurredBackground paintEvent fired, size={self.size()}")  # DEBUG
       if self._raw.isNull():
           #print("RAW IMAGE IS NULL")  # DEBUG
           super().paintEvent(event)
           return
       if self._cached_bg is None or self._cached_size != self.size():
           self._build_cache()
       p = QPainter(self)
       p.drawPixmap(0, 0, self._cached_bg)
       p.end()