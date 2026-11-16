
import ctypes
from ctypes import wintypes

from pywinauto import Desktop


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG)
    ]


user32 = ctypes.windll.user32

user32.ClientToScreen.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(POINT)
]
user32.ClientToScreen.restype = wintypes.BOOL


def get_desktop_icons():
    icons = []
    desktop = Desktop(backend="win32")

    for window in desktop.windows():
        try:
            if window.class_name() not in ("Progman", "WorkerW"):
                continue

            views = window.descendants(
                class_name="SHELLDLL_DefView"
            )

            for view in views:
                lists = view.descendants(
                    class_name="SysListView32"
                )

                for icon_list in lists:
                    count = icon_list.item_count()

                    print(f"Ikon listesi: {count} oge")

                    for index in range(count):
                        try:
                            item = icon_list.get_item(index)
                            name = item.text()

                            if not name:
                                continue

                            # Ikonun kendi kontrolundeki konumu
                            rect = item.rectangle("icon")

                            center_x = (
                                rect.left + rect.right
                            ) // 2

                            center_y = (
                                rect.top + rect.bottom
                            ) // 2

                            # Ekran koordinatina cevir
                            point = POINT(center_x, center_y)

                            success = user32.ClientToScreen(
                                icon_list.handle,
                                ctypes.byref(point)
                            )

                            if not success:
                                print(
                                    "Koordinat cevrilemedi:",
                                    name
                                )
                                continue

                            icons.append({
                                "name": name,
                                "x": point.x,
                                "y": point.y
                            })

                        except Exception as error:
                            print(
                                f"Ikon {index} hatasi:",
                                error
                            )

        except Exception as error:
            print("Pencere hatasi:", error)

    return icons


if __name__ == "__main__":
    icons = get_desktop_icons()

    print("\nMASAUSTU IKONLARI")
    print("-" * 35)

    for icon in icons:
        print(
            f"{icon['name']} -> "
            f"X: {icon['x']}, "
            f"Y: {icon['y']}"
        )

    print("-" * 35)
    print(f"Toplam {len(icons)} ikon bulundu.")
